# ICP Visa Status Checker

Runs daily on GitHub Actions — completely free.

## Setup Steps

### 1. Create Google Sheet
Columns needed (exact names):
```
Name | UID | NationalityId | DOB | FileModuleId | SearchMethod | Phone | FileNo | FileStatus | ExpiryDate | DaysLeft | AlertLevel | LastChecked
```

### 2. Create Google Service Account
1. Go to console.cloud.google.com
2. Create new project → Enable Google Sheets API
3. Create Service Account → download JSON key
4. Share your Google Sheet with the service account email

### 3. Add GitHub Secrets
In your GitHub repo → Settings → Secrets → New secret:
- `GOOGLE_SHEET_ID` → your sheet ID from the URL
- `GOOGLE_CREDENTIALS` → paste the entire JSON key file content

### 4. Run manually first
Go to Actions tab → "ICP Visa Status Check" → Run workflow

## NationalityId Reference
| Country | ID |
|---------|-----|
| Egypt | 13 |
| Indonesia | 43 |
| India | 25 |
| Pakistan | 24 |
| Philippines | 40 |
| Bangladesh | 26 |
| Nepal | 39 |

## FileModuleId
- 1 = Residency
- 2 = Visa

## Alert Levels
- 🔴 CRITICAL — Canceled / Expired / Overstay
- 🟡 WARNING  — Expiring within 30 days
- 🟢 OK       — Active
- ⚪ UNKNOWN  — Could not retrieve

## Phase 2 — Adding WhatsApp (coming later)
Will use Green API free tier to send messages via personal WhatsApp.
