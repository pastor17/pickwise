#!/usr/bin/env python3
"""
PickWise — quick demo image fetcher (NO API credentials required).

Downloads the official Amazon product image (watermark-free, Associates-safe)
for each product into assets/img/products/<slug>.jpg, and prints the product
title so you can verify each image matches the right product.

This page-scraping path is for LOCAL DEMO use only. For production, use the
official Product Advertising API instead — see amazon_images.py in this folder.

Usage:
  python3 fetch_product_images.py \
      "levoit-core-300s|Levoit Core 300S Smart True HEPA Air Purifier" \
      "coway-mighty|Coway Airmega Mighty AP-1512HH Air Purifier"
"""

import argparse
import os
import re
import sys
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "img", "products")


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml",
    })
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")


def search_asin(keyword):
    q = urllib.parse.quote(keyword)
    html = fetch(f"https://www.amazon.com/s?k={q}")
    m = re.search(r'data-asin="([A-Z0-9]{10})"', html)
    return m.group(1) if m else None


def product_info(asin):
    html = fetch(f"https://www.amazon.com/dp/{asin}")
    title = ""
    m = re.search(r'<span[^>]*id="productTitle"[^>]*>\s*(.*?)\s*</span>', html, re.S)
    if m:
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    img = None
    m = re.search(r'data-old-hires="([^"]+)"', html)
    if m:
        img = m.group(1)
    return title, img


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r, open(path, "wb") as f:
        f.write(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("items", nargs="+", help="Each as 'slug|Amazon search keyword'")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    for item in args.items:
        if "|" not in item:
            print(f"SKIP (bad format, want 'slug|keyword'): {item}")
            continue
        slug, keyword = [p.strip() for p in item.split("|", 1)]
        asin = search_asin(keyword)
        if not asin:
            print(f"FAIL  {slug}: no ASIN found")
            continue
        title, img = product_info(asin)
        if not img:
            print(f"FAIL  {slug} ({asin}): no image found")
            continue
        path = os.path.join(OUT_DIR, f"{slug}.jpg")
        download(img, path)
        size = os.path.getsize(path)
        print(f"OK    {slug}\n       ASIN={asin}\n       title={title[:80]}\n       image={img}\n       saved={path} ({size//1024} KB)\n")


if __name__ == "__main__":
    main()
