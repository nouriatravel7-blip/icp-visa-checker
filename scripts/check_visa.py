import json, time, os, base64, gspread
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from google.oauth2.service_account import Credentials

GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
ICP_URL     = "https://smartservices.icp.gov.ae/echannels/web/client/default.html#/fileValidity"
ICP_API_URL = "https://beta.smartservices.icp.gov.ae/echannels/api/api/landing/fileValidityNew"
CREDS_B64   = "eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogImtlZW4tZGVmZW5kZXItNDk3ODA3LWsxIiwgInByaXZhdGVfa2V5X2lkIjogIjU3YzlmMjY3ZTAyNzRiYTMyM2EyODNkMTBiYjI5NWJmODJjNTk5NWUiLCAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdlFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUUMrN1VXODg0S2xkdXFLXG5oM3RLZEMycEU0emQraUhRc0R1V1A3cG1LWFRLc05FakFjdDBjTVZIU0llcTFOVkVqWEdjL3lnVnRJMW96SlNFXG5DbkRyUkg0Nndxd1l1WTBqM1kvRTVmd2EzSENGUEJEelI3NE03c3dSQzBSelI2RjdpUlNLRzdJdEI2SWdHMWhEXG5iSTdFOEpHbWVWemFudUU2LytlNGVvbFNrK2k2OU4xNmpnUkJReGxNb3ExWHBuYXFCd2VXZHVuMW5MaktTOGRQXG56YWNEWDBWN1JJSmduQ3plM0JxN3FHYW4vdU5PUmZBSjJKWU9IcWhjRGNIUXg0T2w1b3NKaGEycmtZcUxtbXZ1XG4vRVRLSkovd1NRZ3dvU25RSm5LN0JjeWtyTE1hT0cvelA1Qm9INFJ2Z0RTdUpzcWwzUko3b3dXSnlxY1Eyb1VFXG5MSWErNkNzOUFnTUJBQUVDZ2dFQUl2UGhtenFTTFpRRVVvbUVlT2dsYnNsSk5kOERuMGFRRmd6REpVNU1Gd3BCXG5NekV5SzdZMGEzMGI5eHFCRTR4NFl1YzBVYXJzNDJWbWYvakFYTlc4YlNuejR3L2ZCcFNhYkErMWRENXNhL3ZIXG4xNTNIN1dxdkdhU3dLcEdQdnNPazZyYXd5djBWZ1Y2NExSbTcxbEo3TzVpR3R2QTBwLzR1eis5QTRnajVaM1k0XG4xeDhHTzJlZ3lORGR2bTFOZkV6ZzYvelNsY2lQMVg5RXZxVDNpNkt0S1B0VnVrUk1RMWd4N3JMT254UGRKTTNhXG5yMWx0elFQRDlKZGl1cFUvZUVLdmI5S2w2eWRzMWhrYTlZRUgyUkpSM1JYMzZWdDBLK05lUUVaRE1oVkdWRFdEXG5ReHVKSXhNSjlUVHlnQUxvMEZSdUpncnIvV1NoRFNkYVY4WnpVblhRcVFLQmdRRHJFQWx4V0ZYOXl1MDRQV2NDXG43YUM3WDQ4K1dvaFV2cXFSTFo0ZS9oUmk3ZS9UM1B2VUVqY2xoRFNOS2JwYU1pZTg4aGJzK01HZysrRUM3WC9pXG5ETW45RDZJRW9qaHZGcDd0LzdyWUh4bUltbkg4bmZXOUI1b2hLQm1qS1pnVVVuRFcyWENlbSt1ZXMrVW9IdzRuXG40VS9Jb1hVWlBwQ2JaZ2RuK2VnMDJxQStHUUtCZ1FEUDd0YkIrMFlpS09lckVhNFB0YXVxZmJKdi9nb0FtZjJBXG5QVzNPUFZvRWV2c1U3bU1kQ1NzcDdzblpKTVRCOERDVStUV3NkM1I5WnA4KzRXY1NGL3JpcWZFYnUvZGJGWnNTXG5tRVRRb0VPdk9pWFNuSDQxNUNHUW80RzBrNnJJbWhiUy9lU04xSFRlYjRDMEpnczJpTTFhc3R2SFo5SlNGY3B2XG5QcXBFZ1NPeXhRS0JnQ2FHWVZYUFNZQ240b3NtSFJ6d3Z6Z1dhRTZxM2M4dDFKeW9vbEtvQjhWVEE4eHdXbUdlXG5mcVZLYnFaNElVK3BDclEvNVJ2L2hSU1NVNFY4VVVwR0dGQytZQ3BzUDkyTkVvMGxMWVZBUzVvRTNndXVBOWx3XG5Sb1dLb2ZFSTN5RHRoZ3JnWmtISWdpeG5oWFkyNk1ZR2VtSUNmRU9mNm1sZHBuY1hFVVNnVkVUNUFvR0FaQ3huXG5VQnJUQmQvNUJDUkhYQkFrdk1WRHNzcUxYUkRTM1BZN01WSERUVWRHTVNaTG41QnNPQTV2TmVxTjAvVDRJcjBRXG55NTdkQXhEdWhTZW9OVUpTUHVLcVlyY2lpc0lVN0ZkcFI2eitEcXdQenJCUDZYeVhZd3d5ajZGWWRMNHZZc1NvXG5XRi9UVWRvY0FpNFYxdGIvUDhQTk4vcmZpMll1R1h2eUlZQ3BoeFVDZ1lFQXVYd3BackZuSlc2b1BlSkNYOW5xXG5hM3luekJtNkVwTGVyNzVUeTQxRlo5eWJPSjAzalVWTEZVN1lKYk5UVWNjTE1TNTlhNHlnNmpNdkRyZjQ0eUN4XG5ZaE9pWi8vS3dOekpLNlpxMmcwV1U1ckFOWjZSeVNjS0NQclhKeS83Rmd2eVgzSFFMU2c2cGxnMGxVMER5Q0R5XG5iT1BZeFZ3elp2NU5pT3gzd3BsL1N5Yz1cbi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS1cbiIsICJjbGllbnRfZW1haWwiOiAiaWNwLWNoZWNrZXJAa2Vlbi1kZWZlbmRlci00OTc4MDctazEuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCAiY2xpZW50X2lkIjogIjExMjE4MDUzMDUwNjY1NzM4NjE3MyIsICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsICJ0b2tlbl91cmkiOiAiaHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4iLCAiYXV0aF9wcm92aWRlcl94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL29hdXRoMi92MS9jZXJ0cyIsICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L2ljcC1jaGVja2VyJTQwa2Vlbi1kZWZlbmRlci00OTc4MDctazEuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCAidW5pdmVyc2VfZG9tYWluIjogImdvb2dsZWFwaXMuY29tIn0="

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

def get_captcha_token():
    print("  Getting Cloudflare token via browser...")
    captured = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome", args=[
            "--no-sandbox","--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled"
        ])
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            viewport={"width":1366,"height":768}
        )
        page = ctx.new_page()
        Stealth().apply_stealth_sync(page)

        def on_req(r):
            if "fileValidityNew" in r.url and r.method == "POST":
                try:
                    body = json.loads(r.post_data or "{}")
                    t = body.get("recaptchaResponse") or body.get("token") or body.get("captchaToken")
                    if t:
                        captured["token"] = t
                        print("  ✓ Token captured from request!")
                except: pass

        page.on("request", on_req)
        try:
            page.goto(ICP_URL, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_selector("input[type='radio']", timeout=20000)
            time.sleep(2)

            # Select "Emirate Unified Number" under File Type
            for lbl in page.locator("label").all():
                try:
                    txt = (lbl.inner_text() or "").strip().lower()
                    if "emirate unified" in txt:
                        lbl.click(); time.sleep(0.5); break
                except: pass

            # Fill in the UID field
            for inp in page.locator("input[type='text']:visible").all():
                try:
                    ph = (inp.get_attribute("placeholder") or "").lower()
                    if "dd/" not in ph and "date" not in ph:
                        inp.fill("000000000"); break
                except: pass

            time.sleep(1)

            # Click the Search/Check button
            clicked = False
            for btn in page.locator("button").all():
                try:
                    txt = (btn.inner_text() or "").strip().lower()
                    if any(w in txt for w in ["search", "check", "submit", "enquire"]):
                        btn.click(); clicked = True; print("  Clicked search button"); break
                except: pass

            if not clicked:
                # Try any visible button as fallback
                btns = page.locator("button:visible").all()
                if btns:
                    btns[-1].click(); print("  Clicked fallback button")

            # Wait up to 10s for token to be captured via request intercept
            for _ in range(20):
                if captured.get("token"): break
                time.sleep(0.5)

            # Also check Turnstile hidden input
            if not captured.get("token"):
                t = page.evaluate("""()=>{
                    const selectors = [
                        'input[name="cf-turnstile-response"]',
                        'input[name="g-recaptcha-response"]',
                        'textarea[name="g-recaptcha-response"]'
                    ];
                    for(const s of selectors){
                        const el = document.querySelector(s);
                        if(el && el.value) return el.value;
                    }
                    return null;
                }""")
                if t:
                    captured["token"] = t
                    print("  ✓ Token from page widget!")

        except Exception as e:
            print(f"  Browser error: {e}")
        finally:
            browser.close()
    return captured.get("token")

def call_icp(emp, token):
    import requests
    nat_id = int(emp.get("NationalityId") or NATIONALITY_IDS.get(str(emp.get("Nationality","")).upper(), 0))
    dob = str(emp.get("DOB") or emp.get("dateOfBirth") or "")
    if "/" in dob:
        p = dob.split("/")
        if len(p) == 3 and len(p[2]) == 4:
            dob = f"{p[2]}/{p[1]}/{p[0]}"
    uid = str(emp.get("Emirate Unified Number") or emp.get("UID") or "")
    body = {
        "fileModuleId": int(emp.get("fileModuleId") or emp.get("FileModuleId") or 2),
        "longUnifiedNumber": uid,
        "nationalityId": nat_id,
        "dateOfBirth": dob,
        "serviceYear": None, "sequenceNumber": None, "expireDate": None,
        "isUsingCaptcha": True, "recaptchaResponse": token,
    }
    import requests as req
    r = req.post(ICP_API_URL, json=body, timeout=30, headers={
        "Content-Type":"application/json",
        "Accept":"application/json, text/plain, */*",
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
    print(f"  Sheet headers: {headers}")
    if not rows:
        print("  Sheet is empty — please add employee data!"); return

    today = datetime.now().strftime("%d/%m/%Y")
    results = []

    for i, emp in enumerate(rows):
        # Support both old and new column names
        name = (emp.get("VISA  NAME ") or emp.get("VISA_NAME") or
                emp.get("Customer Name") or emp.get("Name") or f"Row {i+2}")
        uid  = str(emp.get("Emirate Unified Number") or emp.get("UID") or "").strip()

        if not uid:
            print(f"\n[{i+1}/{len(rows)}] Skipping {name} — no UID"); continue

        print(f"\n[{i+1}/{len(rows)}] Checking: {name} — UID: {uid}")

        token = get_captcha_token()
        if not token:
            print("  ✗ No CAPTCHA token, skipping"); continue

        try:
            raw = call_icp(emp, token)
            print(f"  ICP Response: {str(raw)[:250]}")
        except Exception as e:
            print(f"  ✗ API error: {e}"); continue

        d = raw.get("data") or raw.get("result") or raw or {}
        status   = (d.get("fileStatus") or d.get("status") or "UNKNOWN").upper()
        expire   = (d.get("lastDateAllowedToEnterTheCountry") or
                    d.get("fileExpireDate") or d.get("expireDate") or "")
        file_no  = d.get("fileNo") or d.get("fileNoFormatted") or ""
        file_iss = d.get("fileIssuanceDate") or d.get("issuanceDate") or ""
        file_can = d.get("fileCancellationDate") or d.get("cancellationDate") or ""
        alert, days = classify(status, expire)

        print(f"  ✓ Status: {status} | Last Date: {expire} | Alert: {alert}")

        # Map to new column names — update only columns that exist in the sheet
        col_map = {
            "File No":               file_no,
            "File Status":           status,
            "File Issuance Date":    file_iss,
            "Last Date Allowed to Enter the Country": expire,
            "File Cancellation Date": file_can,
            "AlertLevel":            alert,
            "DaysLeft":              days if days is not None else "",
            "LastChecked":           today,
        }

        row_num = i + 2
        for col_name, val in col_map.items():
            if col_name in headers:
                sheet.update_cell(row_num, headers.index(col_name) + 1, val)
            else:
                print(f"  ⚠ Column '{col_name}' not found in sheet headers — skipping")

        results.append({"name": name, "status": status, "alert": alert})
        time.sleep(2)

    print(f"\n{'='*55}\n  SUMMARY\n{'='*55}")
    for r in results:
        print(f"  {r['alert']}  {r['name']:<25} {r['status']}")
    print(f"\n  Done — {len(results)} employees checked")

if __name__ == "__main__":
    main()
