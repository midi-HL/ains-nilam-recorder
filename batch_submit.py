#!/usr/bin/env python3
"""
Batch submit books to both AINS accounts with 3-minute cooldown.

Usage:
    1. Put your books in the BOOKS list below
    2. Make sure cookies.json exists
    3. Run: python batch_submit.py
"""

import json
import time
from submit_book import submit_book

# ─── Load cookies ───
with open("cookies.json") as f:
    accs = json.load(f)

COOKIE1 = accs["account1"]["cookie"]
COOKIE2 = accs["account2"]["cookie"]

# ─── Book list ───
# Fill in your books here. rumusan and pengajaran must be >100 chars each.
BOOKS = [
    {
        "tajuk": "Example Book Title",
        "tahun": 2020,
        "penulis": "Author Name",
        "mukasurat": 300,
        "penerbit": "Publisher Name",
        "kategori": "fiction",
        "bahasa": "my",  # or "en"
        "penilaian": 4,
        "rumusan": "Tulis ringkasan buku di sini. Pastikan lebih daripada 100 aksara. Contoh: Novel ini mengisahkan perjalanan seorang watak yang menghadapi pelbagai cabaran dalam hidup. Beliau perlu membuat pilihan yang sukar antara cinta dan kerjaya, antara keluarga dan impian. Sepanjang cerita, kita dapat melihat perkembangan watak dari seorang yang naif kepada seorang yang matang dan berwibawa.",
        "pengajaran": "Tulis pengajaran daripada buku di sini. Pastikan lebih daripada 100 aksara. Contoh: Buku ini mengajar saya tentang pentingnya ketabahan dan keyakinan diri. Kita belajar bahawa setiap cabaran ada hikmahnya, dan kejayaan tidak datang tanpa pengorbanan. Novel ini juga mengingatkan kita untuk menghargai orang di sekeliling dan tidak mudah menyerah kalah apabila menghadapi kegagalan.",
    },
    # Add more books here...
]

# ─── Run batch ───
if __name__ == "__main__":
    total = len(BOOKS)
    print(f"Starting batch: {total} books, both accounts")
    print("=" * 50)

    for i, book in enumerate(BOOKS):
        print(f"\nBook {i+1}/{total}: {book['tajuk']}")

        r1 = submit_book(cookie=COOKIE1, **book)
        r2 = submit_book(cookie=COOKIE2, **book)

        print(f"  Account 1: {'OK' if r1['success'] else 'FAIL'} — {r1['detail']}")
        print(f"  Account 2: {'OK' if r2['success'] else 'FAIL'} — {r2['detail']}")

        if i < total - 1:
            print("  Waiting 3 minutes...")
            time.sleep(180)

    print("\n=== BATCH COMPLETE ===")
