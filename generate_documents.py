#!/usr/bin/env python3
"""Flexible document generator for creating various document types from CSV data.

Supports:
    * Table tents - folded cards for table placement
    * Custom templates - upload PDF or image templates and populate with data

Requirements:
    pip install reportlab pillow pypdf2
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
from typing import Iterable, Optional, Sequence, Dict, Any, List
import io

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image

try:
    from PyPDF2 import PdfReader, PdfWriter
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False


# Standard page size
PAGE_WIDTH = 8.5 * inch
PAGE_HEIGHT = 11 * inch
PAGE_SIZE = (PAGE_WIDTH, PAGE_HEIGHT)

# Table tent dimensions (standard: 4" x 6" when folded, printed 2 per page)
TABLE_TENT_WIDTH = 4 * inch
TABLE_TENT_HEIGHT = 6 * inch
TABLE_TENTS_PER_PAGE = 2
TABLE_TENT_MARGIN = 0.5 * inch
TABLE_TENT_GAP = 0.25 * inch

# Table tent layout constants
TABLE_TENT_NAME_FONT = "Helvetica-Bold"
TABLE_TENT_NAME_SIZE = 32
TABLE_TENT_ORG_FONT = "Helvetica"
TABLE_TENT_ORG_SIZE = 18
TABLE_TENT_TITLE_FONT = "Helvetica"
TABLE_TENT_TITLE_SIZE = 14
TABLE_TENT_IMAGE_SIZE = 1.5 * inch
TABLE_TENT_PADDING = 0.3 * inch


@dataclass
class DocumentRecord:
    """Generic data record for document generation."""
    data: Dict[str, Any]
    image_path: Optional[Path] = None
    
    def get(self, key: str, default: str = "") -> str:
        """Get a field value, with fallback."""
        return str(self.data.get(key, default)).strip()
    
    @property
    def full_name(self) -> str:
        """Get full name from first and last name fields."""
        first = self.get("First Name", self.get("first_name", ""))
        last = self.get("Last Name", self.get("last_name", ""))
        return " ".join(filter(None, [first, last]))


class DocumentType(str, Enum):
    """Supported document types."""
    TABLE_TENT = "table_tent"
    CUSTOM_TEMPLATE = "custom_template"


def load_records_from_csv(
    csv_path: Path,
    image_dir: Optional[Path] = None,
    column_mapping: Optional[Dict[str, str]] = None,
) -> List[DocumentRecord]:
    """Load records from CSV file.
    
    Args:
        csv_path: Path to CSV file
        image_dir: Optional directory containing images to match
        column_mapping: Optional mapping of CSV columns to standard names
    
    Returns:
        List of DocumentRecord objects
    """
    records: List[DocumentRecord] = []
    
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Apply column mapping if provided
            if column_mapping:
                mapped_row = {}
                for csv_col, standard_col in column_mapping.items():
                    if csv_col in row:
                        mapped_row[standard_col] = row[csv_col]
                # Keep unmapped columns
                for key, value in row.items():
                    if key not in column_mapping:
                        mapped_row[key] = value
                row = mapped_row
            
            # Try to find matching image
            image_path = None
            if image_dir and image_dir.exists():
                first = row.get("First Name", row.get("first_name", "")).strip()
                last = row.get("Last Name", row.get("last_name", "")).strip()
                if first and last:
                    prefix = f"{first}_{last}".replace(" ", "_")
                    # Look for image with this prefix
                    for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
                        img_path = image_dir / f"{prefix}{ext}"
                        if img_path.exists():
                            image_path = img_path
                            break
                        # Also try case-insensitive
                        for existing_img in image_dir.glob(f"{prefix}*"):
                            if existing_img.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
                                image_path = existing_img
                                break
                        if image_path:
                            break
            
            record = DocumentRecord(data=row, image_path=image_path)
            records.append(record)
    
    return records


def generate_table_tents(
    records: Sequence[DocumentRecord],
    output_path: Path,
    *,
    include_images: bool = True,
    font_name: str = TABLE_TENT_NAME_FONT,
    font_size: int = TABLE_TENT_NAME_SIZE,
) -> None:
    """Generate table tent PDF from records.
    
    Table tents are printed 2 per page, designed to be folded in half.
    Each tent shows name, organization, title, and optionally an image.
    
    Args:
        records: List of DocumentRecord objects
        output_path: Path to save output PDF
        include_images: Whether to include images if available
        font_name: Font name for the main name text
        font_size: Font size for the main name text
    """
    pdf = canvas.Canvas(str(output_path), pagesize=PAGE_SIZE)
    
    # Calculate positions for two tents per page
    available_width = PAGE_WIDTH - 2 * TABLE_TENT_MARGIN
    available_height = PAGE_HEIGHT - 2 * TABLE_TENT_MARGIN - TABLE_TENT_GAP
    
    # Each tent gets half the available width
    tent_width = (available_width - TABLE_TENT_GAP) / 2
    tent_height = available_height
    
    # Position for left tent
    left_x = TABLE_TENT_MARGIN
    # Position for right tent
    right_x = TABLE_TENT_MARGIN + tent_width + TABLE_TENT_GAP
    
    y_start = PAGE_HEIGHT - TABLE_TENT_MARGIN
    
    records_list = list(records)
    for page_idx in range(0, len(records_list), TABLE_TENTS_PER_PAGE):
        page_records = records_list[page_idx:page_idx + TABLE_TENTS_PER_PAGE]
        
        for tent_idx, record in enumerate(page_records):
            x = left_x if tent_idx == 0 else right_x
            
            # Draw tent border (optional, for visual reference)
            pdf.setStrokeColor(colors.Color(0.9, 0.9, 0.9))
            pdf.setLineWidth(0.5)
            pdf.rect(x, y_start - tent_height, tent_width, tent_height, stroke=1, fill=0)
            
            # Draw content
            _draw_table_tent_content(
                pdf, record, x, y_start - tent_height, tent_width, tent_height,
                include_images=include_images,
                font_name=font_name,
                font_size=font_size,
            )
        
        pdf.showPage()
    
    pdf.save()


def _draw_table_tent_content(
    pdf: canvas.Canvas,
    record: DocumentRecord,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    include_images: bool = True,
    font_name: str = TABLE_TENT_NAME_FONT,
    font_size: int = TABLE_TENT_NAME_SIZE,
) -> None:
    """Draw content for a single table tent."""
    pdf.saveState()
    
    # Content area (with padding)
    content_x = x + TABLE_TENT_PADDING
    content_y = y + height - TABLE_TENT_PADDING
    content_width = width - 2 * TABLE_TENT_PADDING
    content_height = height - 2 * TABLE_TENT_PADDING
    
    current_y = content_y
    
    # Draw image if available and requested
    if include_images and record.image_path and record.image_path.exists():
        try:
            image_reader = ImageReader(str(record.image_path))
            img_width, img_height = image_reader.getSize()
            
            # Scale image to fit
            max_image_height = content_height * 0.4  # Use 40% of height for image
            scale = min(TABLE_TENT_IMAGE_SIZE / img_width, max_image_height / img_height)
            display_width = img_width * scale
            display_height = img_height * scale
            
            # Center image horizontally
            image_x = content_x + (content_width - display_width) / 2
            image_y = current_y - display_height
            
            pdf.drawImage(
                image_reader,
                image_x,
                image_y,
                width=display_width,
                height=display_height,
                preserveAspectRatio=True,
                mask="auto",
            )
            
            current_y = image_y - TABLE_TENT_PADDING
        except Exception as e:
            print(f"Warning: Could not load image {record.image_path}: {e}", file=sys.stderr)
    
    # Draw name (centered, large)
    name = record.full_name
    if name:
        pdf.setFont(font_name, font_size)
        name_lines = simpleSplit(name, font_name, font_size, content_width)
        
        # Calculate total name height
        name_height = len(name_lines) * (font_size * 1.2)
        name_start_y = current_y - name_height / 2
        
        for line in name_lines:
            pdf.drawCentredString(
                content_x + content_width / 2,
                name_start_y,
                line,
            )
            name_start_y -= font_size * 1.2
        
        current_y = name_start_y - TABLE_TENT_PADDING
    
    # Draw organization (centered, medium)
    org = record.get("Organization", record.get("organization", ""))
    if org:
        pdf.setFont(TABLE_TENT_ORG_FONT, TABLE_TENT_ORG_SIZE)
        org_lines = simpleSplit(org, TABLE_TENT_ORG_FONT, TABLE_TENT_ORG_SIZE, content_width)
        
        for line in org_lines:
            pdf.drawCentredString(
                content_x + content_width / 2,
                current_y,
                line,
            )
            current_y -= TABLE_TENT_ORG_SIZE * 1.3
    
    # Draw title (centered, smaller)
    title = record.get("Job Title", record.get("Title", record.get("title", "")))
    if title:
        pdf.setFont(TABLE_TENT_TITLE_FONT, TABLE_TENT_TITLE_SIZE)
        title_lines = simpleSplit(title, TABLE_TENT_TITLE_FONT, TABLE_TENT_TITLE_SIZE, content_width)
        
        for line in title_lines:
            pdf.drawCentredString(
                content_x + content_width / 2,
                current_y,
                line,
            )
            current_y -= TABLE_TENT_TITLE_SIZE * 1.2
    
    pdf.restoreState()


def generate_from_template(
    records: Sequence[DocumentRecord],
    template_path: Path,
    output_path: Path,
    *,
    field_mapping: Optional[Dict[str, str]] = None,
) -> None:
    """Generate documents from a template PDF or image.
    
    This is a placeholder for template-based generation. For full template support,
    you would need to:
    1. Parse the template to find placeholder fields
    2. Replace placeholders with data from records
    3. Merge into final PDF
    
    For now, this creates a simple overlay approach.
    
    Args:
        records: List of DocumentRecord objects
        template_path: Path to template PDF or image
        output_path: Path to save output PDF
        field_mapping: Optional mapping of template field names to record fields
    """
    # For now, create a simple implementation
    # In a full implementation, you'd use PyPDF2 or similar to overlay text on templates
    
    if template_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
        # Image template - create PDF with image as background
        _generate_from_image_template(records, template_path, output_path, field_mapping)
    elif template_path.suffix.lower() == '.pdf' and HAS_PYPDF2:
        # PDF template - overlay text (simplified)
        _generate_from_pdf_template(records, template_path, output_path, field_mapping)
    else:
        raise ValueError(f"Unsupported template format: {template_path.suffix}")


def _generate_from_image_template(
    records: Sequence[DocumentRecord],
    template_path: Path,
    output_path: Path,
    field_mapping: Optional[Dict[str, str]] = None,
) -> None:
    """Generate documents from an image template."""
    # Load template image
    template_img = Image.open(template_path)
    img_width, img_height = template_img.size
    
    # Convert pixels to points (assuming 72 DPI, standard for PDFs)
    # If image is high resolution, scale appropriately
    page_width = img_width * (72.0 / 72.0)  # Adjust if needed for different DPI
    page_height = img_height * (72.0 / 72.0)
    
    # Create PDF with template as background
    pdf = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))
    
    for record in records:
        # Draw template image
        pdf.drawImage(
            str(template_path),
            0, 0,
            width=page_width,
            height=page_height,
            preserveAspectRatio=True,
        )
        
        # Overlay text fields (simplified - would need template parsing for full support)
        # For now, just add name in center
        name = record.full_name
        if name:
            pdf.setFont("Helvetica-Bold", 24)
            pdf.drawCentredString(page_width / 2, page_height / 2, name)
        
        pdf.showPage()
    
    pdf.save()


def _generate_from_pdf_template(
    records: Sequence[DocumentRecord],
    template_path: Path,
    output_path: Path,
    field_mapping: Optional[Dict[str, str]] = None,
) -> None:
    """Generate documents from a PDF template."""
    if not HAS_PYPDF2:
        raise ImportError("PyPDF2 is required for PDF template support. Install with: pip install pypdf2")
    
    # This is a simplified implementation
    # Full implementation would parse template for form fields or text placeholders
    
    reader = PdfReader(str(template_path))
    writer = PdfWriter()
    
    # For each record, create a page
    for record in records:
        # Get first page of template (or create new page)
        if len(reader.pages) > 0:
            page = reader.pages[0]
            writer.add_page(page)
        else:
            # Create blank page if template is empty
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            temp_buffer = io.BytesIO()
            temp_canvas = canvas.Canvas(temp_buffer, pagesize=letter)
            temp_canvas.showPage()
            temp_canvas.save()
            temp_buffer.seek(0)
            # Would need to convert to PyPDF2 page here
    
    # Save output
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
    
    # Note: This is a placeholder. Full implementation would overlay text on template pages


def main():
    """Command-line interface for document generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate documents from CSV data")
    parser.add_argument("csv_path", type=Path, help="Path to CSV file")
    parser.add_argument("output_path", type=Path, help="Output PDF path")
    parser.add_argument(
        "--document-type",
        type=DocumentType,
        choices=list(DocumentType),
        default=DocumentType.TABLE_TENT,
        help="Type of document to generate",
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=None,
        help="Directory containing images to match with records",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=None,
        help="Template file (PDF or image) for custom template generation",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Don't include images in output",
    )
    
    args = parser.parse_args()
    
    # Load records
    records = load_records_from_csv(args.csv_path, args.image_dir)
    
    if not records:
        print("No records found in CSV", file=sys.stderr)
        return 1
    
    # Generate documents
    if args.document_type == DocumentType.TABLE_TENT:
        generate_table_tents(records, args.output_path, include_images=not args.no_images)
    elif args.document_type == DocumentType.CUSTOM_TEMPLATE:
        if not args.template:
            print("Template file required for custom template generation", file=sys.stderr)
            return 1
        generate_from_template(records, args.template, args.output_path)
    
    print(f"Generated {len(records)} documents: {args.output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

