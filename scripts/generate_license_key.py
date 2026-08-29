#!/usr/bin/env python3
"""
Generate an encrypted CDE license file outside the Flask app.

Example:
    python scripts/generate_license_key.py \
        --secret "$CDE_LICENSE_SECRET" \
        --output /etc/cde/license.key \
        --module MOV008 --module PRC010 --module ENV006
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services import licenseManager


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a CDE license key file.")
    parser.add_argument("--secret", required=True, help="License encryption secret.")
    parser.add_argument(
        "--output",
        required=True,
        help="Destination license file path.",
    )
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        help="Allowed module code. Repeat for multiple modules.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    modules = sorted({module.strip().upper() for module in args.module if module.strip()})
    output_path = Path(args.output)
    payload = {"modules": modules}
    token = licenseManager.encrypt_license_payload(payload, args.secret)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(token + "\n", encoding="utf-8")
    print(f"License written to {output_path} with {len(modules)} module(s).")


if __name__ == "__main__":
    main()
