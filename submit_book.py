#!/usr/bin/env python3
"""
AINS NILAM book record submitter.
Usage:
    from submit_book import submit_book
    result = submit_book(cookie="...", tajuk="...", ...)
"""

import re
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://ains.moe.gov.my"


def get_csrf(cookie: str) -> str:
    """Fetch the new-record page and extract CSRF token from meta tag."""
    r = requests.get(
        f"{BASE}/web/new-record-book",
        headers={"Cookie": cookie},
        verify=False,
        allow_redirects=True,
        timeout=30,
    )
    m = re.search(r'csrf-token"\s+content="([^"]+)"', r.text)
    if not m:
        raise RuntimeError(f"CSRF token not found. Status {r.status_code}. "
                           f"Maybe cookie expired. URL: {r.url}")
    return m.group(1)


def submit_book(
    cookie: str,
    tajuk: str,
    tahun: int,
    penulis: str,
    mukasurat: int,
    penerbit: str,
    rumusan: str,
    pengajaran: str,
    kategori: str = "fiction",
    jenis: str = "physical",
    bahasa: str = "my",
    isbn: str = "",
    pautan: str = "",
    penilaian: int = 4,
    cover_path: str = "",
) -> dict:
    """
    Submit one book record to AINS.

    Returns {"success": bool, "detail": str}.
    """
    if len(rumusan) < 100:
        return {"success": False, "detail": f"Rumusan too short ({len(rumusan)} chars, need >100)"}
    if len(pengajaran) < 100:
        return {"success": False, "detail": f"Pengajaran too short ({len(pengajaran)} chars, need >100)"}

    csrf = get_csrf(cookie)

    data = {
        "_csrf": csrf,
        "jenis_rekod": "book",
        "kategori": kategori,
        "jenis": jenis,
        "bahasa": bahasa,
        "tajuk": tajuk,
        "tahun": str(tahun),
        "penulis": penulis,
        "isbn": isbn,
        "mukasurat": str(mukasurat),
        "penerbit": penerbit,
        "pautan": pautan,
        "penilaian": str(penilaian),
        "rumusan": rumusan,
        "pengajaran": pengajaran,
    }

    files = None
    if cover_path:
        files = {"kulit": ("cover.jpg", open(cover_path, "rb"), "image/jpeg")}

    r = requests.post(
        f"{BASE}/reading-record/saverecord",
        data=data,
        files=files,
        headers={
            "Cookie": cookie,
            "X-CSRF-Token": csrf,
        },
        verify=False,
        timeout=30,
    )

    if r.text.strip() == "success":
        return {"success": True, "detail": f"OK — '{tajuk}' submitted"}
    else:
        return {"success": False, "detail": f"Server responded: {r.text[:300]}"}


def submit_to_both(
    cookie1: str,
    cookie2: str,
    **book_kwargs,
) -> dict:
    """Submit the same book to both accounts. Returns results per account."""
    r1 = submit_book(cookie=cookie1, **book_kwargs)
    r2 = submit_book(cookie=cookie2, **book_kwargs)
    return {"account1": r1, "account2": r2}


if __name__ == "__main__":
    # Quick test: just check CSRF extraction
    import sys
    if len(sys.argv) > 1:
        c = sys.argv[1]
        try:
            token = get_csrf(c)
            print(f"CSRF OK: {token[:20]}...")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python submit_book.py '<cookie_string>'")
