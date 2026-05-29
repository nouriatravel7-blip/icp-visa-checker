import json, time, os, base64, gspread
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from google.oauth2.service_account import Credentials

GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
ICP_URL     = "https://smartservices.icp.gov.ae/echannels/web/client/default.html#/fileValidity"
ICP_API_URL = "https://beta.smartservices.icp.gov.ae/echannels/api/api/landing/fileValidityNew"

NATIONALITY_IDS = {
    "EGYPT":13,"INDONESIA":43,"INDIA":25,"PAKISTAN":24,
    "PHILIPPINES":40,"BANGLADESH":26,"NEPAL":39,"SRI LANKA":31,
    "ETHIOPIA":67,"KENYA":71,"NIGERIA":76,"JORDAN":15,
    "SYRIA":18,"LEBANON":16,"SUDAN":19,"MOROCCO":14,
}

def connect_sheet():
    # Read secret — try base64 first, then raw JSON
    raw = os.environ.get("GOOGLE_CREDENTIALS", "").strip()
    if not raw:
        raise ValueError("GOOGLE_CREDENTIALS secret is empty!")
    
    # Try base64 decode first
    try:
        decoded = base64.b64decode(raw).decode("utf-8")
        creds_dict = json.loads(decoded)
        print("  Credentials loaded via base64")
    except Exception:
        # Try raw JSON
        try:
            creds_dict = json.loads(raw)
            print("  Credentials loaded via raw JSON")
        except Exception as e:
            raise ValueError(f"Cannot parse credentials: {e}\nFirst 100 chars: {raw[:100]}")

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"]
    )
    gc = gspread.authorize(creds)
    return gc.open_by_key(GOOGLE_SHEET_ID).sheet1


def get_captcha_token():
    print("  Getting Cloudflare token...")
    captured = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            "--no-sandbox","--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled"
        ])
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            viewport={"width":1366,"height":768}
        )
        page = ctx.new_page()

        def on_req(r):
            if "fileValidityNew" in r.url and r.method == "POST":
                try:
                    t = json.loads(r.post_data or "{}").get("recaptchaResponse")
                    if t: captured["token"] = t; print("  ✓ Token captured!")
                except: pass
        page.on("request", on_req)

        try:
            page.goto(ICP_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("input[type='radio']", timeout=15000)
            time.sleep(2)
            for txt in ["File No.","Visa","Emirate Unified Number"]:
                for lbl in page.locator("label").all():
                    try:
                        if txt.lower() in (lbl.inner_text() or "").lower():
                            lbl.click(); time.sleep(0.4); break
                    except: pass
            for inp in page.locator("input[type='text']:visible").all():
                try:
                    if "dd/" not in (inp.get_attribute("placeholder") or "").lower():
                        inp.fill("000000000"); break
                except: pass
            time.sleep(3)
            t = page.evaluate("()=>{const i=document.querySelector('input[name=\"cf-turnstile-response\"]');return i?i.value:null;}")
            if t: captured["token"] = t; print("  ✓ Token from widget!")
            if not captured.get("token"):
                for btn in page.locator("button").all():
                    try:
                        if "search" in (btn.inner_text() or "").lower():
                            btn.click(); time.sleep(3); break
                    except: pass
        except Exception as e:
            print(f"  Browser error: {e}")
        finally:
            browser.close()
    return captured.get("token")


def call_icp(emp, token):
    import requests
    nat_id = int(emp.get("NationalityId") or NATIONALITY_IDS.get(str(emp.get("Nationality","")).upper(),0))
    dob = str(emp.get("DOB",""))
    if "/" in dob:
        p = dob.split("/")
        if len(p)==3 and len(p[2])==4: dob = f"{p[2]}/{p[1]}/{p[0]}"
    body = {
        "fileModuleId": int(emp.get("FileModuleId",2)),
        "longUnifiedNumber": str(emp.get("UID","")),
        "nationalityId": nat_id,
        "dateOfBirth": dob,
        "serviceYear": None, "sequenceNumber": None, "expireDate": None,
        "isUsingCaptcha": True, "recaptchaResponse": token,
    }
    r = requests.post(ICP_API_URL, json=body, timeout=30, headers={
        "Content-Type":"application/json","Accept":"application/json, text/plain, */*",
        "Origin":"https://smartservices.icp.gov.ae",
        "Referer":"https://smartservices.icp.gov.ae/echannels/web/client/default.html",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    })
    return r.json()


def classify(status, expire):
    s = (status or "").upper()
    days = None
    if expire:
        try:
            p = str(expire).split("/")
            e = datetime(int(p[0]),int(p[1]),int(p[2])) if len(p[0])==4 else datetime(int(p[2]),int(p[1]),int(p[0]))
            days = (e - datetime.now()).days
        except: pass
    if any(x in s for x in ["CANCEL","OVERSTAY","EXPIRED","REJECTED","ABSCONDING"]): return "🔴 CRITICAL", days
    if days is not None and days < 0: return "🔴 CRITICAL", days
    if days is not None and days <= 30: return "🟡 WARNING", days
    if "ACTIVE" in s: return "🟢 OK", days
    return "⚪ UNKNOWN", days


def main():
    print("="*55)
    print("  ICP Visa Status Checker — GitHub Actions")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC")
    print("="*55)
    print("\nConnecting to Google Sheet...")
    sheet = connect_sheet()
    rows = sheet.get_all_records()
    headers = sheet.row_values(1)
    print(f"  Found {len(rows)} employees")
    if not rows:
        print("  Sheet is empty — add employees first!"); return

    today = datetime.now().strftime("%d/%m/%Y")
    results = []

    for i, emp in enumerate(rows):
        name = emp.get("Name", f"Row {i+2}")
        uid  = emp.get("UID","")
        if not uid: print(f"\nSkipping {name} — no UID"); continue
        print(f"\n[{i+1}/{len(rows)}] {name} — UID: {uid}")

        token = get_captcha_token()
        if not token:
            print("  ✗ No token"); continue

        try:
            raw = call_icp(emp, token)
            print(f"  Response: {str(raw)[:200]}")
        except Exception as e:
            print(f"  ✗ API error: {e}"); continue

        d = raw.get("data") or raw.get("result") or raw or {}
        status   = (d.get("fileStatus") or d.get("status") or "UNKNOWN").upper()
        expire   = d.get("fileExpireDate") or d.get("expireDate") or d.get("lastDateAllowedToEnterTheCountry")
        file_no  = d.get("fileNo") or d.get("fileNoFormatted") or "N/A"
        alert, days = classify(status, expire)

        print(f"  Status: {status} | Expiry: {expire} | Alert: {alert}")

        row = i + 2
        for col, val in {
            "FileNo": file_no, "FileStatus": status,
            "ExpiryDate": expire or "", "DaysLeft": days if days is not None else "",
            "AlertLevel": alert, "LastChecked": today
        }.items():
            if col in headers:
                sheet.update_cell(row, headers.index(col)+1, val)

        results.append({"name": name, "status": status, "alert": alert})
        time.sleep(2)

    print(f"\n{'='*55}\n  SUMMARY\n{'='*55}")
    for r in results:
        print(f"  {r['alert']}  {r['name']:<25} {r['status']}")
    print(f"\n  Done — {len(results)} checked")

if __name__ == "__main__":
    main()
