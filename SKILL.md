---
name: ains-nilam-recorder
description: "Automate submitting book reading records to the Malaysian AINS NILAM portal (ains.moe.gov.my). Direct HTTP API only — no browser needed. Supports dual accounts. Requires session cookies from user. Key constraint: 3-minute cooldown between submissions per account."
---

# AINS NILAM Recorder — Direct API Mode

Submits book records to `POST /reading-record/saverecord` using raw HTTP requests with session cookies. No browser, no visual OCR, no JS rendering. Just `requests.get` + `requests.post`.

## Discovered Rules (tested 2026-10-07)

| Rule | Detail |
|---|---|
| **Cooldown** | Each account must wait **180 seconds (3 minutes)** between submissions. If you submit too soon, server returns plain text `failed`. |
| **Daily limit** | User reports ~30 books/day per account. Not yet confirmed by this skill. Test carefully. |
| **Dual account** | Two accounts are independent. Submit to A1 then A2 back-to-back, THEN wait 3 minutes. Do NOT wait between A1 and A2. |
| **Success response** | HTTP 200, body is exactly `success` (plain text). Anything else = failed. |
| **Session cookies** | `PHPSESSID` + `_csrf` + `_identity` cookies. `_identity` lasts 24 hours. Cookies may need refreshing. |

## One-time Setup

User logs into ains.moe.gov.my on their own browser (Google OAuth works there), then provides cookies.

**How user gets cookies:**
1. Log into ains.moe.gov.my in Chrome
2. F12 → Application tab → Cookies → https://ains.moe.gov.my
3. Copy all cookie name=value pairs as a semicolon-joined string
4. Repeat for second account

Save in `cookies.json`:
```json
{
  "account1": { "cookie": "PHPSESSID=xxx; _csrf=yyy; _identity=zzz;" },
  "account2": { "cookie": "PHPSESSID=aaa; _csrf=bbb; _identity=ccc;" }
}
```

## Core API Flow

### Step 1: Get CSRF token

```python
import re, requests
r = requests.get(
    "https://ains.moe.gov.my/web/new-record-book",
    headers={"Cookie": cookie_str},
    verify=False, timeout=30
)
csrf = re.search(r'csrf-token" content="([^"]+)"', r.text).group(1)
```

If the page shows "Rekod bacaan hanya boleh ditambah semula selepas tempoh 3 minit" — you're in cooldown, wait.

### Step 2: Submit the book

```python
data = {
    "_csrf": csrf,
    "jenis_rekod": "book",
    "kategori": "fiction",      # or "nonFiction"
    "jenis": "physical",         # or "ebook"
    "bahasa": "my",              # "my"=Malay, "en"=English, "others"
    "tajuk": "Book Title",
    "tahun": "2005",
    "penulis": "Author Name",
    "isbn": "978-xxx",           # optional, can be empty
    "mukasurat": "300",          # page count, integer
    "penerbit": "Publisher",
    "pautan": "",                # optional URL, can be empty
    "penilaian": "4",            # 1-5
    "rumusan": "...",            # MUST be >100 chars
    "pengajaran": "...",          # MUST be >100 chars
    # "kulit": open("/tmp/cover.jpg","rb")  # optional cover image
}
r = requests.post(
    "https://ains.moe.gov.my/reading-record/saverecord",
    data=data,
    headers={"Cookie": cookie_str, "X-CSRF-Token": csrf},
    verify=False, timeout=30
)
success = (r.text.strip() == "success")
```

## Field Reference

| Field | Required | Values |
|---|---|---|
| `jenis_rekod` | yes | always `book` |
| `kategori` | yes | `fiction` or `nonFiction` |
| `jenis` | yes | `physical` or `ebook` |
| `bahasa` | yes | `my`, `en`, `others` |
| `tajuk` | yes | book title (string) |
| `tahun` | yes | 1900–2100 (integer) |
| `penulis` | yes | author name |
| `isbn` | no | string, can be empty |
| `mukasurat` | yes | integer page count |
| `penerbit` | yes | publisher name |
| `pautan` | no | URL string, can be empty |
| `penilaian` | yes | 1–5 |
| `rumusan` | yes | summary, **>100 characters** |
| `pengajaran` | yes | lesson/reflection, **>100 characters** |
| `kulit` | no | JPG/PNG file upload, max 2MB |

## Batch Submission Pattern

```python
import time

books = [ ... ]  # list of book dicts

for i, book in enumerate(books):
    # Submit to BOTH accounts back-to-back (no wait between them)
    result_a1 = submit_one(cookie1, book)
    result_a2 = submit_one(cookie2, book)
    print(f"Book {i+1}: A1={result_a1} A2={result_a2}")

    # THEN wait 3 minutes before next book
    if i < len(books) - 1:
        time.sleep(180)
```

**CRITICAL**: Do NOT wait 3 min between A1 and A2. The cooldown is per-account, so submit both immediately, then wait.

## What to do when a submission fails

1. **First retry**: wait 180 seconds, then try the same book again. Most likely cause = cooldown not elapsed.
2. **Check cookies**: if CSRF extraction fails or response is a login page, cookies expired — user needs to provide fresh ones.
3. **Check daily limit**: if both accounts return `failed` after proper 3-min waits, you may have hit the daily cap (~30 books).
4. **Don't spam**: repeated failed submissions can flag the account.

## Book Data Generation

The AI should search the web for real book information:
- Title, author, year, pages, publisher, ISBN
- Write `rumusan` (summary) in Malay or English, ~150-200 words
- Write `pengajaran` (moral lesson) in same language, ~100-150 words
- Prefer: **Malay novels first, then English novels, physical books, long novels**
- Avoid: Chinese books, short pamphlets, audiobooks without page counts

## Files in this skill

- `SKILL.md` — this document
- `submit_book.py` — Python helper function
- `cookies.json` — dual account cookies (user-provided)
