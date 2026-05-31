import json, time, os, base64, gspread, subprocess
from datetime import datetime
from playwright.sync_api import sync_playwright
from google.oauth2.service_account import Credentials

GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
ICP_URL  = "https://smartservices.icp.gov.ae/echannels/web/client/default.html#/fileValidity"
API_URL  = "https://smartservices.icp.gov.ae/echannels/api/api/landing/fileValidityNew"
CREDS_B64 = "eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogImtlZW4tZGVmZW5kZXItNDk3ODA3LWsxIiwgInByaXZhdGVfa2V5X2lkIjogIjU3YzlmMjY3ZTAyNzRiYTMyM2EyODNkMTBiYjI5NWJmODJjNTk5NWUiLCAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdlFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUUMrN1VXODg0S2xkdXFLXG5oM3RLZEMycEU0emQraUhRc0R1V1A3cG1LWFRLc05FakFjdDBjTVZIU0llcTFOVkVqWEdjL3lnVnRJMW96SlNFXG5DbkRyUkg0Nndxd1l1WTBqM1kvRTVmd2EzSENGUEJEelI3NE03c3dSQzBSelI2RjdpUlNLRzdJdEI2SWdHMWhEXG5iSTdFOEpHbWVWemFudUU2LytlNGVvbFNrK2k2OU4xNmpnUkJReGxNb3ExWHBuYXFCd2VXZHVuMW5MaktTOGRQXG56YWNEWDBWN1JJSmduQ3plM0JxN3FHYW4vdU5PUmZBSjJKWU9IcWhjRGNIUXg0T2w1b3NKaGEycmtZcUxtbXZ1XG4vRVRLSkovd1NRZ3dvU25RSm5LN0JjeWtyTE1hT0cvelA1Qm9INFJ2Z0RTdUpzcWwzUko3b3dXSnlxY1Eyb1VFXG5MSWErNkNzOUFnTUJBQUVDZ2dFQUl2UGhtenFTTFpRRVVvbUVlT2dsYnNsSk5kOERuMGFRRmd6REpVNU1Gd3BCXG5NekV5SzdZMGEzMGI5eHFCRTR4NFl1YzBVYXJzNDJWbWYvakFYTlc4YlNuejR3L2ZCcFNhYkErMWRENXNhL3ZIXG4xNTNIN1dxdkdhU3dLcEdQdnNPazZyYXd5djBWZ1Y2NExSbTcxbEo3TzVpR3R2QTBwLzR1eis5QTRnajVaM1k0XG4xeDhHTzJlZ3lORGR2bTFOZkV6ZzYvelNsY2lQMVg5RXZxVDNpNkt0S1B0VnVrUk1RMWd4N3JMT254UGRKTTNhXG5yMWx0elFQRDlKZGl1cFUvZUVLdmI5S2w2eWRzMWhrYTlZRUgyUkpSM1JYMzZWdDBLK05lUUVaRE1oVkdWRFdEXG5ReHVKSXhNSjlUVHlnQUxvMEZSdUpncnIvV1NoRFNkYVY4WnpVblhRcVFLQmdRRHJFQWx4V0ZYOXl1MDRQV2NDXG43YUM3WDQ4K1dvaFV2cXFSTFo0ZS9oUmk3ZS9UM1B2VUVqY2xoRFNOS2JwYU1pZTg4aGJzK01HZysrRUM3WC9pXG5ETW45RDZJRW9qaHZGcDd0LzdyWUh4bUltbkg4bmZXOUI1b2hLQm1qS1pnVVVuRFcyWENlbSt1ZXMrVW9IdzRuXG40VS9Jb1hVWlBwQ2JaZ2RuK2VnMDJxQStHUUtCZ1FEUDd0YkIrMFlpS09lckVhNFB0YXVxZmJKdi9nb0FtZjJBXG5QVzNPUFZvRWV2c1U3bU1kQ1NzcDdzblpKTVRCOERDVStUV3NkM1I5WnA4KzRXY1NGL3JpcWZFYnUvZGJGWnNTXG5tRVRRb0VPdk9pWFNuSDQxNUNHUW80RzBrNnJJbWhiUy9lU04xSFRlYjRDMEpnczJpTTFhc3R2SFo5SlNGY3B2XG5QcXBFZ1NPeXhRS0JnQ2FHWVZYUFNZQ240b3NtSFJ6d3Z6Z1dhRTZxM2M4dDFKeW9vbEtvQjhWVEE4eHdXbUdlXG5mcVZLYnFaNElVK3BDclEvNVJ2L2hSU1NVNFY4VVVwR0dGQytZQ3BzUDkyTkVvMGxMWVZBUzVvRTNndXVBOWx3XG5Sb1dLb2ZFSTN5RHRoZ3JnWmtISWdpeG5oWFkyNk1ZR2VtSUNmRU9mNm1sZHBuY1hFVVNnVkVUNUFvR0FaQ3huXG5VQnJUQmQvNUJDUkhYQkFrdk1WRHNzcUxYUkRTM1BZN01WSERUVWRHTVNaTG41QnNPQTV2TmVxTjAvVDRJcjBRXG55NTdkQXhEdWhTZW9OVUpTUHVLcVlyY2lpc0lVN0ZkcFI2eitEcXdQenJCUDZYeVhZd3d5ajZGWWRMNHZZc1NvXG5XRi9UVWRvY0FpNFYxdGIvUDhQTk4vcmZpMll1R1h2eUlZQ3BoeFVDZ1lFQXVYd3BackZuSlc2b1BlSkNYOW5xXG5hM3luekJtNkVwTGVyNzVUeTQxRlo5eWJPSjAzalVWTEZVN1lKYk5UVWNjTE1TNTlhNHlnNmpNdkRyZjQ0eUN4XG5ZaE9pWi8vS3dOekpLNlpxMmcwV1U1ckFOWjZSeVNjS0NQclhKeS83Rmd2eVgzSFFMU2c2cGxnMGxVMER5Q0R5XG5iT1BZeFZ3elp2NU5pT3gzd3BsL1N5Yz1cbi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS1cbiIsICJjbGllbnRfZW1haWwiOiAiaWNwLWNoZWNrZXJAa2Vlbi1kZWZlbmRlci00OTc4MDctazEuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCAiY2xpZW50X2lkIjogIjExMjE4MDUzMDUwNjY1NzM4NjE3MyIsICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsICJ0b2tlbl91cmkiOiAiaHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4iLCAiYXV0aF9wcm92aWRlcl94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL29hdXRoMi92MS9jZXJ0cyIsICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L2ljcC1jaGVja2VyJTQwa2Vlbi1kZWZlbmRlci00OTc4MDctazEuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCAidW5pdmVyc2VfZG9tYWluIjogImdvb2dsZWFwaXMuY29tIn0="

# Nationality name → ICP nationalityId
NATIONALITY_ID = {
    "EGYPT": 13, "INDONESIA": 43, "INDIA": 25, "PAKISTAN": 24,
    "PHILIPPINES": 40, "BANGLADESH": 26, "NEPAL": 39,
    "SRI LANKA": 196, "ETHIOPIA": 70, "KENYA": 113,
    "NIGERIA": 155, "JORDAN": 107, "SYRIA": 204,
    "LEBANON": 121, "SUDAN": 197, "MOROCCO": 143,
    "MYANMAR": 148, "GHANA": 80, "CAMEROON": 44,
    "TANZANIA": 206, "UGANDA": 218, "VIETNAM": 227,
    "THAILAND": 207, "CHINA": 49, "MALAYSIA": 130,
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

def load_page_and_pass_cloudflare(page):
    """Load ICP page, wait for Cloudflare to verify, return Turnstile token."""
    page.goto(ICP_URL, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_selector("input[type='radio']", timeout=20000)

    print("  Waiting for Cloudflare...")
    try:
        page.wait_for_selector("iframe[src*='cloudflare'], iframe[src*='recaptcha'], #cf-turnstile", timeout=15000)
    except: pass
    time.sleep(3)

    for _ in range(40):
        if page.locator("text=Verification failed").count() == 0:
            print("  ✓ Cloudflare passed!")
            break
        time.sleep(0.5)
    else:
        raise RuntimeError("Cloudflare failed")

    time.sleep(1)
    return get_token(page)

def get_token(page):
    """Extract current Turnstile/reCAPTCHA token from the page DOM."""
    return page.evaluate("""() => {
        for (const s of ['input[name="cf-turnstile-response"]',
                         'textarea[name="g-recaptcha-response"]',
                         'input[name="turnstile-response"]']) {
            const el = document.querySelector(s);
            if (el && el.value) return el.value;
        }
        return null;
    }""")

def refresh_token(page):
    """Ask Turnstile widget to generate a new token (no page reload needed)."""
    page.evaluate("if (window.turnstile) { window.turnstile.reset(); }")
    for _ in range(20):
        tok = get_token(page)
        if tok:
            return tok
        time.sleep(0.3)
    # Fallback: full page reload
    print("  Token refresh failed — reloading page...")
    return load_page_and_pass_cloudflare(page)

def call_api(page, emp, token):
    """Make POST directly from Chrome's JS context — cookies included automatically."""
    uid = str(emp.get("Emirate Unified Number") or "").strip()
    nat_key = str(emp.get("Nationality", "")).upper().strip()
    nat_id  = NATIONALITY_ID.get(nat_key)

    dob_raw = str(emp.get("dateOfBirth") or emp.get("DOB") or "").strip()
    dob = dob_raw
    if dob and "/" in dob:
        parts = dob.split("/")
        if len(parts) == 3 and len(parts[0]) == 4:
            pass  # already YYYY/MM/DD
        elif len(parts) == 3:
            dob = f"{parts[2]}/{parts[1]}/{parts[0]}"  # dd/MM/yyyy → YYYY/MM/DD

    raw_module = str(emp.get("fileModuleId") or "2").strip().lower()
    file_module = 1 if raw_module in ("1", "residency") else 2

    payload = {
        "serviceYear": None,
        "sequenceNumber": None,
        "nationalityId": nat_id,
        "fileModuleId": file_module,
        "longUnifiedNumber": uid,
        "expireDate": None,
        "isUsingCaptcha": True if token else False,
        "recaptchaResponse": token,
        "dateOfBirth": dob,
    }

    result = page.evaluate("""async ([url, payload]) => {
        try {
            const r = await fetch(url, {
                method: 'POST',
                headers: {
                    'accept': 'application/json, text/plain, */*',
                    'content-type': 'application/json;charset=UTF-8',
                    'current_portal': 'ICA',
                    'languageid': '2',
                },
                body: JSON.stringify(payload)
            });
            return { ok: r.ok, status: r.status, data: await r.json() };
        } catch(e) {
            return { ok: false, error: e.toString() };
        }
    }""", [API_URL, payload])

    return result

def fmt_date(dt_str):
    if not dt_str: return ""
    return str(dt_str).split("T")[0].replace("-", "/")

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
    print("  ICP Visa Status Checker  (Direct API mode)")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("="*55)
    print("\nConnecting to Google Sheet...")
    sheet = connect_sheet()
    rows = sheet.get_all_records()
    headers = sheet.row_values(1)
    print(f"  Found {len(rows)} employees")
    if not rows:
        print("  Sheet is empty — please add employee data!"); return

    today = datetime.now().strftime("%d/%m/%Y")
    results = []

    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    chrome_exe = next((cp for cp in chrome_paths if os.path.exists(cp)), None)
    if not chrome_exe:
        raise RuntimeError("Chrome not found.")

    chrome_proc = subprocess.Popen([
        chrome_exe,
        "--remote-debugging-port=9222",
        "--user-data-dir=C:\\chrome-icp-session",
        "--no-first-run",
        "--no-default-browser-check",
        "--start-maximized",
        ICP_URL,
    ])
    print("  Chrome launched — waiting for it to load...")
    time.sleep(6)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        ctx  = browser.contexts[0] if browser.contexts else browser.new_context()
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        print(f"  Connected to Chrome. Starting checks...")

        # Pass Cloudflare once, get initial token
        token = load_page_and_pass_cloudflare(page)
        print(f"  Token: {'found' if token else 'NOT FOUND — will try without'}")
        token_uses = 0

        for i, emp in enumerate(rows):
            name = (emp.get("VISA  NAME ") or emp.get("Customer Name") or emp.get("Name") or f"Row {i+2}")
            uid  = str(emp.get("Emirate Unified Number") or "").strip()

            if not uid:
                print(f"\n[{i+1}/{len(rows)}] Skipping {name} — no UID"); continue

            print(f"\n[{i+1}/{len(rows)}] {name} — UID: {uid}", end="  ", flush=True)

            # Refresh token after each use (Turnstile tokens are single-use)
            if token_uses > 0:
                token = refresh_token(page)
                if not token:
                    print("(no token — trying anyway)")

            result = call_api(page, emp, token)
            token_uses += 1

            if not result or not result.get("ok"):
                status_code = (result or {}).get("status", "?")
                print(f"✗ API error {status_code}")
                # If 400/403, might need page reload for fresh session
                if status_code in (400, 403, 401):
                    print("  Refreshing session...")
                    token = load_page_and_pass_cloudflare(page)
                    token_uses = 0
                    result = call_api(page, emp, token)
                    token_uses += 1
                    if not result or not result.get("ok"):
                        print("  ✗ Still failed, skipping"); continue

            raw = result.get("data", {})
            d   = raw.get("fileValidity") or raw
            svc = d.get("serviceStatus") or {}
            status   = (svc.get("text") or svc.get("enDescription") or
                        svc.get("description") or d.get("fileStatus") or "UNKNOWN").upper().strip()
            expire   = fmt_date(d.get("validityDate") or d.get("expireDate") or
                                 d.get("lastDateAllowedToEnterTheCountry") or d.get("fileExpireDate"))
            file_no  = (d.get("fileNo") or d.get("fileNoFormatted") or
                        f"{d.get('fileDepartmentCode','')}/{d.get('fileServiceYear','')}/{d.get('fileServiceCode','')}/{d.get('fileSequenceNumber','')}").strip("/")
            file_iss = fmt_date(d.get("issuanceDate") or d.get("fileIssuanceDate"))
            file_can = fmt_date(d.get("cancelDate") or d.get("fileCancellationDate"))
            alert, days = classify(status, expire)

            print(f"→ {alert} {status} | {expire}")

            col_map = {
                "File No.":                               file_no,
                "File Status":                            status,
                "File Issuance Date":                     file_iss,
                "Last Date Allowed to Enter the Country": expire,
                "File Cancellation Date":                 file_can,
                "AlertLevel":                             alert,
                "DaysLeft":                               days if days is not None else "",
                "LastChecked":                            today,
            }

            row_num = i + 2
            batch = []
            for col_name, val in col_map.items():
                if col_name in headers:
                    col_idx = headers.index(col_name) + 1
                    col_letter = chr(64 + col_idx) if col_idx <= 26 else f"A{chr(64 + col_idx - 26)}"
                    batch.append({"range": f"{col_letter}{row_num}", "values": [[str(val)]]})
            if batch:
                sheet.batch_update(batch)

            results.append({"name": name, "status": status, "alert": alert})

        browser.close()
    chrome_proc.terminate()

    print(f"\n{'='*55}\n  SUMMARY\n{'='*55}")
    for r in results:
        print(f"  {r['alert']}  {r['name']:<30} {r['status']}")
    print(f"\n  Done — {len(results)} employees checked")

if __name__ == "__main__":
    main()
