# AINS NILAM Recorder

**[切换至中文文档 →](README.zh.md)**

Automate submitting book reading records to the Malaysian **AINS NILAM** portal (`ains.moe.gov.my`).

Pure HTTP API — no browser, no screenshots, no OCR. Designed for AI agents to operate end-to-end.

---

## What This Project Does

AINS NILAM is Malaysia's national reading program. Students log every book they read on the portal. This tool automates that process:

1. AI searches the web for real book metadata (title, author, year, pages, publisher, ISBN)
2. AI writes a summary (`rumusan`) and moral lesson (`pengajaran`) in Malay or English
3. Python script POSTs the record directly to the AINS API
4. Supports **two student accounts simultaneously**

---

## Environment Requirements

| Requirement | Detail |
|---|---|
| **OS** | Any — Linux, macOS, Windows |
| **Python** | 3.7+ |
| **Dependencies** | `requests` (install: `pip install requests`) |
| **Network** | HTTPS access to `ains.moe.gov.my` |
| **Browser** | **Not required** |
| **Screenshot / OCR** | **Not required** |
| **GUI** | **Not required** |

```bash
pip install -r requirements.txt
```

---

## How It Works (Reverse-Engineered API)

| Step | Endpoint | Purpose |
|---|---|---|
| 1 | `GET /web/new-record-book` | Fetch CSRF token from `<meta name="csrf-token">` |
| 2 | `POST /reading-record/saverecord` | Submit the book record as form data |

**Success**: HTTP 200, body is exactly `success`.
**Failure**: HTTP 200, body is `failed`.

### Form Fields

| Field | Required | Values |
|---|---|---|
| `_csrf` | yes | extracted from meta tag |
| `jenis_rekod` | yes | always `book` |
| `kategori` | yes | `fiction` or `nonFiction` |
| `jenis` | yes | `physical` or `ebook` |
| `bahasa` | yes | `my` (Malay), `en` (English), `others` |
| `tajuk` | yes | book title |
| `tahun` | yes | 1900–2100 |
| `penulis` | yes | author name |
| `isbn` | no | optional |
| `mukasurat` | yes | integer page count |
| `penerbit` | yes | publisher |
| `pautan` | no | optional URL |
| `penilaian` | yes | 1–5 |
| `rumusan` | yes | summary, **>100 characters** |
| `pengajaran` | yes | moral lesson, **>100 characters** |
| `kulit` | no | cover image JPG/PNG, max 2MB |

---

## Discovered Server Rules (Tested 2026-10-07/08)

### 1. Three-minute cooldown (per account)

After submitting a book, you **must wait 180 seconds** before submitting another to the same account. The page shows:

> *"Rekod bacaan hanya boleh ditambah semula selepas tempoh 3 minit."*

If you submit too fast, the API returns `failed`.

### 2. Dual accounts are independent

Account 1 and Account 2 have separate cooldown timers. **Submit to both back-to-back, then wait 3 minutes.**

```
Submit A1 → Submit A2 → wait 3 min → next book
```

### 3. Daily limit: ~50 books per account per day

**Tested on 2026-10-08**: successfully submitted **~49 books** per account before the server started returning `failed` for both accounts. The limit appears to be **~50 books/day per account**. It resets the next day.

Earlier manual testing by the user reported ~30 books/day; the limit may have been raised since.

### 4. Cookie lifespan

- `PHPSESSID`: session cookie
- `_csrf`: session cookie
- `_identity`: 86400 seconds (24 hours)

If submissions return login-page redirects, cookies have expired — user needs to provide fresh ones.

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
  "account1": { "cookie": "PHPSESSID=xxx; _csrf=yyy; _identity=zzz;" },
  "account2": { "cookie": "PHPSESSID=aaa; _csrf=bbb; _identity=ccc;" }
}
```

### Step 3: Run

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

### Batch mode with cooldown

See `batch_submit.py`. Pattern:

```python
for i, book in enumerate(books):
    submit_book(cookie1, **book)
    submit_book(cookie2, **book)
    if i < len(books) - 1:
        time.sleep(180)
```

---

## For AI Agents

This repo is a self-contained Skill. When an AI agent reads `SKILL.md`, it will:

1. Understand the AINS API endpoint and field requirements
2. Know the 3-minute cooldown and ~50/day limit
3. Search the web for book metadata
4. Write `rumusan` and `pengajaran` in Malay or English (>100 chars each)
5. Call `submit_book.py` to POST
6. Wait 3 minutes between rounds

No browser, no visual reasoning, no DOM manipulation needed.

---

## Book Selection Guidelines

- **Prioritize Malay novels** (`bahasa=my`)
- **Then English novels** (`bahasa=en`)
- **Physical books** (`jenis=physical`)
- **Long novels** (300+ pages preferred)
- **Avoid**: Chinese books, short pamphlets, audiobooks without page counts

---

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | AI agent skill definition |
| `submit_book.py` | Core Python submission module |
| `batch_submit.py` | Example batch runner with 3-min cooldown |
| `cookies.json` | User's session cookies (gitignored) |
| `requirements.txt` | Python dependencies |
| `README.zh.md` | Chinese documentation |

---

## Disclaimer

This tool is for educational automation. Users are responsible for ensuring compliance with AINS NILAM terms and their school's requirements. Not affiliated with Kementerian Pendidikan Malaysia.
