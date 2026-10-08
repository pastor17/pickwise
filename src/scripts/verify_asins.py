#!/usr/bin/env python3
"""
Verify Amazon products: title, USD price, rating, review count, image.

Why this exists
---------------
Amazon serves different currency/offer data depending on the request's
geo vantage point, and the page contains MANY `priceAmount` fields (list
price, variant price, per-unit price, cross-sell items). Naively grabbing
the first `priceAmount` produces wrong numbers — we saw a $59.98 fan
report as $9490.46.

The reliable signals are the rendered price spans:
    <span class="a-offscreen">$59.98</span>
and for ratings:
    <span class="a-icon-alt">4.5 out of 5 stars</span>

Usage:
  python3 verify_asins.py B09MKPDJRT B0C2C9NHZW ...
  python3 verify_asins.py --file asins.txt --sleep 20
"""
import argparse
import html
import re
import subprocess
import sys
import time

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

HEADERS = [
    "-H", f"User-Agent: {UA}",
    "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "-H", "Accept-Language: en-US,en;q=0.9",
    # force US locale + USD regardless of egress IP
    "-H", "Cookie: i18n-prefs=USD; lc-main=en_US",
]


def fetch(asin: str) -> str:
    r = subprocess.run(
        ["curl", "-s", f"https://www.amazon.com/dp/{asin}", *HEADERS],
        capture_output=True, text=True, timeout=60,
    )
    return r.stdout


def parse(src: str) -> dict:
    def first(pat, group=1, flags=0):
        m = re.search(pat, src, flags)
        return m.group(group).strip() if m else ""

    title = first(r'id="productTitle"[^>]*>([^<]+)')
    if not title:
        title = first(r'<span id="title"[^>]*>([^<]+)')

    # Rendered price — prefer the main buybox price (a-offscreen with $)
    prices = re.findall(r'class="a-offscreen">\$([\d,]+\.\d{2})</span>', src)
    price = prices[0] if prices else ""

    rating = first(r'([\d.]+) out of 5 stars')
    reviews = first(r'id="acrCustomerReviewText"[^>]*>([\d,]+)')
    img = first(r'data-old-hires="([^"]+)"') or first(r'"hiRes":"([^"]+)"')

    blocked = ("api-services-support@amazon.com" in src
               or "Enter the characters you see below" in src
               or len(src) < 200_000)

    return {
        "asin": "",
        "title": html.unescape(title),
        "price": price,
        "rating": rating,
        "reviews": reviews,
        "image": img,
        "blocked": blocked,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("asins", nargs="*")
    ap.add_argument("--file")
    ap.add_argument("--sleep", type=float, default=20.0)
    args = ap.parse_args()

    asins = list(args.asins)
    if args.file:
        asins += [l.strip() for l in open(args.file) if l.strip()]

    print(f"{'ASIN':<12} {'PRICE':>9} {'★':>4} {'RATINGS':>9}  TITLE", flush=True)
    print("-" * 108, flush=True)

    for i, asin in enumerate(asins):
        d = parse(fetch(asin))
        if d["blocked"]:
            print(f"{asin:<12} {'':>9} {'':>4} {'':>9}  ⚠ BLOCKED/THROTTLED — pause 60s",
                  flush=True)
            time.sleep(60)
            d = parse(fetch(asin))
        flag = "⚠ " if d["blocked"] else "  "
        print(f"{asin:<12} {('$' + d['price']) if d['price'] else '-':>9} "
              f"{d['rating'] or '-':>4} {d['reviews'] or '-':>9}  {flag}{d['title'][:70]}",
              flush=True)
        # keep the image URL for later download
        if d["image"]:
            with open("/tmp/asins/images.tsv", "a") as fh:
                fh.write(f"{asin}\t{d['image']}\n")
        if i < len(asins) - 1:
            time.sleep(args.sleep)


if __name__ == "__main__":
    main()
