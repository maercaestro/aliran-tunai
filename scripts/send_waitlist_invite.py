#!/usr/bin/env python3
"""
send_waitlist_invite.py
=======================

Send an approved WhatsApp Cloud API template message to a list of waiting-list
recipients (the "First Users" of FLOW).

Why a template?
    Recipients have not messaged your business in the last 24h, so Meta will
    reject any free-form text. Only pre-approved templates are allowed for
    business-initiated conversations.

Usage examples
--------------
    # 1. Dry run — show what would be sent, don't call the API
    python scripts/send_waitlist_invite.py \
        --template flow_early_access_welcome --lang ms \
        --recipients scripts/waitlist_recipients.csv --dry-run

    # 2. Send to YOUR number only (smoke test before the real blast)
    python scripts/send_waitlist_invite.py \
        --template flow_early_access_welcome --lang en \
        --test 0176757773 --name Abu

    # 3. Real send to a CSV of recipients
    python scripts/send_waitlist_invite.py \
        --template flow_early_access_welcome --lang en \
        --recipients scripts/waitlist_recipients.csv

Important notes
---------------
    - This script sends the first body parameter as the {{1}} template variable.
    - Use --name for your test run, and include a name column for real sends.

CSV format
----------
    phone,name
    0176757773,Abu
    0136179379,Ahmad
    0143015897,Siti

Environment
-----------
    WHATSAPP_ACCESS_TOKEN          (required)
    WHATSAPP_PHONE_NUMBER_ID       (required)
    WHATSAPP_API_VERSION           (optional, default v18.0)
    WAITLIST_DEFAULT_COUNTRY_CODE  (optional, default 60 for Malaysia)
    WAITLIST_SEND_DELAY            (optional, default 1.5 seconds)

Results
-------
    A timestamped CSV is written next to this script:
        scripts/waitlist_invite_results_YYYYMMDD-HHMMSS.csv
    Columns: phone, normalised, name, status, http_status, message_id, error

    Re-running with `--retry-failed <path-to-results.csv>` re-sends only the
    rows whose status != 'sent'.
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
from typing import Iterable

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("waitlist-invite")

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v18.0")
DEFAULT_COUNTRY_CODE = os.getenv("WAITLIST_DEFAULT_COUNTRY_CODE", "60")
SEND_DELAY = float(os.getenv("WAITLIST_SEND_DELAY", "1.5"))

SCRIPT_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Phone normalisation
# ---------------------------------------------------------------------------
def normalise_phone(raw: str, default_cc: str = DEFAULT_COUNTRY_CODE) -> str | None:
    """Normalise a Malaysian-style phone number to WhatsApp format (no '+').

    Examples (default_cc='60'):
        '0176757773'    -> '60176757773'
        '+60176757773'  -> '60176757773'
        '60176757773'   -> '60176757773'
        '017-675 7773'  -> '60176757773'
        ''              -> None
    """
    if not raw:
        return None
    digits = re.sub(r"[^0-9]", "", str(raw))
    if not digits:
        return None
    # Strip leading 0 for local numbers, then prepend country code.
    if digits.startswith("0"):
        digits = default_cc + digits[1:]
    # Already has country code → leave as is.
    if len(digits) < 7 or len(digits) > 15:
        return None
    return digits


# ---------------------------------------------------------------------------
# WhatsApp Cloud API
# ---------------------------------------------------------------------------
def send_template(
    to_number: str,
    template_name: str,
    language_code: str,
    body_params: list[str] | None = None,
    timeout: int = 20,
) -> tuple[bool, int, dict]:
    """Send a template message. Returns (ok, http_status, response_json)."""
    url = (
        f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"
        f"/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    components: list[dict] = []
    if body_params:
        components.append({
            "type": "body",
            "parameters": [{"type": "text", "text": p} for p in body_params],
        })
    payload: dict = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
        },
    }
    if components:
        payload["template"]["components"] = components

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        try:
            data = r.json()
        except ValueError:
            data = {"raw": r.text}
        return r.ok, r.status_code, data
    except requests.RequestException as e:
        return False, 0, {"error": {"message": str(e)}}


# ---------------------------------------------------------------------------
# Recipients I/O
# ---------------------------------------------------------------------------
def load_recipients(csv_path: Path) -> list[dict]:
    """Load a recipients CSV. Required column: 'phone'. Optional: 'name'."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Recipients CSV not found: {csv_path}")
    recipients: list[dict] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "phone" not in [c.lower() for c in reader.fieldnames]:
            raise ValueError("CSV must have at least a 'phone' column")
        for row in reader:
            phone = (row.get("phone") or row.get("Phone") or "").strip()
            name = (row.get("name") or row.get("Name") or "").strip()
            if not phone:
                continue
            recipients.append({"phone": phone, "name": name})
    return recipients


def load_failed_from_results(results_csv: Path) -> list[dict]:
    """Re-build recipient list from a previous results CSV, only non-sent rows."""
    if not results_csv.exists():
        raise FileNotFoundError(f"Results CSV not found: {results_csv}")
    out: list[dict] = []
    with results_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("status") != "sent":
                out.append({"phone": row.get("phone", ""), "name": row.get("name", "")})
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Send approved WhatsApp template to waitlist.")
    p.add_argument("--template", required=True, help="Approved template name, e.g. flow_early_access_welcome")
    p.add_argument("--lang", required=True, help="Template language code, e.g. ms or en")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--recipients", type=Path, help="Path to CSV with phone[,name] columns")
    src.add_argument("--test", help="Single test phone number (e.g. 0176757773)")
    src.add_argument("--retry-failed", type=Path, help="Path to a previous results CSV — resend failed rows only")
    p.add_argument("--name", help="Used with --test: value for the {{1}} body variable")
    p.add_argument(
        "--no-name-var",
        action="store_true",
        help="Set if your template body has ZERO variables.",
    )
    p.add_argument("--dry-run", action="store_true", help="Don't call the API, just print")
    p.add_argument("--delay", type=float, default=SEND_DELAY,
                   help=f"Seconds between sends (default {SEND_DELAY}). Be polite to Meta's rate limits.")
    p.add_argument("--country-code", default=DEFAULT_COUNTRY_CODE,
                   help=f"Country code for local numbers starting with 0 (default {DEFAULT_COUNTRY_CODE})")
    p.add_argument("-y", "--yes", action="store_true", help="Skip the 'are you sure' prompt")
    return p.parse_args()


def confirm(prompt: str) -> bool:
    try:
        ans = input(f"{prompt} [y/N]: ").strip().lower()
    except EOFError:
        return False
    return ans in {"y", "yes"}


def main() -> int:
    args = parse_args()

    if not args.dry_run:
        if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
            log.error("WHATSAPP_ACCESS_TOKEN / WHATSAPP_PHONE_NUMBER_ID not set in env.")
            return 2

    # Build recipients list
    if args.test:
        recipients = [{"phone": args.test, "name": args.name or "First User"}]
    elif args.retry_failed:
        recipients = load_failed_from_results(args.retry_failed)
    else:
        recipients = load_recipients(args.recipients)

    if not recipients:
        log.warning("No recipients to send to. Exiting.")
        return 0

    # Normalise + dedupe
    seen: set[str] = set()
    prepared: list[dict] = []
    skipped: list[dict] = []
    for r in recipients:
        norm = normalise_phone(r["phone"], default_cc=args.country_code)
        if not norm:
            skipped.append({**r, "reason": "invalid phone"})
            continue
        if norm in seen:
            skipped.append({**r, "reason": "duplicate"})
            continue
        seen.add(norm)
        prepared.append({**r, "normalised": norm})

    log.info(
        "Prepared %d recipient(s); skipped %d (dupes/invalid). Template=%s lang=%s%s",
        len(prepared), len(skipped), args.template, args.lang,
        " [DRY RUN]" if args.dry_run else "",
    )
    for s in skipped:
        log.warning("  skip  %-15s name=%r reason=%s", s.get("phone"), s.get("name"), s.get("reason"))

    if not prepared:
        return 0

    # Preview the first 3
    log.info("Preview (first 3):")
    for r in prepared[:3]:
        log.info("  → %s  (name=%r)", r["normalised"], r["name"] or "—")

    if not args.dry_run and not args.yes:
        if not confirm(f"Send to {len(prepared)} number(s)?"):
            log.info("Aborted by user.")
            return 1

    # Open results CSV
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    results_path = SCRIPT_DIR / f"waitlist_invite_results_{ts}.csv"
    fieldnames = ["phone", "normalised", "name", "status", "http_status", "message_id", "error"]
    results_file = None
    writer = None
    if not args.dry_run:
        results_file = results_path.open("w", newline="", encoding="utf-8")
        writer = csv.DictWriter(results_file, fieldnames=fieldnames)
        writer.writeheader()

    sent = 0
    failed = 0
    try:
        for i, r in enumerate(prepared, 1):
            body_params: list[str] | None = None
            if not args.no_name_var:
                # Default: first template body parameter is the recipient's name.
                # This is used for templates with a {{name}} placeholder.
                body_params = [r["name"] or "First User"]

            log.info("[%d/%d] → %s  name=%r", i, len(prepared), r["normalised"], r["name"] or "—")

            if args.dry_run:
                continue

            ok, http_status, data = send_template(
                to_number=r["normalised"],
                template_name=args.template,
                language_code=args.lang,
                body_params=body_params,
            )
            row = {
                "phone": r["phone"],
                "normalised": r["normalised"],
                "name": r["name"],
                "http_status": http_status,
                "message_id": "",
                "error": "",
                "status": "sent" if ok else "failed",
            }
            if ok:
                msgs = data.get("messages") or []
                row["message_id"] = msgs[0].get("id", "") if msgs else ""
                sent += 1
                log.info("    ✓ sent  msg_id=%s", row["message_id"])
            else:
                err = (data.get("error") or {})
                row["error"] = (
                    f"{err.get('code', '')}:{err.get('message', '')} "
                    f"sub={err.get('error_subcode', '')} "
                    f"details={err.get('error_data', {}).get('details', '')}"
                ).strip()
                failed += 1
                log.error("    ✗ failed (HTTP %s): %s", http_status, row["error"])

            writer.writerow(row)
            results_file.flush()

            # Be nice to Meta's rate limits.
            if i < len(prepared):
                time.sleep(args.delay)

    finally:
        if results_file:
            results_file.close()

    if args.dry_run:
        log.info("DRY RUN done. No messages sent.")
    else:
        log.info("Done. sent=%d failed=%d total=%d", sent, failed, sent + failed)
        log.info("Results: %s", results_path)
        if failed:
            log.info("Retry failed only with:")
            log.info("  python %s --template %s --lang %s --retry-failed %s",
                     Path(__file__).name, args.template, args.lang, results_path)
    return 0 if failed == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
