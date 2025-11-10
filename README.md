# Flashcard Generator

A user-friendly application for creating printable flashcards from attendee data with names, organizations, titles, and headshot images.

## Features

- 📄 **CSV Upload**: Upload attendee data with names, organizations, and job titles
- 🖼️ **Image Management**: Upload and manage headshot images
- 👥 **Smart Matching**: Automatically matches CSV names to image files
- 📑 **PDF Generation**: Creates printable flashcards with front (text) and back (image) sides
- ⚙️ **Flexible Settings**: Configure duplex printing mode for your printer
- 🔄 **Reusable**: Easy to use for multiple events

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Web App (Recommended)

Run the Streamlit web interface:

```bash
streamlit run flashcard_app.py
```

The app will open in your browser. Use the tabs to:
1. **Upload Data**: Upload CSV and set headshots directory
2. **Manage Images**: Upload and manage headshot images
3. **Review Attendees**: Check that names match images correctly
4. **Generate PDFs**: Create and download printable flashcards

### Command Line

For command-line usage, use the original script:

```bash
python3 generate_flashcards.py "attendees.csv" headshots/ --combined-output flashcards.pdf --duplex-mode short-edge
```

## CSV Format

Your CSV file should have the following columns:
- `First Name` (required)
- `Last Name` (required)
- `Organization` (optional)
- `Job Title` (optional)

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

## Duplex Printing

The app supports two duplex printing modes:

- **Short Edge**: For printers that flip pages along the short edge (top-to-top)
- **Long Edge**: For printers that flip pages along the long edge (side-to-side)

Select the mode that matches your printer's duplex settings.

## Output Files

The app can generate:
- **Combined PDF**: Front and back pages interleaved (ready for duplex printing)
- **Fronts Only**: Just the text sides
- **Backs Only**: Just the image sides
- **Cut Guides**: Printable guides showing where to cut the cards

## Card Specifications

- Size: 3" × 5" (standard flashcard size)
- Cards per page: 3
- Page size: 8.5" × 11" (US Letter)

## Troubleshooting

### Images not matching
- Ensure image filenames match the format `FirstName_LastName.ext`
- Check that names in CSV match exactly (case-insensitive)
- Special characters in names are converted to underscores

### Missing images
- Attendees without matching images are skipped
- Check the "Review Attendees" tab to see which attendees have images

### PDF generation errors
- Ensure all required columns are in your CSV
- Check that the headshots directory exists and contains images
- Verify you have write permissions for the output directory

## Future Events

To use this for a new event:
1. Create a new CSV file with attendee data
2. Create a new headshots directory (or use an existing one)
3. Upload images matching the naming convention
4. Generate new flashcards

The app is designed to be reusable for any event!

## Web Deployment

To host this app online, see [DEPLOYMENT.md](DEPLOYMENT.md) for instructions on deploying to Streamlit Cloud (free hosting).

Once deployed, you'll get a URL like `https://your-app-name.streamlit.app` that you can share or link from your website.



