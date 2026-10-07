# AINS NILAM Recorder

Automate submitting book reading records to the Malaysian **AINS NILAM** portal (`ains.moe.gov.my`).

Pure HTTP API — no browser, no screenshots, no OCR. Works with any AI agent that can run Python.

---

## What it does

The AINS NILAM system is Malaysia's national reading program. Students log every book they read online. This tool automates that process:

1. AI searches the web for real book metadata (title, author, pages, publisher, year)
2. AI writes a Malay/English summary (`rumusan`) and moral lesson (`pengajaran`)
3. Python script POSTs the record directly to the AINS API
4. Supports **two student accounts simultaneously**

---

## Requirements

| Requirement | Detail |
|---|---|
| **Python** | 3.7+ |
| **Dependencies** | `requests` (only) |
| **OS** | Any — Linux, macOS, Windows |
| **Browser** | **Not needed** |
| **Visual/OCR** | **Not needed** |
| **Network** | HTTPS access to `ains.moe.gov.my` |
| **Cookies** | Session cookies from both accounts (one-time setup) |

### Install

```bash
pip install requests
```

---

## How It Works (Reverse-Engineered API)

The AINS web app is a Yii2 PHP application. We discovered:

| Step | Endpoint | Purpose |
|---|---|---|
| 1 | `GET /web/new-record-book` | Fetch CSRF token from `<meta name="csrf-token">` |
| 2 | `POST /reading-record/saverecord` | Submit the book record as form data |

**Success response**: HTTP 200, body is exactly `success` (plain text).
**Failure response**: HTTP 200, body is `failed` (plain text).

### Form fields

| Field | Required | Values |
|---|---|---|
| `_csrf` | yes | from meta tag |
| `jenis_rekod` | yes | always `book` |
| `kategori` | yes | `fiction` or `nonFiction` |
| `jenis` | yes | `physical` or `ebook` |
| `bahasa` | yes | `my` (Malay), `en` (English), `others` |
| `tajuk` | yes | book title |
| `tahun` | yes | 1900–2100 |
| `penulis` | yes | author name |
| `isbn` | no | optional string |
| `mukasurat` | yes | integer page count |
| `penerbit` | yes | publisher |
| `pautan` | no | optional URL |
| `penilaian` | yes | 1–5 |
| `rumusan` | yes | summary, **>100 characters** |
| `pengajaran` | yes | moral lesson, **>100 characters** |
| `kulit` | no | cover image file (JPG/PNG, max 2MB) |

---

## Discovered Server Rules

### 1. 3-minute cooldown (per account)

After submitting a book, you **must wait 180 seconds** before submitting another to the same account. The server shows this message on the page:

> *"Rekod bacaan hanya boleh ditambah semula selepas tempoh 3 minit. Sila cuba lagi selepas 3 minit."*

If you submit too fast, the API returns `failed`.

### 2. Dual accounts are independent

Account 1 and Account 2 have separate cooldown timers. **Submit to both back-to-back, then wait 3 minutes.** Do NOT wait between the two accounts.

```
Submit A1 → Submit A2 → wait 3 min → next book
```

### 3. Daily limit

**Tested up to 31 books per account — still successful, no limit hit.**

The user previously reported a ~30 book/day cap when submitting manually, but testing on 2026-10-07 showed the API accepting at least 31 books per account without any rejection. The daily limit may have been raised, or it may reset at a different time of day. Further testing needed to find the actual ceiling.

### 4. Cookie lifespan

- `PHPSESSID`: session cookie (dies when browser closes)
- `_csrf`: session cookie
- `_identity`: 86400 seconds (24 hours)

If submissions start failing with login-page redirects, the user needs to provide fresh cookies.

---

## Setup

### Step 1: Get cookies

1. Log into `ains.moe.gov.my` in Chrome (Google OAuth)
2. Press F12 → **Application** tab → **Cookies** → `https://ains.moe.gov.my`
3. Copy all cookies as a semicolon-joined string:
   ```
   PHPSESSID=abc123; _csrf=def456; _identity=ghi789;
   ```
4. Repeat for the second account

### Step 2: Save cookies

Create `cookies.json`:

```json
{
  "account1": {
    "cookie": "PHPSESSID=xxx; _csrf=yyy; _identity=zzz;"
  },
  "account2": {
    "cookie": "PHPSESSID=aaa; _csrf=bbb; _identity=ccc;"
  }
}
```

### Step 3: Submit a book

```python
from submit_book import submit_to_both
import json

with open("cookies.json") as f:
    accs = json.load(f)

result = submit_to_both(
    cookie1=accs["account1"]["cookie"],
    cookie2=accs["account2"]["cookie"],
    tajuk="Laskar Pelangi",
    tahun=2005,
    penulis="Andrea Hirata",
    mukasurat=529,
    penerbit="Bentang Pustaka",
    kategori="fiction",
    bahasa="my",
    penilaian=4,
    rumusan="...(more than 100 characters)...",
    pengajaran="...(more than 100 characters)...",
)
print(result)
```

### Step 4: Batch mode with 3-min waits

```python
import time, json
from submit_book import submit_book

with open("cookies.json") as f:
    accs = json.load(f)

books = [
    {"tajuk": "Book 1", ...},
    {"tajuk": "Book 2", ...},
]

for i, book in enumerate(books):
    submit_book(accs["account1"]["cookie"], **book)
    submit_book(accs["account2"]["cookie"], **book)
    if i < len(books) - 1:
        time.sleep(180)  # 3 minutes
```

---

## AI Agent Integration

This repo is designed as a **Skill** for AI agents (like Doubao, Claude, GPT). The AI:

1. Reads `SKILL.md` to understand the API
2. Searches the web for book metadata
3. Writes `rumusan` and `pengajaran` in Malay or English
4. Calls `submit_book.py` to POST
5. Waits 3 minutes between rounds

The AI does **not** need:
- Browser control
- Screenshot/OCR
- Visual reasoning
- DOM manipulation

It only needs:
- HTTP requests (Python `requests` library)
- Web search (to find book facts)
- Text generation (to write summaries)

---

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | AI agent skill definition |
| `submit_book.py` | Core Python submission module |
| `batch_submit.py` | Example batch runner with 3-min cooldown |
| `cookies.json` | User's session cookies (gitignore'd) |
| `requirements.txt` | Python dependencies |

---

## Book Selection Guidelines

- **Prioritize Malay novels** (bahasa `my`)
- **Then English novels** (bahasa `en`)
- **Physical books** (`jenis=physical`)
- **Long novels** (300+ pages preferred)
- **Avoid**: Chinese books, short pamphlets, audiobooks without page counts

---

## Disclaimer

This tool is for educational automation purposes. Users are responsible for ensuring their use complies with AINS NILAM terms and their school's requirements. The author is not affiliated with Kementerian Pendidikan Malaysia.
