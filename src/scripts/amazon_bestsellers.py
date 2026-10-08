#!/usr/bin/env python3
"""
Fetch an Amazon Best Sellers page and print the ranked products.

Why: Amazon's /s?k= search endpoint is bot-blocked, but the public
Best Sellers (/gp/bestsellers/... or /zgbs/...) pages are fetchable.
They are the best available proxy for what overseas buyers ACTUALLY
buy — far better than guessing which models to review.

Usage:
  python3 src/scripts/amazon_bestsellers.py <url> [--brands Levoit,Dreo,Govee]
  python3 src/scripts/amazon_bestsellers.py --category air-purifiers

Notes:
  * Rate-limited after a few rapid requests — the script sleeps between
    categories. If a response comes back suspiciously small, it was
    throttled; wait 30-60s and retry.
  * Prices are often absent from best-seller cards (Amazon omits them in
    some renders) — use /dp/<ASIN> for a reliable price.
"""
import argparse
import html
import re
import subprocess
import sys
import time

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

CATEGORIES = {
    # Heating, Cooling & Air Quality  (home-garden/3206324011)
    "air-purifiers": "https://www.amazon.com/Best-Sellers-Home-Kitchen-Home-Air-Purifiers/zgbs/home-garden/267554011/",
    "dehumidifiers": "https://www.amazon.com/Best-Sellers-Home-Kitchen-Dehumidifiers/zgbs/home-garden/267557011/",
    "humidifiers": "https://www.amazon.com/Best-Sellers-Home-Kitchen-Humidifiers/zgbs/home-garden/17685839011/",
    "household-fans": "https://www.amazon.com/Best-Sellers-Home-Kitchen-Household-Fans/zgbs/home-garden/3737601/",
    "space-heaters": "https://www.amazon.com/Best-Sellers-Home-Kitchen-Indoor-Space-Heaters/zgbs/home-garden/510182/",
    # Floor care
    "robot-vacuums": "https://www.amazon.com/Best-Sellers-Home-Kitchen-Vacuums-Floor-Care/zgbs/home-garden/3743561/",
}


def fetch(url: str) -> str:
    out = subprocess.run(
        ["curl", "-s", url,
         "-H", f"User-Agent: {UA}",
         "-H", "Accept: text/html,application/xhtml+xml",
         "-H", "Accept-Language: en-US,en;q=0.9"],
        capture_output=True, text=True, timeout=60,
    )
    return out.stdout


def parse(src: str):
    """Split the page into per-product cards keyed by data-asin."""
    rows, seen = [], set()
    for chunk in re.split(r'(?=data-asin="[A-Z0-9]{10}")', src):
        m = re.match(r'data-asin="([A-Z0-9]{10})"', chunk)
        if not m:
            continue
        asin = m.group(1)
        if asin in seen:
            continue

        t = (re.search(r'class="_cDEzb_p13n-sc-css-line-clamp[^"]*"[^>]*>(.*?)</div>', chunk, re.S)
             or re.search(r'class="p13n-sc-truncate[^"]*"[^>]*>(.*?)</div>', chunk, re.S))
        title = html.unescape(re.sub(r"<[^>]+>", "", t.group(1))).strip() if t else ""

        p = re.search(r'class="_cDEzb_p13n-sc-price_[^"]*"[^>]*>\$([\d,]+\.\d{2})', chunk)
        r = re.search(r"([\d.]+) out of 5 stars", chunk)
        rc = re.search(r'class="a-size-small"[^>]*>([\d,]+)</span>', chunk)

        if title:
            seen.add(asin)
            rows.append({
                "rank": len(rows) + 1,
                "asin": asin,
                "title": title,
                "price": p.group(1) if p else "",
                "rating": r.group(1) if r else "",
                "reviews": rc.group(1) if rc else "",
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?")
    ap.add_argument("--category", choices=sorted(CATEGORIES))
    ap.add_argument("--brands", help="comma-separated substrings to highlight")
    ap.add_argument("--top", type=int, default=30)
    args = ap.parse_args()

    url = CATEGORIES[args.category] if args.category else args.url
    if not url:
        ap.error("pass a URL or --category")

    src = fetch(url)
    if len(src) < 50_000:
        print(f"⚠ Response only {len(src)} bytes — likely throttled. "
              f"Wait 30-60s and retry.", file=sys.stderr)

    rows = parse(src)
    wanted = [b.strip().lower() for b in args.brands.split(",")] if args.brands else []

    print(f"\n{args.category or url}\n")
    print(f"{'#':>3} {'ASIN':<12} {'PRICE':>8} {'★':>4} {'REVIEWS':>9}  TITLE")
    print("-" * 118)
    for r in rows[: args.top]:
        mark = "★CN " if wanted and any(b in r["title"].lower() for b in wanted) else "    "
        price = f"${r['price']}" if r["price"] else "-"
        print(f"{mark}{r['rank']:>3} {r['asin']:<12} {price:>8} "
              f"{r['rating'] or '-':>4} {r['reviews'] or '-':>9}  {r['title'][:86]}")
    return rows


if __name__ == "__main__":
    main()
