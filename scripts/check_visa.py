"""
ICP Visa Status Checker
Runs daily via GitHub Actions - completely free
Uses Playwright to handle Cloudflare Turnstile automatically
Updates Google Sheet with results
"""

import json
import time
import os
import gspread
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from google.oauth2.service_account import Credentials

# ── Config from GitHub Secrets ─────────────────────────────────────────────
GOOGLE_SHEET_ID        = os.environ["GOOGLE_SHEET_ID"]
GOOGLE_CREDS_JSON      = os.environ["GOOGLE_CREDENTIALS"]   # full JSON string
ICP_URL                = "https://smartservices.icp.gov.ae/echannels/web/client/default.html#/fileValidity"
ICP_API_URL            = "https://beta.smartservices.icp.gov.ae/echannels/api/api/landing/fileValidityNew"

# ── Nationality ID mapping ──────────────────────────────────────────────────
NATIONALITY_IDS = {
    "EGYPT": 13, "INDONESIA": 43, "INDIA": 25, "PAKISTAN": 24,
    "PHILIPPINES": 40, "BANGLADESH": 26, "NEPAL": 39, "SRI LANKA": 31,
    "ETHIOPIA": 67, "KENYA": 71, "NIGERIA": 76, "GHANA": 68,
    "JORDAN": 15, "SYRIA": 18, "LEBANON": 16, "SUDAN": 19,
    "MOROCCO": 14, "TUNISIA": 20, "ALGERIA": 12,
}

# ── Google Sheet columns (must match your sheet header row) ────────────────
COL_UID           = "UID"
COL_NAME          = "Name"
COL_NATIONALITY   = "Nationality"       # text e.g. EGYPT
COL_NATIONALITY_ID= "NationalityId"    # number e.g. 13
COL_DOB           = "DOB"              # DD/MM/YYYY
COL_FILE_MODULE   = "FileModuleId"     # 1=Residency 2=Visa
COL_SEARCH_METHOD = "SearchMethod"     # UID or PASSPORT
COL_PASSPORT_NO   = "PassportNo"
COL_PASSPORT_EXP  = "PassportExpiry"
COL_PHONE         = "Phone"
# Auto-filled columns:
COL_FILE_NO       = "FileNo"
COL_FILE_STATUS   = "FileStatus"
COL_EXPIRY        = "ExpiryDate"
COL_DAYS_LEFT     = "DaysLeft"
COL_ALERT         = "AlertLevel"
COL_LAST_CHECKED  = "LastChecked"


def get_captcha_token():
    """Open real browser, load ICP page, extract Cloudflare Turnstile token"""
    print("  Getting Cloudflare token via real browser...")
    token = None

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
        )
        page = context.new_page()

        # Intercept the API call to steal the token from the request
        captured_token = {}

        def on_request(request):
            if "fileValidityNew" in request.url and request.method == "POST":
                try:
                    body = json.loads(request.post_data or "{}")
                    t = body.get("recaptchaResponse")
                    if t:
                        captured_token["token"] = t
                        print("  ✓ Token captured from browser request!")
                except Exception:
                    pass

        page.on("request", on_request)

        try:
            page.goto(ICP_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("input[type='radio']", timeout=15000)
            time.sleep(2)

            # Fill a dummy search to trigger the Turnstile
            # Select "File No." and "Visa"
            for label_text in ["File No.", "Visa", "Emirate Unified Number"]:
                try:
                    for lbl in page.locator("label").all():
                        if label_text.lower() in (lbl.inner_text() or "").lower():
                            lbl.click()
                            time.sleep(0.4)
                            break
                except Exception:
                    pass

            # Fill UID field with a dummy value to enable Search button
            try:
                inputs = page.locator("input[type='text']:visible").all()
                for inp in inputs:
                    ph = inp.get_attribute("placeholder") or ""
                    if "dd/" not in ph.lower():
                        inp.fill("000000000")
                        break
            except Exception:
                pass

            # Wait for Cloudflare widget to render
            time.sleep(3)

            # Try to extract token from cf-turnstile widget directly
            try:
                token_val = page.evaluate("""
                    () => {
                        // Check hidden input added by Turnstile
                        const inputs = document.querySelectorAll('input[name="cf-turnstile-response"], input[name="g-recaptcha-response"]');
                        for (const inp of inputs) {
                            if (inp.value) return inp.value;
                        }
                        // Check window object
                        if (window.turnstile) {
                            const containers = document.querySelectorAll('.cf-turnstile, [data-sitekey]');
                            for (const c of containers) {
                                const resp = turnstile.getResponse(c);
                                if (resp) return resp;
                            }
                        }
                        return null;
                    }
                """)
                if token_val:
                    token = token_val
                    print("  ✓ Token extracted from Turnstile widget!")
            except Exception:
                pass

            # If still no token, click Search to trigger validation and capture from request
            if not token:
                try:
                    for btn in page.locator("button, a.btn").all():
                        txt = (btn.inner_text() or "").lower()
                        if "search" in txt or "verify" in txt:
                            btn.click()
                            time.sleep(3)
                            break
                except Exception:
                    pass

            if captured_token.get("token"):
                token = captured_token["token"]

        except Exception as e:
            print(f"  Browser error: {e}")
        finally:
            browser.close()

    return token


def call_icp_api(page_session, employee, token):
    """Call ICP API with the employee data and CAPTCHA token"""
    import requests

    nat_id = int(employee.get(COL_NATIONALITY_ID) or
                 NATIONALITY_IDS.get(str(employee.get(COL_NATIONALITY, "")).upper(), 0))

    # Convert DOB from DD/MM/YYYY to YYYY/MM/DD
    dob_raw = str(employee.get(COL_DOB, ""))
    dob_api = dob_raw
    if "/" in dob_raw:
        parts = dob_raw.split("/")
        if len(parts) == 3 and len(parts[2]) == 4:
            dob_api = f"{parts[2]}/{parts[1]}/{parts[0]}"

    body = {
        "fileModuleId":      int(employee.get(COL_FILE_MODULE, 2)),
        "longUnifiedNumber": str(employee.get(COL_UID, "")),
        "nationalityId":     nat_id,
        "dateOfBirth":       dob_api,
        "serviceYear":       None,
        "sequenceNumber":    None,
        "expireDate":        None,
        "isUsingCaptcha":    True,
        "recaptchaResponse": token,
    }

    headers = {
        "Content-Type":     "application/json",
        "Accept":           "application/json, text/plain, */*",
        "Origin":           "https://smartservices.icp.gov.ae",
        "Referer":          "https://smartservices.icp.gov.ae/echannels/web/client/default.html",
        "User-Agent":       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    resp = requests.post(ICP_API_URL, json=body, headers=headers, timeout=30)
    return resp.json()


def classify(file_status, expire_date):
    """Return alert level and days left"""
    status = (file_status or "").upper()
    days_left = None

    if expire_date:
        try:
            p = str(expire_date).split("/")
            if len(p) == 3:
                exp = datetime(int(p[0]) if len(p[0]) == 4 else int(p[2]),
                               int(p[1]),
                               int(p[2]) if len(p[0]) == 4 else int(p[0]))
                days_left = (exp - datetime.now()).days
        except Exception:
            pass

    if any(x in status for x in ["CANCEL", "OVERSTAY", "EXPIRED", "REJECTED", "ABSCONDING"]):
        return "🔴 CRITICAL", days_left
    if days_left is not None and days_left < 0:
        return "🔴 CRITICAL", days_left
    if days_left is not None and days_left <= 30:
        return "🟡 WARNING", days_left
    if "ACTIVE" in status:
        return "🟢 OK", days_left
    return "⚪ UNKNOWN", days_left


def connect_sheet():
    """Connect to Google Sheet using service account"""
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"]
    )
    gc = gspread.authorize(creds)
    return gc.open_by_key(GOOGLE_SHEET_ID).sheet1


def main():
    print("=" * 55)
    print("  ICP Visa Status Checker — GitHub Actions")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC")
    print("=" * 55)

    # Connect to sheet
    print("\nConnecting to Google Sheet...")
    sheet = connect_sheet()
    rows = sheet.get_all_records()
    headers = sheet.row_values(1)
    print(f"  Found {len(rows)} employees")

    results = []
    today = datetime.now().strftime("%d/%m/%Y")

    for i, emp in enumerate(rows):
        name = emp.get(COL_NAME, f"Row {i+2}")
        uid  = emp.get(COL_UID, "")
        if not uid:
            print(f"\nSkipping row {i+2} — no UID")
            continue

        print(f"\n[{i+1}/{len(rows)}] {name} — UID: {uid}")

        # Get fresh CAPTCHA token for each employee
        token = get_captcha_token()
        if not token:
            print("  ✗ Could not get CAPTCHA token, skipping")
            results.append({**emp, "AlertLevel": "⚪ ERROR", "LastChecked": today})
            continue

        # Call ICP API
        try:
            raw = call_icp_api(None, emp, token)
            print(f"  ICP response: {json.dumps(raw)[:200]}")
        except Exception as e:
            print(f"  ✗ API error: {e}")
            continue

        # Parse response
        d = raw.get("data") or raw.get("result") or raw or {}
        file_status  = (d.get("fileStatus") or d.get("status") or "UNKNOWN").upper()
        expire_date  = d.get("fileExpireDate") or d.get("expireDate") or d.get("lastDateAllowedToEnterTheCountry")
        issuance     = d.get("fileIssuanceDate") or d.get("issuanceDate")
        file_no      = d.get("fileNo") or d.get("fileNoFormatted") or "N/A"

        alert, days_left = classify(file_status, expire_date)

        print(f"  Status:  {file_status}")
        print(f"  Expiry:  {expire_date}")
        print(f"  Alert:   {alert}")

        # Update sheet row
        row_num = i + 2  # +2 because row 1 is header
        updates = {
            COL_FILE_NO:      file_no,
            COL_FILE_STATUS:  file_status,
            COL_EXPIRY:       expire_date or "",
            COL_DAYS_LEFT:    days_left if days_left is not None else "",
            COL_ALERT:        alert,
            COL_LAST_CHECKED: today,
        }

        for col_name, value in updates.items():
            if col_name in headers:
                col_idx = headers.index(col_name) + 1
                sheet.update_cell(row_num, col_idx, value)

        results.append({**emp, **updates})
        time.sleep(2)  # polite delay between employees

    # Summary
    print(f"\n{'='*55}")
    print("  SUMMARY")
    print(f"{'='*55}")
    for r in results:
        print(f"  {r.get('AlertLevel','⚪')}  {r.get(COL_NAME,'?'):<25} {r.get(COL_FILE_STATUS,'?')}")
    print(f"\n  Done — {len(results)} employees checked")


if __name__ == "__main__":
    main()
