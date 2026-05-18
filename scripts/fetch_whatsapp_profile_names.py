#!/usr/bin/env python3
"""
fetch_whatsapp_profile_names.py
===============================

Query WhatsApp Cloud for contact profile names for a list of phone numbers.
The results are saved to a CSV that can be opened in Excel.

Usage examples:
    python scripts/fetch_whatsapp_profile_names.py \
        --input scripts/waitlist_recipients.csv \
        --output scripts/waitlist_profiles.csv

    python scripts/fetch_whatsapp_profile_names.py \
        --input scripts/waitlist_recipients.csv \
        --output scripts/waitlist_profiles.csv \
        --batch-size 10

    python scripts/fetch_whatsapp_profile_names.py \
        --input scripts/waitlist_recipients.csv \
        --output scripts/waitlist_profiles.csv \
        --dry-run

Environment variables:
    WHATSAPP_ACCESS_TOKEN          (required)
    WHATSAPP_PHONE_NUMBER_ID       (required)
    WHATSAPP_API_VERSION           (optional, default v18.0)
    WAITLIST_DEFAULT_COUNTRY_CODE  (optional, default 60)
    WAITLIST_SEND_DELAY            (optional, default 1.5 seconds)
"""
from __future__ import annotations

import argparse
import csv
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("fetch-whatsapp-profiles")

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v18.0")
DEFAULT_COUNTRY_CODE = os.getenv("WAITLIST_DEFAULT_COUNTRY_CODE", "60")
DEFAULT_SEND_DELAY = float(os.getenv("WAITLIST_SEND_DELAY", "1.5"))

SCRIPT_DIR = Path(__file__).resolve().parent


def normalise_phone(raw: str, default_cc: str = DEFAULT_COUNTRY_CODE) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"[^0-9]", "", str(raw))
    if not digits:
        return None
    if digits.startswith("0"):
        digits = default_cc + digits[1:]
    if len(digits) < 7 or len(digits) > 15:
        return None
    return digits


def load_input_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "phone" not in [c.lower() for c in reader.fieldnames]:
            raise ValueError("Input CSV must have at least a 'phone' column")
        for raw in reader:
            rows.append({k.strip(): (v or "").strip() for k, v in raw.items() if k is not None})
    return rows


def batch_iter(items: list[Any], size: int) -> list[list[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def fetch_contacts(phones: list[str]) -> dict[str, dict[str, str]]:
    url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/contacts"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "blocking": "wait",
        "contacts": phones,
    }
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    try:
        result = response.json()
    except ValueError:
        raise RuntimeError(f"Invalid JSON response from WhatsApp: {response.text}")
    if response.status_code != 200:
        raise RuntimeError(f"WhatsApp contacts API returned {response.status_code}: {result}")

    out: dict[str, dict[str, str]] = {}
    for item in result.get("contacts", []):
        input_number = item.get("input") or ""
        wa_id = item.get("wa_id") or ""
        profile_name = item.get("profile", {}).get("name", "")
        out[input_number] = {
            "wa_id": wa_id,
            "profile_name": profile_name,
            "status": "ok",
            "error": "",
        }
    for err in result.get("errors", []):
        contact_input = err.get("input") or ""
        out.setdefault(contact_input, {
            "wa_id": "",
            "profile_name": "",
            "status": "error",
            "error": err.get("message", "unknown error"),
        })
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch WhatsApp profile names for phone numbers.")
    parser.add_argument("--input", type=Path, required=True, help="CSV input file containing a phone column")
    parser.add_argument("--output", type=Path, required=False, help="Output CSV file path")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of numbers to query per request")
    parser.add_argument("--delay", type=float, default=DEFAULT_SEND_DELAY, help="Delay between batch requests")
    parser.add_argument("--country-code", default=DEFAULT_COUNTRY_CODE, help="Country code for local numbers starting with 0")
    parser.add_argument("--dry-run", action="store_true", help="Do not call the API; only print what would happen")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        log.error("WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID must be set in env.")
        return 2

    rows = load_input_csv(args.input)
    prepared: list[dict[str, str]] = []
    for row in rows:
        phone = row.get("phone", "")
        normalised = normalise_phone(phone, default_cc=args.country_code)
        if not normalised:
            log.warning("Skipping invalid phone: %s", phone)
            continue
        row["normalised"] = normalised
        prepared.append(row)

    if not prepared:
        log.error("No valid phone numbers found in the input CSV.")
        return 1

    output_path = args.output or (SCRIPT_DIR / f"waitlist_profiles_{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.csv")
    fieldnames = list({*sum(([k for k in row.keys()] for row in prepared), [])})
    if "name" not in fieldnames:
        fieldnames.append("name")
    if "normalised" not in fieldnames:
        fieldnames.append("normalised")
    if "profile_name" not in fieldnames:
        fieldnames.append("profile_name")
    if "status" not in fieldnames:
        fieldnames.append("status")
    if "error" not in fieldnames:
        fieldnames.append("error")

    log.info("Loaded %d rows; batch size %d", len(prepared), args.batch_size)

    results: list[dict[str, str]] = []
    for batch_number, batch in enumerate(batch_iter(prepared, args.batch_size), start=1):
        batch_phones = [row["normalised"] for row in batch]
        log.info("Querying batch %d/%d: %s", batch_number, (len(prepared) + args.batch_size - 1) // args.batch_size, ", ".join(batch_phones))
        if args.dry_run:
            for row in batch:
                row["profile_name"] = ""
                row["status"] = "dry_run"
                row["error"] = ""
                results.append(row)
            continue

        try:
            contact_map = fetch_contacts(batch_phones)
        except Exception as exc:
            log.error("Batch %d failed: %s", batch_number, exc)
            for row in batch:
                row["profile_name"] = ""
                row["status"] = "error"
                row["error"] = str(exc)
                results.append(row)
            time.sleep(args.delay)
            continue

        for row in batch:
            norm = row["normalised"]
            contact_info = contact_map.get(norm) or contact_map.get(row.get("phone", "")) or {}
            row["profile_name"] = contact_info.get("profile_name", "")
            row["status"] = contact_info.get("status", "missing")
            row["error"] = contact_info.get("error", "")
            if not row.get("name") and row["profile_name"]:
                row["name"] = row["profile_name"]
            results.append(row)

        if batch_number * args.batch_size < len(prepared):
            time.sleep(args.delay)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    log.info("Wrote %d rows to %s", len(results), output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
