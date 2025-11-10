#!/usr/bin/env python3
"""Generate a printable facebook proof PDF with five attendees per page.

This script reads the same attendee CSV and headshot directory used for the
flashcards workflow, but produces a single-sided layout: headshot on the left,
name and details on the right. Use this for quick print-and-review booklets.

Requirements:
    pip install reportlab
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from generate_flashcards import draw_facebooks, load_attendees


EXCLUDED_ORGANIZATIONS = {
    "foundation for american innovation",
}


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path, help="Path to attendee CSV file")
    parser.add_argument(
        "headshot_dir",
        type=Path,
        help="Directory containing downloaded headshot images",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.cwd() / "facebook_proof.pdf",
        help="Output PDF path (default: ./facebook_proof.pdf)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on the number of attendees to include",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    csv_path = args.csv_path.expanduser().resolve()
    headshot_dir = args.headshot_dir.expanduser().resolve()
    output_pdf = args.output.expanduser().resolve()

    if not csv_path.exists():
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        return 1

    if not headshot_dir.exists():
        print(f"Headshot directory not found: {headshot_dir}", file=sys.stderr)
        return 1

    attendees = load_attendees(csv_path, headshot_dir)

    if args.limit is not None:
        attendees = attendees[: args.limit]

    if not attendees:
        print("No attendees with headshots found.", file=sys.stderr)
        return 1

    filtered_attendees = [
        attendee
        for attendee in attendees
        if attendee.organization.strip().lower() not in EXCLUDED_ORGANIZATIONS
    ]

    excluded_count = len(attendees) - len(filtered_attendees)
    if excluded_count:
        print(
            f"Excluded {excluded_count} attendee(s) from organizations: "
            f"{', '.join(sorted(EXCLUDED_ORGANIZATIONS))}",
            file=sys.stderr,
        )

    if not filtered_attendees:
        print("No attendees remain after applying exclusions.", file=sys.stderr)
        return 1

    draw_facebooks(filtered_attendees, output_pdf)
    print(f"Created {output_pdf}")
    print(f"Total attendees in proof: {len(filtered_attendees)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

