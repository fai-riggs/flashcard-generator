#!/usr/bin/env python3
"""Download attendee headshots from the provided CSV file.

The CSV is expected to contain the columns `First Name`, `Last Name`, and `Picture`.
The `Picture` column should either contain a URL directly or a value formatted as
"<original_filename> (<url>)" as exported from Airtable. Images are written to the
specified output directory using the participant's first and last names.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

try:
    import requests
except ImportError as exc:  # pragma: no cover - configuration guard
    raise SystemExit(
        "The 'requests' package is required. Install it with 'pip install requests'."
    ) from exc


DEFAULT_OUTPUT_DIR = Path.cwd() / "headshots"


def parse_picture_field(raw_value: str) -> tuple[Optional[str], Optional[str]]:
    """Return the original filename and URL extracted from a CSV picture cell."""

    if not raw_value:
        return None, None

    raw_value = raw_value.strip()

    # Pattern: "filename (url)"
    match = re.match(r"^(?P<name>[^()]+?)\s*\((?P<url>https?://[^)]+)\)$", raw_value)
    if match:
        filename = match.group("name").strip()
        url = match.group("url").strip()
        return filename or None, url or None

    # Otherwise assume the entire value is a URL
    if raw_value.startswith("http://") or raw_value.startswith("https://"):
        return None, raw_value

    return raw_value, None


def sanitize_name(name: str) -> str:
    """Create a filesystem-friendly token from a name component."""

    token = re.sub(r"[^A-Za-z0-9]+", "_", name.strip())
    return token.strip("_") or "unnamed"


def resolve_extension(original_filename: Optional[str], url: Optional[str]) -> str:
    """Decide on an image file extension, preferring the original filename."""

    for candidate in (original_filename, url):
        if not candidate:
            continue

        path = urlparse(candidate).path if candidate.startswith("http") else candidate
        suffix = Path(path).suffix.lower()
        if suffix:
            return suffix

    return ".jpg"


def build_output_path(
    output_dir: Path, first_name: str, last_name: str, extension: str
) -> Path:
    """Construct a unique output file path based on the attendee name."""

    base_name = "_".join(filter(None, (sanitize_name(first_name), sanitize_name(last_name))))
    if not base_name:
        base_name = "attendee"

    candidate = output_dir / f"{base_name}{extension}"
    counter = 1
    while candidate.exists():
        candidate = output_dir / f"{base_name}_{counter}{extension}"
        counter += 1
    return candidate


def download_image(url: str, destination: Path) -> None:
    """Fetch a binary resource at *url* and write it to *destination*."""

    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as file_handle:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file_handle.write(chunk)


def process_csv(csv_path: Path, output_dir: Path) -> None:
    with csv_path.open(newline="", encoding="utf-8-sig") as file_handle:
        reader = csv.DictReader(file_handle)

        missing_url_rows: list[tuple[int, str]] = []
        skipped_rows: list[tuple[int, str]] = []

        for row_number, row in enumerate(reader, start=2):  # account for header row
            first_name = (row.get("First Name") or "").strip()
            last_name = (row.get("Last Name") or "").strip()
            picture_field = (row.get("Picture") or "").strip()

            original_filename, url = parse_picture_field(picture_field)

            if not url:
                missing_url_rows.append((row_number, f"{first_name} {last_name}".strip()))
                continue

            extension = resolve_extension(original_filename, url)

            try:
                output_path = build_output_path(output_dir, first_name, last_name, extension)
            except Exception as exc:  # pragma: no cover - defensive guard
                skipped_rows.append((row_number, str(exc)))
                continue

            try:
                download_image(url, output_path)
            except Exception as exc:
                skipped_rows.append((row_number, f"{output_path.name}: {exc}"))

        if missing_url_rows:
            print("Rows missing a valid picture URL:")
            for line_no, name in missing_url_rows:
                print(f"  line {line_no}: {name or '(no name)'}")

        if skipped_rows:
            print("Rows skipped due to download or write errors:")
            for line_no, reason in skipped_rows:
                print(f"  line {line_no}: {reason}")


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv_path",
        type=Path,
        help="Absolute path to the attendee CSV file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where images will be saved (defaults to ./headshots)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    csv_path = args.csv_path.expanduser().resolve()
    output_dir = args.output.expanduser().resolve()

    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    process_csv(csv_path, output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

