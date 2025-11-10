#!/usr/bin/env python3
"""Create printable PDFs from attendee CSV/headshots.

Each card:
    * Front – full name, organization, and job title in large text.
    * Back – attendee headshot centered on the card.

Additional layouts:
    * Facebook proof – five attendees per letter page, headshot left, details right.

Requirements:
    pip install reportlab
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
from typing import Iterable, Optional, Sequence

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas

try:
    from pyairtable import Api
except ImportError:
    Api = None


CARD_WIDTH = 5 * inch
CARD_HEIGHT = 3 * inch
SCALE_FACTOR = 0.8
PAGE_WIDTH = 8.5 * inch
PAGE_HEIGHT = 11 * inch
PAGE_SIZE = (PAGE_WIDTH, PAGE_HEIGHT)
CARDS_PER_PAGE = 3
FACEBOOKS_PER_PAGE = 5
TOP_MARGIN = 0.5 * inch
BOTTOM_MARGIN = 0.5 * inch
SIDE_MARGIN = (PAGE_WIDTH - CARD_WIDTH) / 2
CUT_LINE_COLOR = colors.Color(0.25, 0.25, 0.25)
SAFE_AREA_COLOR = colors.Color(0.6, 0.6, 0.6)
CROSSHAIR_COLOR = colors.Color(0.5, 0.5, 0.5)

FACEBOOK_LEFT_MARGIN = 0.6 * inch
FACEBOOK_RIGHT_MARGIN = 0.6 * inch
FACEBOOK_TOP_MARGIN = 0.75 * inch
FACEBOOK_BOTTOM_MARGIN = 0.5 * inch
FACEBOOK_IMAGE_WIDTH = 1.9 * inch
FACEBOOK_IMAGE_PADDING = 0.12 * inch
FACEBOOK_LINE_COLOR = colors.Color(0.85, 0.85, 0.85)
FACEBOOK_NAME_FONT = "Helvetica-Bold"
FACEBOOK_BODY_FONT = "Helvetica"
FACEBOOK_NAME_FONT_SIZE = 18
FACEBOOK_BODY_FONT_SIZE = 12
FACEBOOK_TEXT_COLUMN_GAP = 0.3 * inch
FACEBOOK_NAME_TO_BODY_GAP = 0.2 * inch
FACEBOOK_BODY_LINE_SPACING = 0.22 * inch
FACEBOOK_BODY_SECTION_GAP = 0.22 * inch
FACEBOOK_ASCENT_RATIO = 0.72
FACEBOOK_DESCENT_RATIO = 0.2

# Default excluded organizations
DEFAULT_EXCLUDED_ORGANIZATIONS = {
    "foundation for american innovation",
}


class DuplexMode(str, Enum):
    SHORT_EDGE = "short-edge"
    LONG_EDGE = "long-edge"


@dataclass
class Attendee:
    first_name: str
    last_name: str
    organization: str
    title: str
    image_path: Path

    @property
    def full_name(self) -> str:
        return " ".join(filter(None, [self.first_name, self.last_name]))


def chunked(sequence: Sequence[Attendee], size: int) -> Iterable[list[Attendee]]:
    for index in range(0, len(sequence), size):
        yield list(sequence[index : index + size])


def apply_card_transform(pdf: canvas.Canvas, origin_x: float, origin_y: float, *, rotate: bool = False) -> None:
    pdf.translate(origin_x, origin_y)
    pdf.translate(CARD_WIDTH / 2, CARD_HEIGHT / 2)
    if rotate:
        pdf.rotate(180)
    if SCALE_FACTOR != 1.0:
        pdf.scale(SCALE_FACTOR, SCALE_FACTOR)
    pdf.translate(-CARD_WIDTH / 2, -CARD_HEIGHT / 2)


def card_positions(count: int) -> list[tuple[float, float]]:
    if count <= 0:
        return []

    available_height = PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN - (CARD_HEIGHT * count)
    if count > 1:
        gap = max(0.0, available_height / (count - 1))
    else:
        gap = 0.0

    positions: list[tuple[float, float]] = []
    current_y = PAGE_HEIGHT - TOP_MARGIN - CARD_HEIGHT

    for _ in range(count):
        positions.append((SIDE_MARGIN, current_y))
        current_y -= CARD_HEIGHT + gap

    return positions


def sanitize_token(token: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in token).strip("_")


def build_expected_prefix(first_name: str, last_name: str) -> str:
    parts = [sanitize_token(part) for part in (first_name, last_name) if part]
    return "_".join(parts)


def load_attendees(
    csv_path: Path,
    headshot_dir: Path,
) -> list[Attendee]:
    attendees: list[Attendee] = []
    missing_images: list[str] = []

    with csv_path.open(newline="", encoding="utf-8-sig") as file_handle:
        reader = csv.DictReader(file_handle)

        for row in reader:
            first = (row.get("First Name") or "").strip()
            last = (row.get("Last Name") or "").strip()
            organization = (row.get("Organization") or "").strip()
            title = (row.get("Job Title") or "").strip()

            prefix = build_expected_prefix(first, last)
            if not prefix:
                continue

            image = find_headshot(headshot_dir, prefix)

            if image is None:
                missing_images.append(prefix)
                continue

            attendees.append(
                Attendee(
                    first_name=first,
                    last_name=last,
                    organization=organization,
                    title=title,
                    image_path=image,
                )
            )

    if missing_images:
        print(
            "Skipping attendees without headshots in directory:",
            ", ".join(sorted(set(missing_images))),
            file=sys.stderr,
        )

    return attendees


def parse_airtable_url(url: str) -> Optional[tuple[str, str]]:
    """Parse Airtable URL to extract base ID and table name/ID.
    
    Supports formats like:
    - https://airtable.com/appXXXXX/tableYYYYY/...
    - https://airtable.com/appXXXXX/tblYYYYY/...
    
    Returns:
        Tuple of (base_id, table_id) or None if parsing fails
    """
    # Match patterns like /appXXXXXXXXXXXXXX/tableYYYYYYYYYYYYYY or /appXXXXXXXXXXXXXX/tblYYYYYYYYYYYYYY
    patterns = [
        r'/app([a-zA-Z0-9]+)/(?:table|tbl)([a-zA-Z0-9]+)',
        r'airtable\.com/app([a-zA-Z0-9]+)/(?:table|tbl)([a-zA-Z0-9]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return (match.group(1), match.group(2))
    
    return None


def load_attendees_from_airtable(
    airtable_url: str,
    airtable_api_key: str,
    headshot_dir: Path,
    *,
    field_mapping: Optional[dict[str, str]] = None,
) -> list[Attendee]:
    """Load attendees from Airtable.
    
    Args:
        airtable_url: Full Airtable URL or share link
        airtable_api_key: Airtable API key
        headshot_dir: Directory containing headshot images
        field_mapping: Optional mapping of Airtable field names to expected names.
                     Defaults to common variations.
    
    Returns:
        List of Attendee objects
    """
    if Api is None:
        raise ImportError("pyairtable is required for Airtable import. Install with: pip install pyairtable")
    
    # Default field mapping (case-insensitive matching)
    default_mapping = {
        "first_name": ["First Name", "First", "First Name", "firstName", "first_name"],
        "last_name": ["Last Name", "Last", "LastName", "lastName", "last_name"],
        "organization": ["Organization", "Org", "Company", "organization", "company"],
        "title": ["Job Title", "Title", "Position", "jobTitle", "job_title", "title"],
    }
    
    if field_mapping:
        default_mapping.update(field_mapping)
    
    # Parse URL
    parsed = parse_airtable_url(airtable_url)
    if not parsed:
        raise ValueError(f"Could not parse Airtable URL: {airtable_url}")
    
    base_id, table_id = parsed
    
    # Initialize API
    api = Api(airtable_api_key)
    table = api.table(base_id, table_id)
    
    # Fetch all records
    records = table.all()
    
    attendees: list[Attendee] = []
    missing_images: list[str] = []
    
    for record in records:
        fields = record.get("fields", {})
        
        # Find field names (case-insensitive)
        def find_field(possible_names: list[str]) -> str:
            for name in possible_names:
                for field_name in fields.keys():
                    if field_name.lower() == name.lower():
                        return str(fields[field_name] or "")
            return ""
        
        first = find_field(default_mapping["first_name"]).strip()
        last = find_field(default_mapping["last_name"]).strip()
        organization = find_field(default_mapping["organization"]).strip()
        title = find_field(default_mapping["title"]).strip()
        
        prefix = build_expected_prefix(first, last)
        if not prefix:
            continue
        
        image = find_headshot(headshot_dir, prefix)
        
        if image is None:
            missing_images.append(prefix)
            continue
        
        attendees.append(
            Attendee(
                first_name=first,
                last_name=last,
                organization=organization,
                title=title,
                image_path=image,
            )
        )
    
    if missing_images:
        print(
            "Skipping attendees without headshots in directory:",
            ", ".join(sorted(set(missing_images))),
            file=sys.stderr,
        )
    
    return attendees


def find_headshot(directory: Path, prefix: str) -> Optional[Path]:
    if not directory.exists():
        return None

    matches = sorted(directory.glob(f"{prefix}*"))
    for path in matches:
        if path.is_file():
            return path
    return None


def filter_attendees(
    attendees: Sequence[Attendee],
    excluded_organizations: Optional[set[str]] = None,
) -> list[Attendee]:
    """Filter out attendees from excluded organizations.
    
    Args:
        attendees: List of attendees to filter
        excluded_organizations: Set of organization names to exclude (case-insensitive).
                              If None, uses DEFAULT_EXCLUDED_ORGANIZATIONS.
    
    Returns:
        Filtered list of attendees
    """
    if excluded_organizations is None:
        excluded_organizations = DEFAULT_EXCLUDED_ORGANIZATIONS
    
    if not excluded_organizations:
        return list(attendees)
    
    excluded_lower = {org.lower() for org in excluded_organizations}
    filtered = [
        attendee
        for attendee in attendees
        if (attendee.organization or "").strip().lower() not in excluded_lower
    ]
    return filtered


def draw_fronts(attendees: Sequence[Attendee], output_path: Path) -> None:
    pdf = canvas.Canvas(str(output_path), pagesize=PAGE_SIZE)

    for chunk in chunked(attendees, CARDS_PER_PAGE):
        _draw_front_page(pdf, chunk)
        pdf.showPage()

    pdf.save()


def _draw_front_card(pdf: canvas.Canvas, attendee: Attendee, origin_x: float = 0.0, origin_y: float = 0.0) -> None:
    pdf.saveState()
    apply_card_transform(pdf, origin_x, origin_y)

    pdf.setFont("Helvetica-Bold", 30)
    name_y = CARD_HEIGHT - 0.9 * inch
    pdf.drawCentredString(CARD_WIDTH / 2, name_y, attendee.full_name)

    pdf.setFont("Helvetica", 18)
    org_lines = simpleSplit(attendee.organization or "", "Helvetica", 18, CARD_WIDTH - inch)
    title_lines = simpleSplit(attendee.title or "", "Helvetica", 16, CARD_WIDTH - inch)

    y = name_y - 1.2 * inch

    for line in org_lines:
        pdf.drawCentredString(CARD_WIDTH / 2, y, line)
        y -= 0.45 * inch

    pdf.setFont("Helvetica", 16)
    for line in title_lines:
        pdf.drawCentredString(CARD_WIDTH / 2, y, line)
        y -= 0.4 * inch

    pdf.restoreState()


def draw_backs(
    attendees: Sequence[Attendee], output_path: Path, *, duplex_mode: DuplexMode
) -> None:
    pdf = canvas.Canvas(str(output_path), pagesize=PAGE_SIZE)

    for chunk in chunked(attendees, CARDS_PER_PAGE):
        _draw_back_page(pdf, chunk, duplex_mode=duplex_mode)
        pdf.showPage()

    pdf.save()


def _draw_back_card(
    pdf: canvas.Canvas,
    attendee: Attendee,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
    *,
    rotate: bool,
) -> None:
    pdf.saveState()
    apply_card_transform(pdf, origin_x, origin_y, rotate=rotate)

    image_reader = ImageReader(str(attendee.image_path))
    img_width, img_height = image_reader.getSize()

    scale = min(CARD_WIDTH / img_width, CARD_HEIGHT / img_height)
    width = img_width * scale
    height = img_height * scale
    x = (CARD_WIDTH - width) / 2
    y = (CARD_HEIGHT - height) / 2

    pdf.drawImage(image_reader, x, y, width=width, height=height, preserveAspectRatio=True, mask="auto")
    pdf.restoreState()


def _draw_front_page(pdf: canvas.Canvas, chunk: Sequence[Attendee]) -> None:
    for attendee, (x, y) in zip(chunk, card_positions(len(chunk))):
        _draw_front_card(pdf, attendee, x, y)


def _draw_back_page(
    pdf: canvas.Canvas,
    chunk: Sequence[Attendee],
    *,
    duplex_mode: DuplexMode,
) -> None:
    positions = card_positions(len(chunk))
    if duplex_mode is DuplexMode.LONG_EDGE:
        attendee_iter: Iterable[Attendee] = chunk
        position_iter: Iterable[tuple[float, float]] = reversed(positions)
    else:
        attendee_iter = reversed(chunk)
        position_iter = positions

    rotate = True

    for attendee, (x, y) in zip(attendee_iter, position_iter):
        _draw_back_card(pdf, attendee, x, y, rotate=rotate)


def draw_guides(
    attendees: Sequence[Attendee], output_path: Path, *, duplex_mode: DuplexMode
) -> None:
    pdf = canvas.Canvas(str(output_path), pagesize=PAGE_SIZE)

    for page_number, chunk in enumerate(chunked(attendees, CARDS_PER_PAGE), start=1):
        _draw_guide_page(pdf, chunk, title=f"Front cut guide – page {page_number}")
        pdf.showPage()
        _draw_guide_page(
            pdf,
            chunk,
            title=(
                f"Back cut guide – page {page_number}"
                f" (align for {duplex_mode.value} duplex printing)"
            ),
        )
        pdf.showPage()

    pdf.save()


def _draw_guide_page(pdf: canvas.Canvas, chunk: Sequence[Attendee], title: str) -> None:
    pdf.setFont("Helvetica", 10)
    pdf.drawString(SIDE_MARGIN, PAGE_HEIGHT - 0.3 * inch, title)
    safe_margin_x = (CARD_WIDTH - (CARD_WIDTH * SCALE_FACTOR)) / 2
    safe_margin_y = (CARD_HEIGHT - (CARD_HEIGHT * SCALE_FACTOR)) / 2

    positions = card_positions(len(chunk))
    for x, y in positions:
        pdf.saveState()
        pdf.setLineWidth(1)
        pdf.setDash(4, 4)
        pdf.setStrokeColor(CUT_LINE_COLOR)
        pdf.rect(x, y, CARD_WIDTH, CARD_HEIGHT, stroke=1, fill=0)

        pdf.setDash(2, 3)
        pdf.setLineWidth(0.5)
        pdf.setStrokeColor(SAFE_AREA_COLOR)
        pdf.rect(
            x + safe_margin_x,
            y + safe_margin_y,
            CARD_WIDTH * SCALE_FACTOR,
            CARD_HEIGHT * SCALE_FACTOR,
            stroke=1,
            fill=0,
        )

        # Add small crosshair marks at card centers for alignment reference
        center_x = x + CARD_WIDTH / 2
        center_y = y + CARD_HEIGHT / 2
        cross_half = 0.2 * inch

        pdf.setDash(1, 2)
        pdf.setLineWidth(0.3)
        pdf.setStrokeColor(CROSSHAIR_COLOR)
        pdf.line(center_x - cross_half, center_y, center_x + cross_half, center_y)
        pdf.line(center_x, center_y - cross_half, center_x, center_y + cross_half)

        pdf.restoreState()

    footer_text = "Solid outline = 3x5 cut line. Dashed outline = safe area for text/images (80%)."
    pdf.setDash()
    pdf.setStrokeColor(colors.black)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(SIDE_MARGIN, 0.35 * inch, footer_text)


def draw_combined(
    attendees: Sequence[Attendee],
    output_path: Path,
    *,
    duplex_mode: DuplexMode,
) -> None:
    pdf = canvas.Canvas(str(output_path), pagesize=PAGE_SIZE)

    for chunk in chunked(attendees, CARDS_PER_PAGE):
        _draw_front_page(pdf, chunk)
        pdf.showPage()
        _draw_back_page(pdf, chunk, duplex_mode=duplex_mode)
        pdf.showPage()

    pdf.save()


def draw_facebooks(attendees: Sequence[Attendee], output_path: Path) -> None:
    pdf = canvas.Canvas(str(output_path), pagesize=PAGE_SIZE)

    for chunk in chunked(attendees, FACEBOOKS_PER_PAGE):
        _draw_facebook_page(pdf, chunk)
        pdf.showPage()

    pdf.save()


def _draw_facebook_page(pdf: canvas.Canvas, chunk: Sequence[Attendee]) -> None:
    entry_height = (
        PAGE_HEIGHT - FACEBOOK_TOP_MARGIN - FACEBOOK_BOTTOM_MARGIN
    ) / FACEBOOKS_PER_PAGE
    y_cursor = PAGE_HEIGHT - FACEBOOK_TOP_MARGIN

    for index, attendee in enumerate(chunk):
        top = y_cursor
        bottom = top - entry_height
        _draw_facebook_entry(pdf, attendee, top, bottom)

        if index < len(chunk) - 1:
            pdf.saveState()
            pdf.setStrokeColor(FACEBOOK_LINE_COLOR)
            pdf.setLineWidth(0.75)
            pdf.line(
                FACEBOOK_LEFT_MARGIN,
                bottom,
                PAGE_WIDTH - FACEBOOK_RIGHT_MARGIN,
                bottom,
            )
            pdf.restoreState()

        y_cursor -= entry_height


def _draw_facebook_entry(pdf: canvas.Canvas, attendee: Attendee, top: float, bottom: float) -> None:
    entry_height = top - bottom
    image_max_height = entry_height - 2 * FACEBOOK_IMAGE_PADDING
    image_x = FACEBOOK_LEFT_MARGIN
    image_y = bottom + FACEBOOK_IMAGE_PADDING

    pdf.saveState()
    image_reader = ImageReader(str(attendee.image_path))
    img_width, img_height = image_reader.getSize()
    scale = min(FACEBOOK_IMAGE_WIDTH / img_width, image_max_height / img_height)
    display_width = img_width * scale
    display_height = img_height * scale
    image_offset_x = (FACEBOOK_IMAGE_WIDTH - display_width) / 2
    image_offset_y = (image_max_height - display_height) / 2
    pdf.drawImage(
        image_reader,
        image_x + image_offset_x,
        image_y + image_offset_y,
        width=display_width,
        height=display_height,
        preserveAspectRatio=True,
        mask="auto",
    )
    pdf.restoreState()

    text_x = FACEBOOK_LEFT_MARGIN + FACEBOOK_IMAGE_WIDTH + FACEBOOK_TEXT_COLUMN_GAP
    text_width = PAGE_WIDTH - FACEBOOK_RIGHT_MARGIN - text_x
    image_center_y = image_y + display_height / 2

    org_lines = simpleSplit(
        attendee.organization or "",
        FACEBOOK_BODY_FONT,
        FACEBOOK_BODY_FONT_SIZE,
        text_width,
    )
    title_lines = simpleSplit(
        attendee.title or "",
        FACEBOOK_BODY_FONT,
        FACEBOOK_BODY_FONT_SIZE,
        text_width,
    )

    line_specs: list[tuple[str, float, float]] = []
    current_offset = 0.0
    line_specs.append((attendee.full_name, FACEBOOK_NAME_FONT_SIZE, current_offset))

    if org_lines:
        current_offset -= FACEBOOK_NAME_TO_BODY_GAP
        for index, line in enumerate(org_lines):
            line_specs.append((line, FACEBOOK_BODY_FONT_SIZE, current_offset))
            if index < len(org_lines) - 1:
                current_offset -= FACEBOOK_BODY_LINE_SPACING

    if org_lines and title_lines:
        current_offset -= FACEBOOK_BODY_SECTION_GAP

    if title_lines:
        for index, line in enumerate(title_lines):
            line_specs.append((line, FACEBOOK_BODY_FONT_SIZE, current_offset))
            if index < len(title_lines) - 1:
                current_offset -= FACEBOOK_BODY_LINE_SPACING

    ascent_adjustments = [
        offset + font_size * FACEBOOK_ASCENT_RATIO for _, font_size, offset in line_specs
    ]
    descent_adjustments = [
        offset - font_size * FACEBOOK_DESCENT_RATIO for _, font_size, offset in line_specs
    ]

    text_top = max(ascent_adjustments)
    text_bottom = min(descent_adjustments)
    text_center_offset = (text_top + text_bottom) / 2
    start_y = image_center_y - text_center_offset

    pdf.saveState()
    for index, (text, font_size, offset) in enumerate(line_specs):
        font_name = FACEBOOK_NAME_FONT if index == 0 else FACEBOOK_BODY_FONT
        pdf.setFont(font_name, font_size)
        pdf.drawString(text_x, start_y + offset, text)
    pdf.restoreState()


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path, help="Path to attendee CSV file")
    parser.add_argument(
        "headshot_dir",
        type=Path,
        help="Directory containing downloaded headshot images",
    )
    parser.add_argument(
        "--front-output",
        type=Path,
        default=None,
        help="Optional output PDF path for card fronts (omit to skip)",
    )
    parser.add_argument(
        "--back-output",
        type=Path,
        default=None,
        help="Optional output PDF path for card backs (omit to skip)",
    )
    parser.add_argument(
        "--combined-output",
        type=Path,
        default=Path.cwd() / "flashcards_duplex.pdf",
        help="Output PDF path with front/back interleaved pages (default: ./flashcards_duplex.pdf)",
    )
    parser.add_argument(
        "--guides-output",
        type=Path,
        default=None,
        help="Optional output PDF path for cut guides (omit to skip)",
    )
    parser.add_argument(
        "--facebook-output",
        type=Path,
        default=None,
        help=(
            "Optional output PDF path for facebook proof (five attendees per page, headshot left)"
        ),
    )
    parser.add_argument(
        "--duplex-mode",
        type=DuplexMode,
        choices=list(DuplexMode),
        default=DuplexMode.LONG_EDGE,
        help=(
            "Select how backs should be arranged for duplex printing:"
            " 'long-edge' matches printers that rotate the back side 180°"
            " (default), 'short-edge' keeps the same top-to-bottom order."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on the number of attendees/cards to generate",
    )
    parser.add_argument(
        "--exclude-fai",
        action="store_true",
        help="Exclude attendees from Foundation for American Innovation",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    csv_path = args.csv_path.expanduser().resolve()
    headshot_dir = args.headshot_dir.expanduser().resolve()
    front_pdf = args.front_output.expanduser().resolve() if args.front_output else None
    back_pdf = args.back_output.expanduser().resolve() if args.back_output else None
    combined_pdf = args.combined_output.expanduser().resolve() if args.combined_output else None
    guides_pdf = args.guides_output.expanduser().resolve() if args.guides_output else None
    facebook_pdf = args.facebook_output.expanduser().resolve() if args.facebook_output else None

    if not csv_path.exists():
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        return 1

    if not headshot_dir.exists():
        print(f"Headshot directory not found: {headshot_dir}", file=sys.stderr)
        return 1

    attendees = load_attendees(csv_path, headshot_dir)

    if args.exclude_fai:
        excluded_orgs = DEFAULT_EXCLUDED_ORGANIZATIONS
        excluded_count = len(attendees)
        attendees = filter_attendees(attendees, excluded_orgs)
        excluded_count -= len(attendees)
        if excluded_count > 0:
            print(
                f"Excluded {excluded_count} attendee(s) from organizations: "
                f"{', '.join(sorted(excluded_orgs))}",
                file=sys.stderr,
            )

    if args.limit is not None:
        attendees = attendees[: args.limit]

    if not attendees:
        print("No attendees with headshots found.", file=sys.stderr)
        return 1

    if front_pdf:
        draw_fronts(attendees, front_pdf)
        print(f"Created {front_pdf}")

    if back_pdf:
        draw_backs(attendees, back_pdf, duplex_mode=args.duplex_mode)
        print(f"Created {back_pdf}")

    if combined_pdf:
        draw_combined(attendees, combined_pdf, duplex_mode=args.duplex_mode)
        print(f"Created {combined_pdf}")

    if facebook_pdf:
        draw_facebooks(attendees, facebook_pdf)
        print(f"Created {facebook_pdf}")

    if guides_pdf:
        draw_guides(attendees, guides_pdf, duplex_mode=args.duplex_mode)
        print(f"Created {guides_pdf}")
    print(f"Total cards: {len(attendees)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

