#!/usr/bin/env python3
"""
PickWise — fetch official, watermark-free product images from Amazon.

Uses the Amazon Product Advertising API 5.0 (GetItems), which Amazon
Associates are explicitly allowed to use for product imagery. This is the
legitimate, watermark-free source for product photos — no scraping, no
watermark removal.

Setup (one-time):
  1. Create Amazon Associates + Product Advertising API credentials:
     https://webservices.amazon.com/paapi5/documentation/register-for-pa-api.html
  2. Export them (or put them in a .env you never commit):
        export AMAZON_ACCESS_KEY=AKIA...
        export AMAZON_SECRET_KEY=...
        export AMAZON_PARTNER_TAG=yourtag-20

Usage:
  python3 amazon_images.py --asins B07ZTXLKM7,B01728NLRG,B01D8DAYII \
      --marketplace www.amazon.com --out images.yaml

Output (images.yaml) maps each ASIN to its primary image URL + title, ready
to paste into a Hugo content file's `cover:` or a roundup pick's `image:`.
"""

import argparse
import datetime
import hashlib
import hmac
import json
import os
import sys
import urllib.parse
import urllib.request

REGION = "us-east-1"
SERVICE = "ProductAdvertisingAPI"
HOST = "webservices.amazon.com"
ENDPOINT = f"https://{HOST}/paapi5/getitems"


def _sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _signing_key(secret, date_stamp, region, service):
    k_date = _sign(("AWS4" + secret).encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    return _sign(k_service, "aws4_request")


def _auth_headers(access_key, secret_key, payload):
    now = datetime.datetime.utcnow()
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    body = json.dumps(payload)
    body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

    canonical_uri = "/paapi5/getitems"
    canonical_querystring = ""
    canonical_headers = (
        f"content-encoding:amz-1.0\n"
        f"host:{HOST}\n"
        f"x-amz-date:{amz_date}\n"
        f"x-amz-target:com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems\n"
    )
    signed_headers = "content-encoding;host;x-amz-date;x-amz-target"

    canonical_request = "\n".join(
        [
            "POST",
            canonical_uri,
            canonical_querystring,
            canonical_headers,
            signed_headers,
            body_hash,
        ]
    )

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{REGION}/{SERVICE}/aws4_request"
    string_to_sign = "\n".join(
        [
            algorithm,
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )

    signing_key = _signing_key(secret_key, date_stamp, REGION, SERVICE)
    signature = hmac.new(
        signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    authorization = (
        f"{algorithm} Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    return {
        "Content-Encoding": "amz-1.0",
        "Host": HOST,
        "X-Amz-Date": amz_date,
        "X-Amz-Target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems",
        "Authorization": authorization,
    }, body


def get_items(access_key, secret_key, partner_tag, marketplace, asins):
    payload = {
        "Operation": "GetItems",
        "ItemIds": asins,
        "Resources": [
            "Images.Primary.Large",
            "Images.Primary.Medium",
            "ItemInfo.Title.DisplayValue",
        ],
        "PartnerTag": partner_tag,
        "PartnerType": "Associates",
        "Marketplace": marketplace,
    }
    headers, body = _auth_headers(access_key, secret_key, payload)
    req = urllib.request.Request(ENDPOINT, data=body.encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    ap = argparse.ArgumentParser(description="Fetch Amazon product images via PA-API 5.0")
    ap.add_argument("--asins", required=True, help="Comma-separated ASINs, e.g. B07XX,B08YY")
    ap.add_argument("--marketplace", default="www.amazon.com", help="Marketplace, e.g. www.amazon.com")
    ap.add_argument("--out", default="images.yaml", help="Output YAML file")
    args = ap.parse_args()

    access_key = os.environ.get("AMAZON_ACCESS_KEY")
    secret_key = os.environ.get("AMAZON_SECRET_KEY")
    partner_tag = os.environ.get("AMAZON_PARTNER_TAG")

    if not (access_key and secret_key and partner_tag):
        print("ERROR: set AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, and AMAZON_PARTNER_TAG.", file=sys.stderr)
        sys.exit(1)

    asins = [a.strip() for a in args.asins.split(",") if a.strip()]
    data = get_items(access_key, secret_key, partner_tag, args.marketplace, asins)

    lines = ["# Product images fetched via PA-API (official, watermark-free)"]
    errors = data.get("Errors") or []
    if errors:
        for e in errors:
            lines.append(f"# error: {e.get('Code')} - {e.get('Message')}")

    for item in (data.get("ItemsResult", {}).get("Items") or []):
        asin = item.get("ASIN")
        title = item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue", "Unknown")
        images = item.get("Images", {}).get("Primary", {})
        img = images.get("Large", {}).get("URL") or images.get("Medium", {}).get("URL") or ""
        lines.append(f"{asin}:")
        lines.append(f"  title: {json.dumps(title)}")
        lines.append(f"  image: {json.dumps(img)}")

    with open(args.out, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote {args.out} ({len(data.get('ItemsResult', {}).get('Items') or [])} items)")


if __name__ == "__main__":
    main()
