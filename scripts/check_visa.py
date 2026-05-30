import json, time, os, base64, gspread
from datetime import datetime
from playwright.sync_api import sync_playwright
from google.oauth2.service_account import Credentials

# Inline stealth patches — hides headless/automation signals from Cloudflare Turnstile
STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => ({length:3, item:()=>null, namedItem:()=>null, refresh:()=>{}})});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
window.chrome = {runtime:{}, loadTimes:function(){}, csi:function(){}, app:{}};
const _origPermQuery = window.navigator.permissions && window.navigator.permissions.query.bind(window.navigator.permissions);
if (_origPermQuery) {
    window.navigator.permissions.query = (p) =>
        p.name === 'notifications'
            ? Promise.resolve({state: Notification.permission})
            : _origPermQuery(p);
}
"""

GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
ICP_URL     = "https://smartservices.icp.gov.ae/echannels/web/client/default.html#/fileValidity"
ICP_API_URL = "https://beta.smartservices.icp.gov.ae/echannels/api/api/landing/fileValidityNew"
CREDS_B64   = "eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogImtlZW4tZGVmZW5kZXItNDk3ODA3LWsxIiwgInByaXZhdGVfa2V5X2lkIjogIjU3YzlmMjY3ZTAyNzRiYTMyM2EyODNkMTBiYjI5NWJmODJjNTk5NWUiLCAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdlFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUUMrN1VXODg0S2xkdXFLXG5oM3RLZEMycEU0emQraUhRc0R1V1A3cG1LWFRLc05FakFjdDBjTVZIU0llcTFOVkVqWEdjL3lnVnRJMW96SlNFXG5DbkRyUkg0Nndxd1l1WTBqM1kvRTVmd2EzSENGUEJEelI3NE03c3dSQzBSelI2RjdpUlNLRzdJdEI2SWdHMWhEXG5iSTdFOEpHbWVWemFudUU2LytlNGVvbFNrK2k2OU4xNmpnUkJReGxNb3ExWHBuYXFCd2VXZHVuMW5MaktTOGRQXG56YWNEWDBWN1JJSmduQ3plM0JxN3FHYW4vdU5PUmZBSjJKWU9IcWhjRGNIUXg0T2w1b3NKaGEycmtZcUxtbXZ1XG4vRVRLSkovd1NRZ3dvU25RSm5LN0JjeWtyTE1hT0cvelA1Qm9INFJ2Z0RTdUpzcWwzUko3b3dXSnlxY1Eyb1VFXG5MSWErNkNzOUFnTUJBQUVDZ2dFQUl2UGhtenFTTFpRRVVvbUVlT2dsYnNsSk5kOERuMGFRRmd6REpVNU1Gd3BCXG5NekV5SzdZMGEzMGI5eHFCRTR4NFl1YzBVYXJzNDJWbWYvakFYTlc4YlNuejR3L2ZCcFNhYkErMWRENXNhL3ZIXG4xNTNIN1dxdkdhU3dLcEdQdnNPazZyYXd5djBWZ1Y2NExSbTcxbEo3TzVpR3R2QTBwLzR1eis5QTRnajVaM1k0XG4xeDhHTzJlZ3lORGR2bTFOZkV6ZzYvelNsY2lQMVg5RXZxVDNpNkt0S1B0VnVrUk1RMWd4N3JMT254UGRKTTNhXG5yMWx0elFQRDlKZGl1cFUvZUVLdmI5S2w2eWRzMWhrYTlZRUgyUkpSM1JYMzZWdDBLK05lUUVaRE1oVkdWRFdEXG5ReHVKSXhNSjlUVHlnQUxvMEZSdUpncnIvV1NoRFNkYVY4WnpVblhRcVFLQmdRRHJFQWx4V0ZYOXl1MDRQV2NDXG43YUM3WDQ4K1dvaFV2cXFSTFo0ZS9oUmk3ZS9UM1B2VUVqY2xoRFNOS2JwYU1pZTg4aGJzK01HZysrRUM3WC9pXG5ETW45RDZJRW9qaHZGcDd0LzdyWUh4bUltbkg4bmZXOUI1b2hLQm1qS1pnVVVuRFcyWENlbSt1ZXMrVW9IdzRuXG40VS9Jb1hVWlBwQ2JaZ2RuK2VnMDJxQStHUUtCZ1FEUDd0YkIrMFlpS09lckVhNFB0YXVxZmJKdi9nb0FtZjJBXG5QVzNPUFZvRWV2c1U3bU1kQ1NzcDdzblpKTVRCOERDVStUV3NkM1I5WnA4KzRXY1NGL3JpcWZFYnUvZGJGWnNTXG5tRVRRb0VPdk9pWFNuSDQxNUNHUW80RzBrNnJJbWhiUy9lU04xSFRlYjRDMEpnczJpTTFhc3R2SFo5SlNGY3B2XG5QcXBFZ1NPeXhRS0JnQ2FHWVZYUFNZQ240b3NtSFJ6d3Z6Z1dhRTZxM2M4dDFKeW9vbEtvQjhWVEE4eHdXbUdlXG5mcVZLYnFaNElVK3BDclEvNVJ2L2hSU1NVNFY4VVVwR0dGQytZQ3BzUDkyTkVvMGxMWVZBUzVvRTNndXVBOWx3XG5Sb1dLb2ZFSTN5RHRoZ3JnWmtISWdpeG5oWFkyNk1ZR2VtSUNmRU9mNm1sZHBuY1hFVVNnVkVUNUFvR0FaQ3huXG5VQnJUQmQvNUJDUkhYQkFrdk1WRHNzcUxYUkRTM1BZN01WSERUVWRHTVNaTG41QnNPQTV2TmVxTjAvVDRJcjBRXG55NTdkQXhEdWhTZW9OVUpTUHVLcVlyY2lpc0lVN0ZkcFI2eitEcXdQenJCUDZYeVhZd3d5ajZGWWRMNHZZc1NvXG5XRi9UVWRvY0FpNFYxdGIvUDhQTk4vcmZpMll1R1h2eUlZQ3BoeFVDZ1lFQXVYd3BackZuSlc2b1BlSkNYOW5xXG5hM3luekJtNkVwTGVyNzVUeTQxRlo5eWJPSjAzalVWTEZVN1lKYk5UVWNjTE1TNTlhNHlnNmpNdkRyZjQ0eUN4XG5ZaE9pWi8vS3dOekpLNlpxMmcwV1U1ckFOWjZSeVNjS0NQclhKeS83Rmd2eVgzSFFMU2c2cGxnMGxVMER5Q0R5XG5iT1BZeFZ3elp2NU5pT3gzd3BsL1N5Yz1cbi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS1cbiIsICJjbGllbnRfZW1haWwiOiAiaWNwLWNoZWNrZXJAa2Vlbi1kZWZlbmRlci00OTc4MDctazEuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCAiY2xpZW50X2lkIjogIjExMjE4MDUzMDUwNjY1NzM4NjE3MyIsICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsICJ0b2tlbl91cmkiOiAiaHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4iLCAiYXV0aF9wcm92aWRlcl94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL29hdXRoMi92MS9jZXJ0cyIsICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L2ljcC1jaGVja2VyJTQwa2Vlbi1kZWZlbmRlci00OTc4MDctazEuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCAidW5pdmVyc2VfZG9tYWluIjogImdvb2dsZWFwaXMuY29tIn0="

# Actual column names as they appear in the Google Sheet header row
COL_FILE_NO       = "File No."
COL_FILE_STATUS   = "File Status"
COL_FILE_ISSUANCE = "File Issuance Date"
COL_LAST_DATE     = "Last Date Allowed to Enter the Country"
COL_FILE_CANCEL   = "File Cancellation Date"
COL_ALERT         = "AlertLevel"
COL_DAYS_LEFT     = "DaysLeft"
COL_LAST_CHECKED  = "LastChecked"

NATIONALITY_IDS = {
    "EGYPT":13,"INDONESIA":43,"INDIA":25,"PAKISTAN":24,
    "PHILIPPINES":40,"BANGLADESH":26,"NEPAL":39,"SRI LANKA":31,
    "ETHIOPIA":67,"KENYA":71,"NIGERIA":76,"JORDAN":15,
    "SYRIA":18,"LEBANON":16,"SUDAN":19,"MOROCCO":14,
}

def connect_sheet():
    print("  Decoding credentials...")
    creds_dict = json.loads(base64.b64decode(CREDS_B64).decode("utf-8"))
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"]
    )
    gc = gspread.authorize(creds)
    print("  Connected to Google Sheets!")
    return gc.open_by_key(GOOGLE_SHEET_ID).sheet1

def get_captcha_token(playwright_instance):
    """Launch a browser, load the ICP page, and wait up to 45s for Turnstile to auto-solve.
    Also try submitting a dummy search so the token is captured from the network request."""
    print("  Launching browser to capture CAPTCHA token...")
    captured = {}
    browser = playwright_instance.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox", "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
        ]
    )
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        timezone_id="Asia/Dubai",
    )
    page = ctx.new_page()
    page.add_init_script(STEALTH_JS)  # patch navigator.webdriver, Chrome runtime, plugins, etc.

    def on_req(r):
        if "fileValidityNew" in r.url and r.method == "POST":
            try:
                t = json.loads(r.post_data or "{}").get("recaptchaResponse")
                if t:
                    captured["token"] = t
                    print("  ✓ Token captured from network request!")
            except: pass

    page.on("request", on_req)

    try:
        page.goto(ICP_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("input[type='radio']", timeout=20000)
        time.sleep(3)  # let page fully render before polling

        # Poll for Turnstile auto-solve (up to 60 seconds)
        print("  Waiting for Turnstile to auto-solve...")
        for tick in range(60):
            token = page.evaluate("""
                () => {
                    const inputs = document.querySelectorAll('input[name="cf-turnstile-response"], textarea[name="cf-turnstile-response"]');
                    for (const el of inputs) { if (el.value) return el.value; }
                    return null;
                }
            """)
            if token:
                captured["token"] = token
                print(f"  ✓ Token found in DOM after {tick+1}s!")
                break
            time.sleep(1)

        if not captured.get("token"):
            # Fall back: select "Emirate Unified Number", fill a dummy UID and click Search
            # so the browser triggers the API call and we catch the token from the request
            print("  Token not in DOM — triggering a dummy search to capture it...")
            for lbl in page.locator("label").all():
                try:
                    text = (lbl.inner_text() or "").lower()
                    if "emirate unified" in text or "unified number" in text:
                        lbl.click(); time.sleep(1); break
                except: pass

            for inp in page.locator("input[type='text']:visible").all():
                try:
                    placeholder = (inp.get_attribute("placeholder") or "").lower()
                    if "dd/" not in placeholder:
                        inp.fill("000000000"); break
                except: pass

            time.sleep(5)  # let Turnstile solve after user interaction

            for btn in page.locator("button:visible").all():
                try:
                    if "search" in (btn.inner_text() or "").lower():
                        btn.click()
                        print("  Clicked Search button...")
                        time.sleep(5)
                        break
                except: pass

            # One final DOM check
            token = page.evaluate("""
                () => {
                    const inputs = document.querySelectorAll('input[name="cf-turnstile-response"], textarea[name="cf-turnstile-response"]');
                    for (const el of inputs) { if (el.value) return el.value; }
                    return null;
                }
            """)
            if token:
                captured["token"] = token
                print("  ✓ Token found after dummy search!")

    except Exception as e:
        print(f"  Browser error: {e}")
    finally:
        browser.close()

    token = captured.get("token")
    if token:
        print(f"  ✓ Token ready (length={len(token)})")
    else:
        print("  ✗ Failed to capture token")
    return token

ICP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://smartservices.icp.gov.ae",
    "Referer": "https://smartservices.icp.gov.ae/echannels/web/client/default.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
}

def build_body(emp, token=None):
    nat_id = int(emp.get("NationalityId") or emp.get("Code") or
                 NATIONALITY_IDS.get(str(emp.get("Nationality","")).upper(), 0))
    dob = str(emp.get("dateOfBirth") or emp.get("DOB") or "")
    if "/" in dob:
        p = dob.split("/")
        if len(p) == 3 and len(p[2]) == 4:
            dob = f"{p[2]}/{p[1]}/{p[0]}"
    uid = str(emp.get("Emirate Unified Number") or emp.get("UID") or "")
    return {
        "fileModuleId": int(emp.get("fileModuleId") or emp.get("FileModuleId") or 2),
        "longUnifiedNumber": uid,
        "nationalityId": nat_id,
        "dateOfBirth": dob,
        "serviceYear": None, "sequenceNumber": None, "expireDate": None,
        "isUsingCaptcha": bool(token),
        "recaptchaResponse": token or "",
    }

def call_icp(emp, token=None):
    import requests
    r = requests.post(ICP_API_URL, json=build_body(emp, token),
                      timeout=30, headers=ICP_HEADERS)
    return r.json()

def requires_captcha(raw):
    """Return True if the API response indicates a CAPTCHA token is required."""
    if not raw:
        return False
    msg = str(raw).lower()
    return any(x in msg for x in ["captcha", "recaptcha", "token invalid", "unauthorized", "blocked"])

def classify(status, expire):
    s = (status or "").upper()
    days = None
    if expire:
        try:
            p = str(expire).split("/")
            e = datetime(int(p[0]),int(p[1]),int(p[2])) if len(p[0])==4 else datetime(int(p[2]),int(p[1]),int(p[0]))
            days = (e - datetime.now()).days
        except: pass
    if any(x in s for x in ["CANCEL","OVERSTAY","EXPIRED","REJECTED","ABSCONDING"]):
        return "🔴 CRITICAL", days
    if days is not None and days < 0:  return "🔴 CRITICAL", days
    if days is not None and days <= 10: return "🟡 WARNING",  days
    if "ACTIVE" in s or (days is not None and days > 10): return "🟢 OK", days
    return "⚪ UNKNOWN", days


def main():
    print("="*55)
    print("  ICP Visa Status Checker — GitHub Actions")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC")
    print("="*55)

    print("\nConnecting to Google Sheet...")
    sheet = connect_sheet()
    rows  = sheet.get_all_records()
    headers = sheet.row_values(1)
    print(f"  Found {len(rows)} employees")
    print(f"  Sheet headers: {headers}")

    if not rows:
        print("  Sheet is empty — nothing to do."); return

    today = datetime.now().strftime("%d/%m/%Y")
    results = []

    # ── Probe: does the ICP API enforce CAPTCHA server-side? ──────────────────
    probe_emp = next((r for r in rows if str(r.get("Emirate Unified Number","")).strip()), None)
    needs_captcha = False
    if probe_emp:
        print("\nProbing ICP API without CAPTCHA token...")
        try:
            probe_raw = call_icp(probe_emp)
            print(f"  Probe response: {str(probe_raw)[:300]}")
            needs_captcha = requires_captcha(probe_raw)
        except Exception as e:
            print(f"  Probe error: {e}")
            needs_captcha = True
        print(f"  CAPTCHA enforcement: {'YES — will use browser' if needs_captcha else 'NO — direct API calls will work'}")

    token = None
    calls_since_refresh = 0
    TOKEN_REFRESH_EVERY = 50

    with sync_playwright() as pw:
        if needs_captcha:
            token = get_captcha_token(pw)
            if not token:
                print("\nFATAL: CAPTCHA required but could not capture token. Aborting.")
                return

        for i, emp in enumerate(rows):
            name = (emp.get("VISA  NAME ") or emp.get("VISA NAME") or
                    emp.get("Customer Name") or f"Row {i+2}")
            uid  = str(emp.get("Emirate Unified Number") or emp.get("UID") or "").strip()

            if not uid:
                print(f"\n[{i+1}/{len(rows)}] Skipping {name} — no UID"); continue

            print(f"\n[{i+1}/{len(rows)}] {name} — UID: {uid}")

            # Proactively refresh token every N employees
            if needs_captcha and calls_since_refresh >= TOKEN_REFRESH_EVERY:
                print("  Refreshing CAPTCHA token...")
                new_token = get_captcha_token(pw)
                if new_token:
                    token = new_token
                    calls_since_refresh = 0
                else:
                    print("  ⚠ Token refresh failed — continuing with old token")

            try:
                raw = call_icp(emp, token)
                print(f"  ICP Response: {str(raw)[:250]}")
            except Exception as e:
                print(f"  ✗ API error: {e}"); continue

            # If the API now demands a token, get one and retry
            if requires_captcha(raw) and not needs_captcha:
                print("  API now requires CAPTCHA — fetching token and retrying...")
                needs_captcha = True
                token = get_captcha_token(pw)
                if not token:
                    print("  ✗ Could not get token, skipping"); continue
                try:
                    raw = call_icp(emp, token)
                    print(f"  ICP Response (with token): {str(raw)[:250]}")
                except Exception as e:
                    print(f"  ✗ Retry error: {e}"); continue

            d = raw.get("data") or raw.get("result") or raw or {}
            status   = (d.get("fileStatus") or d.get("status") or "UNKNOWN").upper()
            expire   = (d.get("lastDateAllowedToEnterTheCountry") or
                        d.get("fileExpireDate") or d.get("expireDate") or "")
            file_no  = d.get("fileNo") or d.get("fileNoFormatted") or ""
            file_iss = d.get("fileIssuanceDate") or d.get("issuanceDate") or ""
            file_can = d.get("fileCancellationDate") or d.get("cancellationDate") or ""
            alert, days = classify(status, expire)

            print(f"  ✓ Status: {status} | Last Date: {expire} | Alert: {alert}")

            col_updates = {
                COL_FILE_NO:       file_no,
                COL_FILE_STATUS:   status,
                COL_FILE_ISSUANCE: file_iss,
                COL_LAST_DATE:     expire,
                COL_FILE_CANCEL:   file_can,
                COL_ALERT:         alert,
                COL_DAYS_LEFT:     days if days is not None else "",
                COL_LAST_CHECKED:  today,
            }

            row_num = i + 2
            for col_name, val in col_updates.items():
                if col_name in headers:
                    sheet.update_cell(row_num, headers.index(col_name) + 1, val)
                else:
                    print(f"  ⚠ Column '{col_name}' not in sheet — skipping")

            results.append({"name": name, "status": status, "alert": alert})
            calls_since_refresh += 1
            time.sleep(2)

    print(f"\n{'='*55}\n  SUMMARY\n{'='*55}")
    for r in results:
        print(f"  {r['alert']}  {r['name']:<30} {r['status']}")
    print(f"\n  Done — {len(results)} employees checked")

if __name__ == "__main__":
    main()
