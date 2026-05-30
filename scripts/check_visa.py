import json, time, os, base64, requests
from datetime import datetime
from playwright.sync_api import sync_playwright

ICP_URL    = "https://smartservices.icp.gov.ae/echannels/web/client/default.html#/fileValidity"
N8N_WEBHOOK = "https://nouriatravel7.app.n8n.cloud/webhook/icp-result"
CREDS_B64  = "eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogImtlZW4tZGVmZW5kZXItNDk3ODA3LWsxIiwgInByaXZhdGVfa2V5X2lkIjogIjU3YzlmMjY3ZTAyNzRiYTMyM2EyODNkMTBiYjI5NWJmODJjNTk5NWUiLCAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdlFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUUMrN1VXODg0S2xkdXFLXG5oM3RLZEMycEU0emQraUhRc0R1V1A3cG1LWFRLc05FakFjdDBjTVZIU0llcTFOVkVqWEdjL3lnVnRJMW96SlNFXG5DbkRyUkg0Nndxd1l1WTBqM1kvRTVmd2EzSENGUEJEelI3NE03c3dSQzBSelI2RjdpUlNLRzdJdEI2SWdHMWhEXG5iSTdFOEpHbWVWemFudUU2LytlNGVvbFNrK2k2OU4xNmpnUkJReGxNb3ExWHBuYXFCd2VXZHVuMW5MaktTOGRQXG56YWNEWDBWN1JJSmduQ3plM0JxN3FHYW4vdU5PUmZBSjJKWU9IcWhjRGNIUXg0T2w1b3NKaGEycmtZcUxtbXZ1XG4vRVRLSkovd1NRZ3dvU25RSm5LN0JjeWtyTE1hT0cvelA1Qm9INFJ2Z0RTdUpzcWwzUko3b3dXSnlxY1Eyb1VFXG5MSWErNkNzOUFnTUJBQUVDZ2dFQUl2UGhtenFTTFpRRVVvbUVlT2dsYnNsSk5kOERuMGFRRmd6REpVNU1Gd3BCXG5NekV5SzdZMGEzMGI5eHFCRTR4NFl1YzBVYXJzNDJWbWYvakFYTlc4YlNuejR3L2ZCcFNhYkErMWRENXNhL3ZIXG4xNTNIN1dxdkdhU3dLcEdQdnNPazZyYXd5djBWZ1Y2NExSbTcxbEo3TzVpR3R2QTBwLzR1eis5QTRnajVaM1k0XG4xeDhHTzJlZ3lORGR2bTFOZkV6ZzYvelNsY2lQMVg5RXZxVDNpNkt0S1B0VnVrUk1RMWd4N3JMT254UGRKTTNhXG5yMWx0elFQRDlKZGl1cFUvZUVLdmI5S2w2eWRzMWhrYTlZRUgyUkpSM1JYMzZWdDBLK05lUUVaRE1oVkdWRFdEXG5ReHVKSXhNSjlUVHlnQUxvMEZSdUpncnIvV1NoRFNkYVY4WnpVblhRcVFLQmdRRHJFQWx4V0ZYOXl1MDRQV2NDXG43YUM3WDQ4K1dvaFV2cXFSTFo0ZS9oUmk3ZS9UM1B2VUVqY2xoRFNOS2JwYU1pZTg4aGJzK01HZysrRUM3WC9pXG5ETW45RDZJRW9qaHZGcDd0LzdyWUh4bUltbkg4bmZXOUI1b2hLQm1qS1pnVVVuRFcyWENlbSt1ZXMrVW9IdzRuXG40VS9Jb1hVWlBwQ2JaZ2RuK2VnMDJxQStHUUtCZ1FEUDd0YkIrMFlpS09lckVhNFB0YXVxZmJKdi9nb0FtZjJBXG5QVzNPUFZvRWV2c1U3bU1kQ1NzcDdzblpKTVRCOERDVStUV3NkM1I5WnA4KzRXY1NGL3JpcWZFYnUvZGJGWnNTXG5tRVRRb0VPdk9pWFNuSDQxNUNHUW80RzBrNnJJbWhiUy9lU04xSFRlYjRDMEpnczJpTTFhc3R2SFo5SlNGY3B2XG5QcXBFZ1NPeXhRS0JnQ2FHWVZYUFNZQ240b3NtSFJ6d3Z6Z1dhRTZxM2M4dDFKeW9vbEtvQjhWVEE4eHdXbUdlXG5mcVZLYnFaNElVK3BDclEvNVJ2L2hSU1NVNFY4VVVwR0dGQytZQ3BzUDkyTkVvMGxMWVZBUzVvRTNndXVBOWx3XG5Sb1dLb2ZFSTN5RHRoZ3JnWmtISWdpeG5oWFkyNk1ZR2VtSUNmRU9mNm1sZHBuY1hFVVNnVkVUNUFvR0FaQ3huXG5VQnJUQmQvNUJDUkhYQkFrdk1WRHNzcUxYUkRTM1BZN01WSERUVWRHTVNaTG41QnNPQTV2TmVxTjAvVDRJcjBRXG55NTdkQXhEdWhTZW9OVUpTUHVLcVlyY2lpc0lVN0ZkcFI2eitEcXdQenJCUDZYeVhZd3d5ajZGWWRMNHZZc1NvXG5XRi9UVWRvY0FpNFYxdGIvUDhQTk4vcmZpMll1R1h2eUlZQ3BoeFVDZ1lFQXVYd3BackZuSlc2b1BlSkNYOW5xXG5hM3luekJtNkVwTGVyNzVUeTQxRlo5eWJPSjAzalVWTEZVN1lKYk5UVWNjTE1TNTlhNHlnNmpNdkRyZjQ0eUN4XG5ZaE9pWi8vS3dOekpLNlpxMmcwV1U1ckFOWjZSeVNjS0NQclhKeS83Rmd2eVgzSFFMU2c2cGxnMGxVMER5Q0R5XG5iT1BZeFZ3elp2NU5pT3gzd3BsL1N5Yz1cbi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS1cbiIsICJjbGllbnRfZW1haWwiOiAiaWNwLWNoZWNrZXJAa2Vlbi1kZWZlbmRlci00OTc4MDctazEuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCAiY2xpZW50X2lkIjogIjExMjE4MDUzMDUwNjY1NzM4NjE3MyIsICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsICJ0b2tlbl91cmkiOiAiaHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4iLCAiYXV0aF9wcm92aWRlcl94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL29hdXRoMi92MS9jZXJ0cyIsICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L2ljcC1jaGVja2VyJTQwa2Vlbi1kZWZlbmRlci00OTc4MDctazEuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCAidW5pdmVyc2VfZG9tYWluIjogImdvb2dsZWFwaXMuY29tIn0="

MAX_TEST_EMPLOYEES = int(os.environ.get("MAX_TEST_EMPLOYEES", "0"))

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => ({length:3})});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
window.chrome = {runtime:{}, loadTimes:function(){}, csi:function(){}, app:{}};
"""

def connect_sheet():
    import gspread
    from google.oauth2.service_account import Credentials
    creds_dict = json.loads(base64.b64decode(CREDS_B64).decode("utf-8"))
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"]
    )
    gc = gspread.authorize(creds)
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "1dv-IV3ZuwZJL6s6rkmQbEdzx7YAQfGljbfA_u6voZEQ")
    return gc.open_by_key(sheet_id).sheet1

def classify(status, expire):
    s = (status or "").upper()
    days = None
    if expire:
        try:
            p = str(expire).split("/")
            e = datetime(int(p[0]), int(p[1]), int(p[2])) if len(p[0]) == 4 \
                else datetime(int(p[2]), int(p[1]), int(p[0]))
            days = (e - datetime.now()).days
        except:
            pass
    if any(x in s for x in ["CANCEL", "OVERSTAY", "EXPIRED", "REJECTED", "ABSCONDING"]):
        return "CRITICAL", days
    if days is not None and days < 0:    return "EXPIRED",  days
    if days is not None and days <= 10:  return "WARNING",  days
    if "ACTIVE" in s or (days is not None and days > 10): return "OK", days
    return "UNKNOWN", days

def setup_page(playwright):
    browser = playwright.chromium.launch(
        headless=False,
        args=["--no-sandbox", "--disable-setuid-sandbox",
              "--disable-dev-shm-usage",
              "--disable-blink-features=AutomationControlled"]
    )
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1366, "height": 768},
        locale="en-US",
    )
    page = ctx.new_page()
    page.add_init_script(STEALTH_JS)
    return browser, page

def load_icp_page(page):
    print("  Loading ICP page...")
    page.goto(ICP_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("input[type='radio']", timeout=20000)
    time.sleep(2)
    for lbl in page.locator("label").all():
        try:
            text = (lbl.inner_text() or "").lower()
            if "emirate unified" in text or "unified number" in text:
                lbl.click()
                time.sleep(1)
                break
        except:
            pass
    print("  ICP page ready.")

def check_employee(page, uid, dob_raw=""):
    captured = {}

    def on_response(r):
        if "fileValidityNew" in r.url and r.status == 200:
            try:
                captured["data"] = r.json()
            except:
                pass

    page.on("response", on_response)
    try:
        for inp in page.locator("input[type='text']:visible").all():
            try:
                ph = (inp.get_attribute("placeholder") or "").lower()
                if "dd/" not in ph and "mm/" not in ph:
                    inp.triple_click()
                    inp.fill(uid)
                    break
            except:
                pass

        if dob_raw:
            for inp in page.locator("input[type='text']:visible").all():
                try:
                    ph = (inp.get_attribute("placeholder") or "").lower()
                    if "dd/" in ph or "mm/" in ph:
                        inp.triple_click()
                        inp.fill(dob_raw)
                        break
                except:
                    pass

        time.sleep(1)

        for btn in page.locator("button:visible").all():
            try:
                if "search" in (btn.inner_text() or "").lower():
                    btn.click()
                    break
            except:
                pass

        for _ in range(20):
            if captured.get("data"):
                break
            time.sleep(1)

    except Exception as e:
        print(f"  Form error: {e}")
    finally:
        page.remove_listener("response", on_response)

    try:
        for btn in page.locator("button:visible").all():
            try:
                txt = (btn.inner_text() or "").lower()
                if any(x in txt for x in ["clear", "new", "reset", "back"]):
                    btn.click()
                    time.sleep(1)
                    break
            except:
                pass
    except:
        pass

    return captured.get("data")

def post_to_n8n(payload):
    try:
        r = requests.post(N8N_WEBHOOK, json=payload, timeout=15)
        return r.status_code == 200
    except Exception as e:
        print(f"  ⚠ n8n POST failed: {e}")
        return False

def main():
    print("=" * 55)
    print("  ICP Visa Checker — n8n Webhook Mode")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 55)

    print("\nConnecting to Google Sheet...")
    sheet = connect_sheet()
    rows = sheet.get_all_records()
    print(f"  Found {len(rows)} employees")

    if not rows:
        print("  Sheet is empty.")
        return

    employee_list = rows[:MAX_TEST_EMPLOYEES] if MAX_TEST_EMPLOYEES else rows
    if MAX_TEST_EMPLOYEES:
        print(f"\n⚠ DRY RUN — first {MAX_TEST_EMPLOYEES} employees only")

    today = datetime.now().strftime("%Y-%m-%d")
    ok = expired = warning = errors = 0

    with sync_playwright() as pw:
        browser, page = setup_page(pw)
        try:
            load_icp_page(page)

            for i, emp in enumerate(employee_list):
                name = (emp.get("VISA  NAME ") or emp.get("Customer Name") or f"Row {i+2}")
                uid  = str(emp.get("Emirate Unified Number") or "").strip()
                dob  = str(emp.get("dateOfBirth") or "").strip()
                file_no = str(emp.get("File No.") or "").strip()

                if not uid:
                    print(f"\n[{i+1}/{len(employee_list)}] Skipping {name} — no UID")
                    continue

                print(f"\n[{i+1}/{len(employee_list)}] {name} | UID: {uid}")

                raw = check_employee(page, uid, dob)

                if not raw:
                    print("  ✗ No response — reloading and retrying...")
                    load_icp_page(page)
                    raw = check_employee(page, uid, dob)

                if not raw:
                    print("  ✗ Skipping after retry")
                    errors += 1
                    continue

                d = raw.get("data") or raw.get("result") or raw or {}
                status   = (d.get("fileStatus") or "UNKNOWN").upper()
                expire   = d.get("lastDateAllowedToEnterTheCountry") or \
                           d.get("lastDateAllowedToEnter") or ""
                file_iss = d.get("fileIssuanceDate") or ""
                file_can = d.get("fileCancellationDate") or ""
                alert, days = classify(status, expire)

                print(f"  ✓ {status} | Expires: {expire} | Alert: {alert} | Days: {days}")

                payload = {
                    "fileNo":             file_no or d.get("fileNo") or uid,
                    "fileStatus":         status,
                    "fileIssuanceDate":   file_iss,
                    "lastDateAllowed":    expire,
                    "fileCancellationDate": file_can,
                    "alertLevel":         alert,
                    "daysLeft":           str(days) if days is not None else "",
                    "lastChecked":        today,
                }

                if post_to_n8n(payload):
                    print("  ✓ Sent to n8n")
                else:
                    print("  ✗ n8n POST failed")

                if alert == "OK":       ok += 1
                elif alert == "WARNING": warning += 1
                elif alert in ("EXPIRED", "CRITICAL"): expired += 1
                else: errors += 1

                time.sleep(2)

        finally:
            browser.close()

    print(f"\n{'=' * 55}")
    print(f"  DONE — OK: {ok} | WARNING: {warning} | EXPIRED: {expired} | Errors: {errors}")
    print(f"{'=' * 55}")

if __name__ == "__main__":
    main()
