import json, time, os, base64, gspread, subprocess
from datetime import datetime
from playwright.sync_api import sync_playwright
from google.oauth2.service_account import Credentials

GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
ICP_URL     = "https://smartservices.icp.gov.ae/echannels/web/client/default.html#/fileValidity"
ICP_API_URL = "https://beta.smartservices.icp.gov.ae/echannels/api/api/landing/fileValidityNew"
CREDS_B64   = "eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogImtlZW4tZGVmZW5kZXItNDk3ODA3LWsxIiwgInByaXZhdGVfa2V5X2lkIjogIjU3YzlmMjY3ZTAyNzRiYTMyM2EyODNkMTBiYjI5NWJmODJjNTk5NWUiLCAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdlFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUUMrN1VXODg0S2xkdXFLXG5oM3RLZEMycEU0emQraUhRc0R1V1A3cG1LWFRLc05FakFjdDBjTVZIU0llcTFOVkVqWEdjL3lnVnRJMW96SlNFXG5DbkRyUkg0Nndxd1l1WTBqM1kvRTVmd2EzSENGUEJEelI3NE03c3dSQzBSelI2RjdpUlNLRzdJdEI2SWdHMWhEXG5iSTdFOEpHbWVWemFudUU2LytlNGVvbFNrK2k2OU4xNmpnUkJReGxNb3ExWHBuYXFCd2VXZHVuMW5MaktTOGRQXG56YWNEWDBWN1JJSmduQ3plM0JxN3FHYW4vdU5PUmZBSjJKWU9IcWhjRGNIUXg0T2w1b3NKaGEycmtZcUxtbXZ1XG4vRVRLSkovd1NRZ3dvU25RSm5LN0JjeWtyTE1hT0cvelA1Qm9INFJ2Z0RTdUpzcWwzUko3b3dXSnlxY1Eyb1VFXG5MSWErNkNzOUFnTUJBQUVDZ2dFQUl2UGhtenFTTFpRRVVvbUVlT2dsYnNsSk5kOERuMGFRRmd6REpVNU1Gd3BCXG5NekV5SzdZMGEzMGI5eHFCRTR4NFl1YzBVYXJzNDJWbWYvakFYTlc4YlNuejR3L2ZCcFNhYkErMWRENXNhL3ZIXG4xNTNIN1dxdkdhU3dLcEdQdnNPazZyYXd5djBWZ1Y2NExSbTcxbEo3TzVpR3R2QTBwLzR1eis5QTRnajVaM1k0XG4xeDhHTzJlZ3lORGR2bTFOZkV6ZzYvelNsY2lQMVg5RXZxVDNpNkt0S1B0VnVrUk1RMWd4N3JMT254UGRKTTNhXG5yMWx0elFQRDlKZGl1cFUvZUVLdmI5S2w2eWRzMWhrYTlZRUgyUkpSM1JYMzZWdDBLK05lUUVaRE1oVkdWRFdEXG5ReHVKSXhNSjlUVHlnQUxvMEZSdUpncnIvV1NoRFNkYVY4WnpVblhRcVFLQmdRRHJFQWx4V0ZYOXl1MDRQV2NDXG43YUM3WDQ4K1dvaFV2cXFSTFo0ZS9oUmk3ZS9UM1B2VUVqY2xoRFNOS2JwYU1pZTg4aGJzK01HZysrRUM3WC9pXG5ETW45RDZJRW9qaHZGcDd0LzdyWUh4bUltbkg4bmZXOUI1b2hLQm1qS1pnVVVuRFcyWENlbSt1ZXMrVW9IdzRuXG40VS9Jb1hVWlBwQ2JaZ2RuK2VnMDJxQStHUUtCZ1FEUDd0YkIrMFlpS09lckVhNFB0YXVxZmJKdi9nb0FtZjJBXG5QVzNPUFZvRWV2c1U3bU1kQ1NzcDdzblpKTVRCOERDVStUV3NkM1I5WnA4KzRXY1NGL3JpcWZFYnUvZGJGWnNTXG5tRVRRb0VPdk9pWFNuSDQxNUNHUW80RzBrNnJJbWhiUy9lU04xSFRlYjRDMEpnczJpTTFhc3R2SFo5SlNGY3B2XG5QcXBFZ1NPeXhRS0JnQ2FHWVZYUFNZQ240b3NtSFJ6d3Z6Z1dhRTZxM2M4dDFKeW9vbEtvQjhWVEE4eHdXbUdlXG5mcVZLYnFaNElVK3BDclEvNVJ2L2hSU1NVNFY4VVVwR0dGQytZQ3BzUDkyTkVvMGxMWVZBUzVvRTNndXVBOWx3XG5Sb1dLb2ZFSTN5RHRoZ3JnWmtISWdpeG5oWFkyNk1ZR2VtSUNmRU9mNm1sZHBuY1hFVVNnVkVUNUFvR0FaQ3huXG5VQnJUQmQvNUJDUkhYQkFrdk1WRHNzcUxYUkRTM1BZN01WSERUVWRHTVNaTG41QnNPQTV2TmVxTjAvVDRJcjBRXG55NTdkQXhEdWhTZW9OVUpTUHVLcVlyY2lpc0lVN0ZkcFI2eitEcXdQenJCUDZYeVhZd3d5ajZGWWRMNHZZc1NvXG5XRi9UVWRvY0FpNFYxdGIvUDhQTk4vcmZpMll1R1h2eUlZQ3BoeFVDZ1lFQXVYd3BackZuSlc2b1BlSkNYOW5xXG5hM3luekJtNkVwTGVyNzVUeTQxRlo5eWJPSjAzalVWTEZVN1lKYk5UVWNjTE1TNTlhNHlnNmpNdkRyZjQ0eUN4XG5ZaE9pWi8vS3dOekpLNlpxMmcwV1U1ckFOWjZSeVNjS0NQclhKeS83Rmd2eVgzSFFMU2c2cGxnMGxVMER5Q0R5XG5iT1BZeFZ3elp2NU5pT3gzd3BsL1N5Yz1cbi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS1cbiIsICJjbGllbnRfZW1haWwiOiAiaWNwLWNoZWNrZXJAa2Vlbi1kZWZlbmRlci00OTc4MDctazEuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCAiY2xpZW50X2lkIjogIjExMjE4MDUzMDUwNjY1NzM4NjE3MyIsICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsICJ0b2tlbl91cmkiOiAiaHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4iLCAiYXV0aF9wcm92aWRlcl94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL29hdXRoMi92MS9jZXJ0cyIsICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L2ljcC1jaGVja2VyJTQwa2Vlbi1kZWZlbmRlci00OTc4MDctazEuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCAidW5pdmVyc2VfZG9tYWluIjogImdvb2dsZWFwaXMuY29tIn0="

NATIONALITY_MAP = {
    "EGYPT": "Egypt", "INDONESIA": "Indonesia", "INDIA": "India",
    "PAKISTAN": "Pakistan", "PHILIPPINES": "Philippines",
    "BANGLADESH": "Bangladesh", "NEPAL": "Nepal", "SRI LANKA": "Sri Lanka",
    "ETHIOPIA": "Ethiopia", "KENYA": "Kenya", "NIGERIA": "Nigeria",
    "JORDAN": "Jordan", "SYRIA": "Syria", "LEBANON": "Lebanon",
    "SUDAN": "Sudan", "MOROCCO": "Morocco",
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

def check_via_browser(page, emp):
    """Fill the ICP form with real employee data and capture the API response."""
    captured = {}

    def on_response(r):
        if r.request.method == "POST":
            print(f"  POST response: {r.url[:80]} status={r.status}")
        if "fileValidityNew" in r.url and r.request.method == "POST":
            try:
                captured["data"] = r.json()
                print(f"  ✓ API response captured: {str(captured['data'])[:200]}")
            except Exception as e:
                print(f"  ✗ Failed to parse response: {e}")

    page.on("response", on_response)

    try:
        uid = str(emp.get("Emirate Unified Number") or "").strip()
        nationality = NATIONALITY_MAP.get(str(emp.get("Nationality", "")).upper(), "")
        dob_raw = str(emp.get("dateOfBirth") or emp.get("DOB") or "").strip()

        # Convert DOB to dd/MM/yyyy for the form
        dob = dob_raw
        if dob and "/" in dob:
            parts = dob.split("/")
            if len(parts) == 3 and len(parts[0]) == 4:
                # yyyy/MM/dd → dd/MM/yyyy
                dob = f"{parts[2]}/{parts[1]}/{parts[0]}"

        raw_module = str(emp.get("fileModuleId") or "2").strip().lower()
        file_module = 1 if raw_module in ("1", "residency") else 2
        type_label = "Visa" if file_module == 2 else "Residency"

        if ICP_URL not in (page.url or ""):
            page.goto(ICP_URL, wait_until="domcontentloaded", timeout=45000)
        else:
            page.reload(wait_until="domcontentloaded", timeout=45000)
        page.wait_for_selector("input[type='radio']", timeout=20000)

        # Wait for Cloudflare widget to appear first
        print("  Waiting for Cloudflare widget to load...")
        try:
            page.wait_for_selector("iframe[src*='cloudflare'], iframe[src*='recaptcha'], .g-recaptcha, #cf-turnstile", timeout=15000)
        except:
            pass
        time.sleep(3)  # Give the widget time to run its checks

        # Now check if it passed or failed
        print("  Checking Cloudflare result...")
        for _ in range(40):
            failed = page.locator("text=Verification failed").count()
            if failed == 0:
                print("  ✓ Cloudflare passed!")
                break
            print(f"  Still verifying...")
            time.sleep(0.5)
        else:
            print("  ✗ Cloudflare verification failed — skipping")
            return None

        time.sleep(1)

        # Select the Type: Visa (2) or Residency (1)
        try:
            page.locator(f"input[name='selectModule'][value='{file_module}']").click()
            time.sleep(0.4)
        except: pass

        # Select "Emirate Unified Number" radio button
        for lbl in page.locator("label").all():
            try:
                if "emirate unified" in (lbl.inner_text() or "").lower():
                    lbl.click(); time.sleep(0.5); break
            except: pass

        # Fill UID
        uid_input = page.locator("input[type='text']:visible").first
        uid_input.fill(uid)
        time.sleep(0.3)

        # Select nationality — Angular custom dropdown
        if nationality:
            try:
                nat_dropdown = page.locator(".ui-select-container, select, [ng-model*='nation'], [ng-model*='Nation']").first
                nat_dropdown.click()
                time.sleep(0.5)
                search_box = page.locator(".ui-select-search, input[placeholder*='earch'], input[placeholder*='elect']").first
                search_box.fill(nationality)
                time.sleep(0.8)
                page.locator(f".ui-select-choices-row:has-text('{nationality}'), li:has-text('{nationality}'), option:has-text('{nationality}')").first.click()
                time.sleep(0.3)
            except:
                try:
                    page.locator("select").first.select_option(label=nationality)
                except: pass

        # Fill Date of Birth (format: dd/MM/yyyy)
        if dob:
            try:
                dob_input = page.locator("input[placeholder*='Date'], input[placeholder*='date'], input[placeholder*='dd/']").first
                dob_input.click()
                dob_input.fill(dob)
                page.keyboard.press("Tab")
                time.sleep(0.3)
            except: pass

        time.sleep(1)

        # Check reCAPTCHA token value before clicking
        token_val = page.evaluate("""()=>{
            const selectors = ['textarea[name="g-recaptcha-response"]','input[name="cf-turnstile-response"]'];
            for(const s of selectors){
                const el = document.querySelector(s);
                if(el) return el.value || '(empty)';
            }
            return 'not found';
        }""")
        print(f"  CAPTCHA token before search: {token_val[:60]}")

        # Click Search button
        for btn in page.locator("button:visible").all():
            try:
                txt = (btn.inner_text() or "").strip().lower()
                if any(w in txt for w in ["search", "check", "submit"]):
                    btn.click()
                    print("  Clicked Search button")
                    break
            except: pass

        time.sleep(3)

        # Check for any error message shown after clicking Search
        for err_sel in ["text=reCAPTCHA", "text=CAPTCHA", "text=Verification", ".alert", ".error", "[class*='error']", "[class*='alert']"]:
            try:
                err = page.locator(err_sel).first.inner_text()
                if err.strip():
                    print(f"  Page message: {err.strip()[:100]}")
                    break
            except: pass

        # Wait 3 seconds for results to render
        time.sleep(3)

        # Scrape directly via JavaScript
        scraped = page.evaluate("""() => {
            const rows = document.querySelectorAll('span, label, td, p, div');
            const data = {};
            const labels = {
                'File Status': 'fileStatus',
                'File No': 'fileNo',
                'File Issuance Date': 'fileIssuanceDate',
                'Last Date Allowed': 'lastDate',
                'File Cancellation Date': 'cancelDate'
            };
            rows.forEach(el => {
                const txt = (el.innerText || '').trim();
                for (const [label, key] of Object.entries(labels)) {
                    if (txt.startsWith(label) && txt.includes(':')) {
                        data[key] = txt.split(':').slice(1).join(':').trim();
                    }
                }
            });
            return data;
        }""")
        print(f"  Scraped: {scraped}")
        if scraped.get("fileStatus"):
            captured["data"] = {
                "fileStatus":                       scraped.get("fileStatus", ""),
                "fileNo":                           scraped.get("fileNo", ""),
                "fileIssuanceDate":                 scraped.get("fileIssuanceDate", ""),
                "lastDateAllowedToEnterTheCountry": scraped.get("lastDate", ""),
                "fileCancellationDate":             scraped.get("cancelDate", ""),
            }

    except Exception as e:
        print(f"  Browser error: {e}")
    finally:
        page.remove_listener("response", on_response)

    return captured.get("data")

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
    print("  ICP Visa Status Checker")
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

    # Launch real Chrome directly to the ICP page with remote debugging
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    chrome_exe = next((cp for cp in chrome_paths if os.path.exists(cp)), None)
    if not chrome_exe:
        raise RuntimeError("Chrome not found. Please install Google Chrome.")

    chrome_proc = subprocess.Popen([
        chrome_exe,
        f"--remote-debugging-port=9222",
        f"--user-data-dir=C:\\chrome-icp-session",
        "--no-first-run",
        "--no-default-browser-check",
        "--start-maximized",
        ICP_URL,   # Open ICP page directly on launch
    ])
    print("  Chrome launched — waiting for it to load...")
    time.sleep(6)  # Give Chrome time to open and load the page

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        print(f"  Connected to Chrome. Contexts: {len(browser.contexts)}")
        if browser.contexts:
            ctx = browser.contexts[0]
            # Use existing page or open new one
            pages = ctx.pages
            page = pages[0] if pages else ctx.new_page()
        else:
            ctx = browser.new_context()
            page = ctx.new_page()
        print(f"  Browser ready. Starting checks...")

        for i, emp in enumerate(rows):
            name = (emp.get("VISA  NAME ") or emp.get("Customer Name") or emp.get("Name") or f"Row {i+2}")
            uid  = str(emp.get("Emirate Unified Number") or "").strip()

            if not uid:
                print(f"\n[{i+1}/{len(rows)}] Skipping {name} — no UID"); continue

            print(f"\n[{i+1}/{len(rows)}] Checking: {name} — UID: {uid}")

            raw = check_via_browser(page, emp)
            if not raw:
                print("  ✗ No response received, skipping"); continue

            status   = (raw.get("fileStatus") or "UNKNOWN").upper().strip()
            expire   = (raw.get("lastDateAllowedToEnterTheCountry") or "").strip()
            file_no  = (raw.get("fileNo") or "").strip()
            file_iss = (raw.get("fileIssuanceDate") or "").strip()
            file_can = (raw.get("fileCancellationDate") or "").strip()
            alert, days = classify(status, expire)

            print(f"  ✓ Status: {status} | Expires: {expire} | Alert: {alert}")

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
            for col_name, val in col_map.items():
                if col_name in headers:
                    sheet.update_cell(row_num, headers.index(col_name) + 1, val)
                else:
                    print(f"  ⚠ Column '{col_name}' not in sheet — skipping")

            results.append({"name": name, "status": status, "alert": alert})
            time.sleep(1)

        browser.close()
    chrome_proc.terminate()

    print(f"\n{'='*55}\n  SUMMARY\n{'='*55}")
    for r in results:
        print(f"  {r['alert']}  {r['name']:<25} {r['status']}")
    print(f"\n  Done — {len(results)} employees checked")

if __name__ == "__main__":
    main()
