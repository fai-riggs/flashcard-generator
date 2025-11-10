#!/usr/bin/env python3
"""Flashcard Generator Web App

A user-friendly web interface for creating printable flashcards from attendee data.
Supports CSV upload, image management, and PDF generation for future events.
"""

import io
import shutil
import tempfile
from pathlib import Path
from typing import Optional

import streamlit as st
import pandas as pd
from PIL import Image

# Import the flashcard generation functions
from generate_flashcards import (
    load_attendees,
    load_attendees_from_airtable,
    draw_fronts,
    draw_backs,
    draw_combined,
    draw_guides,
    draw_facebooks,
    filter_attendees,
    DEFAULT_EXCLUDED_ORGANIZATIONS,
    DuplexMode,
    Attendee,
    find_headshot,
    build_expected_prefix,
)

# Page configuration
st.set_page_config(
    page_title="Flashcard & Facebook Generator",
    page_icon="📇",
    layout="wide",
)

# Initialize session state
if "attendees_data" not in st.session_state:
    st.session_state.attendees_data = None
if "headshot_dir" not in st.session_state:
    st.session_state.headshot_dir = None
if "csv_path" not in st.session_state:
    st.session_state.csv_path = None
if "airtable_url" not in st.session_state:
    st.session_state.airtable_url = None
if "airtable_api_key" not in st.session_state:
    st.session_state.airtable_api_key = None
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def get_password() -> str:
    """Get password from Streamlit secrets or use default."""
    try:
        return st.secrets.get("app_password", "flashcardsarefun")
    except (AttributeError, FileNotFoundError):
        # Fallback if secrets.toml doesn't exist
        return "flashcardsarefun"


def check_password() -> bool:
    """Check if user is authenticated."""
    if st.session_state.authenticated:
        return True
    
    # Password input form
    with st.container():
        st.markdown("### 🔒 Authentication Required")
        st.markdown("Please enter the password to access this application.")
        
        password_input = st.text_input(
            "Password",
            type="password",
            key="password_input",
            label_visibility="visible"
        )
        
        if st.button("Login", type="primary"):
            if password_input == get_password():
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")
        
        st.markdown("---")
        st.caption("💡 Contact the administrator if you need access.")
    
    return False


def save_uploaded_file(uploaded_file, directory: Path, filename: str) -> Path:
    """Save an uploaded file to the specified directory."""
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / filename
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def get_image_preview(image_path: Path, max_size: tuple[int, int] = (150, 150)) -> Optional[Image.Image]:
    """Load and resize an image for preview."""
    try:
        img = Image.open(image_path)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        return img
    except Exception:
        return None


def main():
    # Check authentication first
    if not check_password():
        st.stop()
    
    st.title("📇 Flashcard & Facebook Generator")
    st.markdown("Create printable flashcards and facebooks for events with attendee names and headshots.")

    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        duplex_mode = st.selectbox(
            "Duplex Printing Mode",
            options=[DuplexMode.SHORT_EDGE, DuplexMode.LONG_EDGE],
            format_func=lambda x: "Short Edge" if x == DuplexMode.SHORT_EDGE else "Long Edge",
            help="Select how your printer handles double-sided printing",
        )
        
        exclude_fai = st.checkbox(
            "Exclude Foundation for American Innovation",
            value=False,
            help="Remove attendees from Foundation for American Innovation from all outputs",
        )
        
        st.markdown("---")
        st.markdown("### 📚 Help")
        st.markdown("""
        1. **Upload CSV**: CSV with columns: First Name, Last Name, Organization, Job Title
        2. **Upload Images**: Add headshot images (named as FirstName_LastName.ext)
        3. **Review Matches**: Check that names match images correctly
        4. **Generate PDFs**: Create printable flashcards or facebooks
        """)

    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Upload Data", "🖼️ Manage Images", "👥 Review Attendees", "📑 Generate PDFs"])

    with tab1:
        st.header("Upload Attendee Data")
        
        # Data source selection
        data_source = st.radio(
            "Choose data source:",
            ["📄 Upload CSV File", "🔗 Import from Airtable"],
            help="Select how you want to provide attendee data"
        )
        
        st.markdown("---")
        
        if data_source == "📄 Upload CSV File":
            # CSV Upload
            st.subheader("CSV File")
            uploaded_csv = st.file_uploader(
                "Upload attendee CSV file",
                type=["csv"],
                help="CSV should have columns: First Name, Last Name, Organization, Job Title",
            )
            
            if uploaded_csv is not None:
                # Save CSV to temp location
                temp_dir = Path(tempfile.mkdtemp())
                csv_path = temp_dir / uploaded_csv.name
                with open(csv_path, "wb") as f:
                    f.write(uploaded_csv.getbuffer())
                
                st.session_state.csv_path = csv_path
                
                # Display preview
                try:
                    df = pd.read_csv(csv_path, encoding="utf-8-sig")
                    st.success(f"✅ CSV loaded: {len(df)} rows")
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    # Check required columns
                    required_cols = ["First Name", "Last Name"]
                    missing_cols = [col for col in required_cols if col not in df.columns]
                    if missing_cols:
                        st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                    else:
                        st.info("✅ Required columns found")
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")
        
        else:  # Airtable import
            st.subheader("Import from Airtable")
            st.markdown("""
            **How to use:**
            1. Open your Airtable base and copy the URL from your browser
            2. Paste it below
            3. Make sure your Airtable has columns for: First Name, Last Name, Organization, Job Title
            """)
            
            airtable_url = st.text_input(
                "Airtable URL",
                placeholder="https://airtable.com/appXXXXX/tableYYYYY/...",
                help="Paste the full Airtable URL or share link here"
            )
            
            # Get API key from secrets or allow input
            try:
                airtable_api_key = st.secrets.get("airtable_api_key", "")
            except (AttributeError, FileNotFoundError):
                airtable_api_key = ""
            
            if not airtable_api_key:
                st.info("💡 **API Key Setup:** Add your Airtable API key in Streamlit Cloud secrets as `airtable_api_key`, or enter it below.")
                airtable_api_key = st.text_input(
                    "Airtable API Key",
                    type="password",
                    help="Get your API key from https://airtable.com/create/tokens",
                    value=airtable_api_key
                )
            else:
                st.success("✅ API key loaded from secrets")
            
            if airtable_url and airtable_api_key:
                if st.button("🔍 Test Airtable Connection", type="primary"):
                    with st.spinner("Connecting to Airtable..."):
                        try:
                            from generate_flashcards import parse_airtable_url
                            parsed = parse_airtable_url(airtable_url)
                            if parsed:
                                base_id, table_id = parsed
                                st.success(f"✅ URL parsed successfully!")
                                st.info(f"**Base ID:** `{base_id[:8]}...`  **Table ID:** `{table_id[:8]}...`")
                                
                                # Try to fetch a sample record
                                try:
                                    from pyairtable import Api
                                    api = Api(airtable_api_key)
                                    table = api.table(base_id, table_id)
                                    sample = table.first()
                                    if sample:
                                        st.success(f"✅ Connection successful! Found table with fields.")
                                        if "fields" in sample:
                                            st.info(f"**Available fields:** {', '.join(list(sample['fields'].keys())[:10])}")
                                except Exception as e:
                                    st.error(f"❌ Could not connect to Airtable: {e}")
                                    st.info("💡 Make sure your API key has access to this base.")
                            else:
                                st.error("❌ Could not parse Airtable URL. Make sure it's a valid Airtable link.")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
            
            # Store in session state for later use
            if airtable_url and airtable_api_key:
                st.session_state.airtable_url = airtable_url
                st.session_state.airtable_api_key = airtable_api_key
                st.session_state.csv_path = None  # Clear CSV path when using Airtable

        # Headshot Directory Selection
        st.subheader("Headshot Images")
        
        col1, col2 = st.columns(2)
        
        with col1:
            use_existing = st.checkbox("Use existing headshots directory", value=True)
            if use_existing:
                headshot_dir_input = st.text_input(
                    "Headshots directory path",
                    value="headshots",
                    help="Path to directory containing headshot images",
                )
                if headshot_dir_input:
                    headshot_dir = Path(headshot_dir_input)
                    if headshot_dir.exists():
                        st.session_state.headshot_dir = headshot_dir
                        image_count = len(list(headshot_dir.glob("*")))
                        st.info(f"📁 Found {image_count} files in directory")
                    else:
                        st.warning(f"⚠️ Directory not found: {headshot_dir}")
        
        with col2:
            st.markdown("**Or create new directory**")
            new_dir_name = st.text_input("New directory name", value="headshots")
            if st.button("Create Directory"):
                new_dir = Path(new_dir_name)
                new_dir.mkdir(parents=True, exist_ok=True)
                st.session_state.headshot_dir = new_dir
                st.success(f"✅ Created directory: {new_dir}")

    with tab2:
        st.header("Manage Headshot Images")
        
        if st.session_state.headshot_dir is None:
            st.warning("⚠️ Please set up a headshots directory in the Upload Data tab first.")
        else:
            headshot_dir = st.session_state.headshot_dir
            
            # Upload new images
            st.subheader("Upload New Images")
            uploaded_images = st.file_uploader(
                "Upload headshot images",
                type=["jpg", "jpeg", "png", "webp"],
                accept_multiple_files=True,
                help="Images should be named as FirstName_LastName.ext (e.g., John_Doe.jpg)",
            )
            
            if uploaded_images:
                for uploaded_file in uploaded_images:
                    file_path = save_uploaded_file(uploaded_file, headshot_dir, uploaded_file.name)
                    st.success(f"✅ Saved: {uploaded_file.name}")
            
            # Display existing images
            st.subheader("Existing Images")
            if headshot_dir.exists():
                image_files = sorted([f for f in headshot_dir.iterdir() if f.is_file()])
                
                if image_files:
                    st.info(f"Found {len(image_files)} images")
                    
                    # Display in grid
                    cols = st.columns(4)
                    for idx, img_path in enumerate(image_files[:20]):  # Show first 20
                        with cols[idx % 4]:
                            preview = get_image_preview(img_path)
                            if preview:
                                st.image(preview, use_container_width=True)
                                st.caption(img_path.name)
                                if st.button("🗑️", key=f"delete_{idx}", help="Delete image"):
                                    img_path.unlink()
                                    st.rerun()
                else:
                    st.info("No images found in directory")
            else:
                st.warning(f"Directory does not exist: {headshot_dir}")

    with tab3:
        st.header("Review Attendees & Matches")
        
        has_data_source = st.session_state.csv_path is not None or (
            st.session_state.airtable_url is not None and st.session_state.airtable_api_key
        )
        
        if not has_data_source or st.session_state.headshot_dir is None:
            st.warning("⚠️ Please upload CSV or connect to Airtable, and set headshots directory first.")
        else:
            if st.button("🔄 Load & Match Attendees"):
                with st.spinner("Loading attendees and matching images..."):
                    try:
                        # Load from Airtable or CSV
                        if st.session_state.airtable_url and st.session_state.airtable_api_key:
                            attendees = load_attendees_from_airtable(
                                st.session_state.airtable_url,
                                st.session_state.airtable_api_key,
                                st.session_state.headshot_dir,
                            )
                            st.info("📡 Loaded from Airtable")
                        elif st.session_state.csv_path:
                            attendees = load_attendees(
                                st.session_state.csv_path,
                                st.session_state.headshot_dir,
                            )
                            st.info("📄 Loaded from CSV")
                        else:
                            st.error("❌ No data source available")
                            attendees = []
                        
                        # Apply FAI exclusion if enabled
                        if exclude_fai:
                            original_count = len(attendees)
                            attendees = filter_attendees(attendees, DEFAULT_EXCLUDED_ORGANIZATIONS)
                            excluded_count = original_count - len(attendees)
                            if excluded_count > 0:
                                st.info(f"ℹ️ Excluded {excluded_count} attendee(s) from Foundation for American Innovation")
                        
                        st.session_state.attendees_data = attendees
                        
                        if attendees:
                            st.success(f"✅ Matched {len(attendees)} attendees with images")
                        else:
                            st.error("❌ No attendees matched. Check data format and image filenames.")
                    except Exception as e:
                        st.error(f"❌ Error loading attendees: {e}")
                        st.exception(e)
            
            if st.session_state.attendees_data:
                attendees = st.session_state.attendees_data
                
                st.metric("Total Cards", len(attendees))
                
                # Display attendees in a table with previews
                st.subheader("Attendee Preview")
                
                # Search/filter
                search_term = st.text_input("🔍 Search attendees", placeholder="Name, organization, or title...")
                
                filtered_attendees = attendees
                if search_term:
                    search_lower = search_term.lower()
                    filtered_attendees = [
                        a for a in attendees
                        if (search_lower in a.full_name.lower() or
                            search_lower in (a.organization or "").lower() or
                            search_lower in (a.title or "").lower())
                    ]
                
                st.info(f"Showing {len(filtered_attendees)} of {len(attendees)} attendees")
                
                # Display cards
                for attendee in filtered_attendees[:50]:  # Limit to 50 for performance
                    with st.expander(f"👤 {attendee.full_name}"):
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            preview = get_image_preview(attendee.image_path, max_size=(200, 200))
                            if preview:
                                st.image(preview, use_container_width=True)
                        with col2:
                            st.write(f"**Organization:** {attendee.organization or 'N/A'}")
                            st.write(f"**Title:** {attendee.title or 'N/A'}")
                            st.write(f"**Image:** `{attendee.image_path.name}`")

    with tab4:
        st.header("Generate PDFs")
        
        if st.session_state.attendees_data is None or len(st.session_state.attendees_data) == 0:
            st.warning("⚠️ Please load attendees in the Review Attendees tab first.")
        else:
            attendees = st.session_state.attendees_data
            
            # Apply FAI exclusion if enabled (in case it wasn't applied during load)
            if exclude_fai:
                original_count = len(attendees)
                attendees = filter_attendees(attendees, DEFAULT_EXCLUDED_ORGANIZATIONS)
                excluded_count = original_count - len(attendees)
                if excluded_count > 0:
                    st.info(f"ℹ️ Excluding {excluded_count} attendee(s) from Foundation for American Innovation")
            
            st.info(f"Ready to generate PDFs for {len(attendees)} attendees")
            
            # PDF options
            st.subheader("Flashcard Options")
            col1, col2 = st.columns(2)
            
            with col1:
                generate_combined = st.checkbox("Combined (Front + Back)", value=True)
                generate_fronts = st.checkbox("Fronts Only", value=False)
                generate_backs = st.checkbox("Backs Only", value=False)
                generate_guides = st.checkbox("Cut Guides", value=False)
            
            with col2:
                limit_cards = st.number_input(
                    "Limit number of cards (for testing)",
                    min_value=0,
                    max_value=len(attendees),
                    value=0,
                    help="Set to 0 to generate all cards",
                )
            
            st.subheader("Facebook Options")
            generate_facebooks = st.checkbox("Generate Facebook Proof", value=False, help="Five attendees per page, headshot left, details right")
            
            if st.button("🚀 Generate PDFs", type="primary"):
                with st.spinner("Generating PDFs..."):
                    attendees_to_use = attendees[:limit_cards] if limit_cards > 0 else attendees
                    
                    temp_dir = Path(tempfile.mkdtemp())
                    pdf_files = {}
                    
                    try:
                        if generate_combined:
                            combined_path = temp_dir / "flashcards_duplex.pdf"
                            draw_combined(attendees_to_use, combined_path, duplex_mode=duplex_mode)
                            pdf_files["Combined PDF"] = combined_path
                        
                        if generate_fronts:
                            fronts_path = temp_dir / "flashcards_fronts.pdf"
                            draw_fronts(attendees_to_use, fronts_path)
                            pdf_files["Fronts PDF"] = fronts_path
                        
                        if generate_backs:
                            backs_path = temp_dir / "flashcards_backs.pdf"
                            draw_backs(attendees_to_use, backs_path, duplex_mode=duplex_mode)
                            pdf_files["Backs PDF"] = backs_path
                        
                        if generate_guides:
                            guides_path = temp_dir / "flashcards_cut_guides.pdf"
                            draw_guides(attendees_to_use, guides_path, duplex_mode=duplex_mode)
                            pdf_files["Cut Guides PDF"] = guides_path
                        
                        if generate_facebooks:
                            facebooks_path = temp_dir / "facebook_proof.pdf"
                            draw_facebooks(attendees_to_use, facebooks_path)
                            pdf_files["Facebook Proof PDF"] = facebooks_path
                        
                        # Display download buttons
                        st.success(f"✅ Generated {len(pdf_files)} PDF file(s)")
                        
                        for pdf_name, pdf_path in pdf_files.items():
                            with open(pdf_path, "rb") as pdf_file:
                                st.download_button(
                                    label=f"📥 Download {pdf_name}",
                                    data=pdf_file.read(),
                                    file_name=pdf_path.name,
                                    mime="application/pdf",
                                    key=f"download_{pdf_name}",
                                )
                        
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"❌ Error generating PDFs: {e}")
                        st.exception(e)


if __name__ == "__main__":
    main()



