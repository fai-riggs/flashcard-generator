# FAI Document Generator

A one-stop shop for FAI staff to easily generate professional documents. Create flashcards, table tents, custom templates, and more from CSV data with automated PDF generation.

## Features

- 📄 **CSV Upload**: Upload attendee data with flexible column mapping
- 🖼️ **Image Management**: Upload and manage headshot images from URLs or files
- 👥 **Smart Matching**: Automatically matches CSV names to image files
- 📑 **Multiple Document Types**: 
  - Flashcards (front/back with names and headshots)
  - Table tents (folded cards for table placement)
  - Custom templates (upload your own PDF/image templates)
  - Facebook proofs (attendee reference sheets)
- ⚙️ **Flexible Settings**: Configure duplex printing mode, font sizes, and more
- 🔄 **Reusable**: Easy to use for multiple events and document types
- 🌐 **Airtable Integration**: Import data directly from Airtable bases

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Web App (Recommended)

Run the Streamlit web interface:

```bash
streamlit run fai_document_generator.py
```

Or use the launcher script:

```bash
./run_app.sh
```

The app will open in your browser. Use the tabs to:
1. **Upload Data**: Upload CSV or connect to Airtable, and manage headshots
2. **Manage Images**: Upload and manage headshot images from URLs or files
3. **Review Attendees**: Check that names match images correctly
4. **Generate PDFs**: Create printable flashcards, facebooks, and more
5. **Document Generator**: Create table tents and custom template-based documents

### Command Line

For command-line usage with flashcards:

```bash
python3 generate_flashcards.py "attendees.csv" headshots/ --combined-output flashcards.pdf --duplex-mode short-edge
```

For other document types:

```bash
python3 generate_documents.py "attendees.csv" output.pdf --document-type table_tent --image-dir headshots/
```

## CSV Format

Your CSV file should have the following columns (or use column mapping in the app):
- `First Name` (required)
- `Last Name` (required)
- `Organization` (optional)
- `Job Title` (optional)

The app supports flexible column mapping, so your CSV can use any column names - just map them in the interface.

## Image Naming

Headshot images should be named using the format:
```
FirstName_LastName.ext
```

For example:
- `John_Doe.jpg`
- `Jane_Smith.png`
- `Bob_Johnson.webp`

The app will automatically match CSV entries to image files based on first and last names.

## Document Types

### Flashcards
- Size: 3" × 5" (standard flashcard size)
- Cards per page: 3
- Page size: 8.5" × 11" (US Letter)
- Options: Combined (front+back), fronts only, backs only, cut guides

### Table Tents
- Size: 4" × 6" when folded (2 per page)
- Designed to be folded in half and stand on tables
- Includes name, organization, title, and optional images
- Customizable font sizes

### Custom Templates
- Upload your own PDF or image templates
- System overlays CSV data onto templates
- Supports PDF, PNG, JPG, JPEG, and WebP formats
- Perfect for branded documents and special layouts

## Duplex Printing

The app supports two duplex printing modes:

- **Short Edge**: For printers that flip pages along the short edge (top-to-top)
- **Long Edge**: For printers that flip pages along the long edge (side-to-side)

Select the mode that matches your printer's duplex settings.

## Troubleshooting

### Images not matching
- Ensure image filenames match the format `FirstName_LastName.ext`
- Check that names in CSV match exactly (case-insensitive)
- Special characters in names are converted to underscores

### Missing images
- Attendees without matching images are skipped
- Check the "Review Attendees" tab to see which attendees have images
- Images are optional for most document types

### PDF generation errors
- Ensure all required columns are in your CSV
- Check that the headshots directory exists and contains images (if using images)
- Verify you have write permissions for the output directory

### Template issues
- For Google Drive templates: Download the file first, then upload it to the app
- Ensure templates are in supported formats (PDF, PNG, JPG, JPEG, WebP)
- Template overlay is simplified - complex templates may need manual adjustment

## Future Events

To use this for a new event:
1. Create a new CSV file with attendee data
2. Upload images matching the naming convention (or use existing headshots)
3. Select your document type and generate
4. Download and print your documents

The app is designed to be reusable for any event and document type!

## Web Deployment

To host this app online, see [DEPLOYMENT.md](DEPLOYMENT.md) for instructions on deploying to Streamlit Cloud (free hosting).

Once deployed, you'll get a URL like `https://your-app-name.streamlit.app` that you can share with your team.

## For FAI Staff

This tool is designed to streamline document creation for events. Simply:
1. Upload your CSV with attendee data
2. Optionally upload headshot images
3. Choose your document type (flashcards, table tents, or custom template)
4. Generate and download print-ready PDFs

No design skills required - the app handles all the formatting automatically!
