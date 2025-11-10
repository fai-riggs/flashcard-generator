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
import requests
from urllib.parse import urlparse

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
    page_icon="",
    layout="wide",
)

# Custom CSS for eDEX-UI sci-fi terminal theme
st.markdown("""
<style>
    /* Pure black background - eDEX-UI style */
    .stApp {
        background: #000000 !important;
        background-color: #000000 !important;
    }
    
    /* Main content - pure black with orange borders */
    .main .block-container {
        background-color: #000000 !important;
        border: 1px solid #FF6B35;
        border-radius: 0px !important;
        padding: 1.5rem;
        margin-top: 1rem;
        box-shadow: none !important;
    }
    
    /* Headers - bright orange, no glow */
    h1, h2, h3, h4, h5, h6 {
        color: #FF6B35 !important;
        text-shadow: none !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold !important;
        letter-spacing: 1px;
    }
    
    /* All text - orange */
    p, span, div, label, li {
        color: #FF6B35 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Body text */
    body {
        background: #000000 !important;
        color: #FF6B35 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Sidebar - pure black with orange border */
    [data-testid="stSidebar"] {
        background: #000000 !important;
        border-right: 2px solid #FF6B35;
        box-shadow: none !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #FF6B35 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Buttons - terminal style, sharp corners, no glow */
    .stButton > button {
        background: #000000 !important;
        color: #FF6B35 !important;
        border: 2px solid #FF6B35 !important;
        border-radius: 0px !important;
        font-weight: bold;
        font-family: 'Courier New', monospace !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        box-shadow: none !important;
        text-shadow: none !important;
        transition: all 0.2s ease;
        padding: 0.75rem 1.5rem;
    }
    
    .stButton > button:hover {
        background: rgba(255, 107, 53, 0.1) !important;
        box-shadow: none !important;
        text-shadow: none !important;
    }
    
    /* Primary button */
    .stButton > button[kind="primary"] {
        background: rgba(255, 107, 53, 0.15) !important;
        box-shadow: none !important;
        border: 2px solid #FF6B35 !important;
    }
    
    /* Text inputs - terminal style */
    .stTextInput > div > div > input {
        background-color: #000000 !important;
        color: #FF6B35 !important;
        border: 1px solid #FF6B35 !important;
        border-radius: 0px !important;
        font-family: 'Courier New', monospace !important;
        box-shadow: none !important;
    }
    
    .stTextInput > div > div > input:focus {
        border: 2px solid #FF6B35 !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    /* Password input on login screen - completely invisible */
    .stTextInput {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    .stTextInput > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    .stTextInput > div > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    .stTextInput > div > div[data-baseweb="base-input"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        display: inline-flex !important;
        align-items: center !important;
        vertical-align: middle !important;
    }
    
    .stTextInput > div > div > input[type="password"] {
        background: transparent !important;
        border: none !important;
        outline: none !important;
        color: #FF6B35 !important;
        font-family: 'Courier New', monospace !important;
        font-size: 16px !important;
        padding: 0 !important;
        margin: 0 !important;
        box-shadow: none !important;
        width: auto !important;
        min-width: 200px !important;
        display: inline !important;
        vertical-align: middle !important;
    }
    
    .stTextInput {
        display: inline !important;
        vertical-align: middle !important;
    }
    
    .stTextInput > div > div > input[type="password"]:focus {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    /* Hide the eye icon and any buttons */
    .stTextInput button,
    .stTextInput svg,
    .stTextInput [data-baseweb="input"] button {
        display: none !important;
        visibility: hidden !important;
    }
    
    .stTextInput label {
        color: #FF6B35 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* File uploader - terminal style */
    .stFileUploader {
        background-color: #000000 !important;
        border: 1px dashed #FF6B35 !important;
        border-radius: 0px !important;
        padding: 1rem;
    }
    
    /* Selectbox - terminal style */
    .stSelectbox > div > div > select {
        background-color: #000000 !important;
        color: #FF6B35 !important;
        border: 1px solid #FF6B35 !important;
        border-radius: 0px !important;
        font-family: 'Courier New', monospace !important;
        box-shadow: none !important;
    }
    
    .stSelectbox label {
        color: #FF6B35 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Radio Buttons - terminal style */
    .stRadio > div {
        display: flex !important;
        flex-direction: row !important;
        gap: 2rem !important;
        flex-wrap: wrap !important;
    }
    
    .stRadio > div > label {
        background: #000000 !important;
        color: #FF6B35 !important;
        border: 2px solid #FF6B35 !important;
        border-radius: 0px !important;
        font-family: 'Courier New', monospace !important;
        font-size: 1rem !important;
        font-weight: bold !important;
        padding: 1rem 1.5rem !important;
        min-width: 200px !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
        text-shadow: none !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
    }
    
    .stRadio > div > label:hover {
        background: rgba(255, 107, 53, 0.1) !important;
        box-shadow: none !important;
        text-shadow: none !important;
    }
    
    /* Selected radio button */
    .stRadio > div > label:has(input[checked]) {
        background: rgba(255, 107, 53, 0.2) !important;
        border-color: #FF6B35 !important;
        box-shadow: none !important;
        color: #FF6B35 !important;
        text-shadow: none !important;
    }
    
    /* Radio button circle */
    .stRadio input[type="radio"] {
        width: 18px !important;
        height: 18px !important;
        margin-right: 0.75rem !important;
        accent-color: #FF6B35 !important;
    }
    
    /* Checkbox - terminal style */
    .stCheckbox > label {
        color: #FF6B35 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    .stCheckbox input[type="checkbox"] {
        accent-color: #FF6B35;
    }
    
    /* Tabs - terminal style */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #000000 !important;
        border-bottom: 2px solid #FF6B35;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #FF6B35 !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    .stTabs [aria-selected="true"] {
        color: #FF6B35 !important;
        border-bottom: 3px solid #FF6B35;
        text-shadow: none !important;
        background: rgba(255, 107, 53, 0.1) !important;
    }
    
    /* Success/Info/Error messages - terminal style */
    .stSuccess {
        background-color: rgba(255, 107, 53, 0.05) !important;
        border-left: 3px solid #FF6B35 !important;
        border-radius: 0px !important;
        color: #FF6B35 !important;
        font-family: 'Courier New', monospace !important;
        box-shadow: none !important;
    }
    
    .stInfo {
        background-color: rgba(255, 107, 53, 0.05) !important;
        border-left: 3px solid #FF6B35 !important;
        border-radius: 0px !important;
        color: #FF6B35 !important;
        font-family: 'Courier New', monospace !important;
        box-shadow: none !important;
    }
    
    .stError {
        background-color: rgba(255, 0, 0, 0.05) !important;
        border-left: 3px solid #FF0000 !important;
        border-radius: 0px !important;
        color: #FF6B6B !important;
        font-family: 'Courier New', monospace !important;
        box-shadow: none !important;
    }
    
    .stWarning {
        background-color: rgba(255, 165, 0, 0.05) !important;
        border-left: 3px solid #FFA500 !important;
        border-radius: 0px !important;
        color: #FFA500 !important;
        font-family: 'Courier New', monospace !important;
        box-shadow: none !important;
    }
    
    /* Dataframes - terminal style */
    .stDataFrame {
        background-color: #000000 !important;
        border: 1px solid #FF6B35 !important;
        border-radius: 0px !important;
    }
    
    /* Metrics - terminal style */
    [data-testid="stMetricValue"] {
        color: #FF6B35 !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold;
        text-shadow: none !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #FF6B35 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    [data-testid="stMetricContainer"] {
        background-color: #000000 !important;
        border: 1px solid #FF6B35 !important;
        border-radius: 0px !important;
        padding: 1rem;
        box-shadow: none !important;
    }
    
    /* Expander - terminal style */
    .streamlit-expanderHeader {
        background-color: #000000 !important;
        color: #FF6B35 !important;
        border: 1px solid #FF6B35 !important;
        border-radius: 0px !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold;
    }
    
    /* Password input */
    input[type="password"] {
        font-family: 'Courier New', monospace !important;
        letter-spacing: 3px;
        color: #FF6B35 !important;
    }
    
    /* Textarea - terminal style */
    .stTextArea > div > div > textarea {
        background-color: #000000 !important;
        color: #FF6B35 !important;
        border: 1px solid #FF6B35 !important;
        border-radius: 0px !important;
        font-family: 'Courier New', monospace !important;
    }
    
    .stTextArea label {
        color: #FF6B35 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Scrollbar - terminal style */
    ::-webkit-scrollbar {
        width: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: #000000;
        border: 1px solid #FF6B35;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #FF6B35;
        border-radius: 0px;
        box-shadow: none !important;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #FF8C42;
        box-shadow: none !important;
    }
    
    /* Hacker Loading Animation */
    @keyframes hackScan {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100vw); }
    }
    
    @keyframes glitch {
        0%, 100% { transform: translate(0); }
        20% { transform: translate(-2px, 2px); }
        40% { transform: translate(-2px, -2px); }
        60% { transform: translate(2px, 2px); }
        80% { transform: translate(2px, -2px); }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .hacker-loader {
        background: #000000;
        border: 2px solid #FF6B35;
        border-radius: 0px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: none !important;
        position: relative;
        overflow: hidden;
    }
    
    .hacker-loader::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 107, 53, 0.1), transparent);
        animation: hackScan 2s infinite;
    }
    
    .hacker-text {
        font-family: 'Courier New', monospace;
        color: #FF6B35;
        text-shadow: none !important;
        font-size: 1.2rem;
        letter-spacing: 2px;
        animation: glitch 0.3s infinite;
    }
    
    .hacker-progress {
        width: 100%;
        height: 30px;
        background: #000000;
        border: 2px solid #FF6B35;
        border-radius: 0px;
        margin-top: 1rem;
        overflow: hidden;
        position: relative;
    }
    
    .hacker-progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #FF6B35, #FF8C42, #FF6B35);
        background-size: 200% 100%;
        animation: progressFlow 2s linear infinite;
        box-shadow: none !important;
        transition: width 0.3s ease;
    }
    
    @keyframes progressFlow {
        0% { background-position: 0% 0%; }
        100% { background-position: 200% 0%; }
    }
    
    .hacker-status {
        font-family: 'Courier New', monospace;
        color: #FF6B35;
        font-size: 0.9rem;
        margin-top: 0.5rem;
        letter-spacing: 1px;
        text-shadow: none !important;
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: #000000 !important;
        color: #FF6B35 !important;
        border: 2px solid #FF6B35 !important;
        border-radius: 0px !important;
        font-family: 'Courier New', monospace !important;
        box-shadow: none !important;
    }
    
    .stDownloadButton > button:hover {
        background: rgba(255, 107, 53, 0.1) !important;
        box-shadow: none !important;
    }
    
    /* Captions */
    .stCaption {
        color: #FF6B35 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Images */
    img {
        border: 1px solid #FF6B35;
        box-shadow: none !important;
    }
</style>
""", unsafe_allow_html=True)

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
if "temp_base_dir" not in st.session_state:
    st.session_state.temp_base_dir = None


def get_password() -> str:
    """Get password from Streamlit secrets or use default."""
    try:
        return st.secrets.get("app_password", "pdfhack")
    except (AttributeError, FileNotFoundError):
        # Fallback if secrets.toml doesn't exist
        return "pdfhack"


def check_password() -> bool:
    """Check if user is authenticated."""
    if st.session_state.authenticated:
        return True
    
    # Basic terminal prompt with blinking cursor - inline with input
    st.markdown("""
    <style>
    .terminal-line {
        display: flex;
        align-items: center;
        font-family: 'Courier New', monospace;
        color: #FF6B35;
        font-size: 16px;
        gap: 8px;
    }
    .blink-cursor {
        animation: blink 1s infinite;
        color: #FF6B35;
        display: inline-block;
    }
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    </style>
    <div class="terminal-line">
        <span>></span>
        <span class="blink-cursor" id="blink-cursor">_</span>
    </div>
    <script>
    setTimeout(function() {
        var input = document.querySelector('input[type="password"]');
        var cursor = document.getElementById('blink-cursor');
        var terminalLine = document.querySelector('.terminal-line');
        if (input && cursor && terminalLine) {
            // Move input into terminal line
            input.style.display = 'inline';
            input.style.verticalAlign = 'middle';
            terminalLine.appendChild(input);
            input.focus();
            input.addEventListener('input', function() {
                cursor.style.display = this.value.length > 0 ? 'none' : 'inline-block';
            });
        }
    }, 100);
    </script>
    """, unsafe_allow_html=True)
    
    password_input = st.text_input(
        "",
        type="password",
        key="password_input",
        label_visibility="collapsed",
        placeholder="",
        autocomplete="off"
    )
    
    # Check password on Enter (when input changes and is not empty)
    if password_input and password_input == get_password():
        st.session_state.authenticated = True
        st.rerun()
    
    return False


def download_image_from_url(url: str, directory: Path, filename: str) -> Optional[Path]:
    """Download an image from a URL and save it to the specified directory."""
    try:
        directory.mkdir(parents=True, exist_ok=True)
        
        # Download the image
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # Determine file extension from URL or content type
        parsed_url = urlparse(url)
        url_path = parsed_url.path
        if url_path and '.' in url_path:
            ext = url_path.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                ext = 'jpg'  # Default
        else:
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = 'jpg'
            elif 'png' in content_type:
                ext = 'png'
            elif 'webp' in content_type:
                ext = 'webp'
            else:
                ext = 'jpg'  # Default
        
        # Ensure filename has correct extension
        if not filename.endswith(f'.{ext}'):
            filename = f"{filename.rsplit('.', 1)[0] if '.' in filename else filename}.{ext}"
        
        file_path = directory / filename
        
        # Save the image
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Verify it's a valid image
        try:
            img = Image.open(file_path)
            img.verify()
        except Exception:
            file_path.unlink()
            return None
        
        return file_path
    except Exception as e:
        st.error(f"Error downloading image from {url}: {e}")
        return None


def get_temp_session_dir() -> Path:
    """Get or create a temporary directory for this session."""
    if st.session_state.temp_base_dir is None:
        st.session_state.temp_base_dir = Path(tempfile.mkdtemp(prefix="flashcard_session_"))
    return st.session_state.temp_base_dir


def clear_session_data():
    """Clear all session data and clean up temporary files."""
    # Clean up temporary directory if it exists
    if st.session_state.temp_base_dir and st.session_state.temp_base_dir.exists():
        try:
            import shutil
            shutil.rmtree(st.session_state.temp_base_dir)
        except Exception:
            pass  # Ignore cleanup errors
        st.session_state.temp_base_dir = None
    
    # Clear all data
    st.session_state.attendees_data = None
    st.session_state.headshot_dir = None
    st.session_state.csv_path = None
    st.session_state.airtable_url = None
    st.session_state.airtable_api_key = None


def show_hacker_loader(status_text: str, progress: float = 0.0) -> str:
    """Return HTML for a hacker-style loading animation with progress bar."""
    progress_pct = min(100, max(0, int(progress * 100)))
    
    return f"""
    <div class="hacker-loader">
        <div class="hacker-text">[SYSTEM] {status_text}</div>
        <div class="hacker-progress">
            <div class="hacker-progress-bar" style="width: {progress_pct}%;"></div>
        </div>
        <div class="hacker-status">> PROGRESS: {progress_pct}% | STATUS: ACTIVE</div>
    </div>
    """


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
    
    # eDEX-UI style header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; border-bottom: 2px solid #FF6B35; margin-bottom: 2rem; background: #000000;">
        <h1 style="margin: 0; font-size: 3rem; text-shadow: none; letter-spacing: 4px;">FLASHCARD GENERATOR</h1>
        <p style="color: #FF6B35; font-family: 'Courier New', monospace; letter-spacing: 3px; margin-top: 1rem; text-shadow: none;">
            > [SYSTEM] INITIALIZING... [READY]
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style="background: rgba(255, 107, 53, 0.05); border-left: 3px solid #FF6B35; padding: 1rem; margin-bottom: 2rem; font-family: 'Courier New', monospace; border-radius: 0px;">
        <strong style="color: #FF6B35; text-shadow: none;">> [INFO]</strong> <span style="color: #FF6B35;">Create printable flashcards and facebooks for events with attendee names and headshots.</span>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar for settings
    with st.sidebar:
        st.markdown("""
        <div style="border-bottom: 2px solid #FF6B35; padding-bottom: 1rem; margin-bottom: 1rem;">
            <h2 style="color: #FF6B35; text-shadow: none; font-family: 'Courier New', monospace; letter-spacing: 2px;">
                > [CONFIG]
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
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
        st.markdown("### Help")
        st.markdown("""
        1. **Upload CSV**: CSV with columns: First Name, Last Name, Organization, Job Title
        2. **Upload Images**: Add headshot images (named as FirstName_LastName.ext)
        3. **Review Matches**: Check that names match images correctly
        4. **Generate PDFs**: Create printable flashcards or facebooks
        """)
        
        st.markdown("---")
        if st.button("Clear All Session Data", help="Remove all uploaded files and data from this session"):
            clear_session_data()
            st.success("Session data cleared")
            st.rerun()

    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["Upload Data", "Manage Images", "Review Attendees", "Generate PDFs"])

    with tab1:
        st.header("Upload Attendee Data")
        
        # Data source selection
        data_source = st.radio(
            "Choose data source:",
            ["Upload CSV File", "Import from Airtable"],
            help="Select how you want to provide attendee data",
            key="data_source_radio"
        )
        
        # Clear data when switching sources
        if "last_data_source" in st.session_state and st.session_state.last_data_source != data_source:
            clear_session_data()
        st.session_state.last_data_source = data_source
        
        st.markdown("---")
        
        if data_source == "Upload CSV File":
            # CSV Upload
            st.subheader("CSV File")
            uploaded_csv = st.file_uploader(
                "Upload attendee CSV file",
                type=["csv"],
                help="CSV should have columns: First Name, Last Name, Organization, Job Title",
            )
            
            if uploaded_csv is not None:
                # Save CSV to session temp location
                session_dir = get_temp_session_dir()
                csv_path = session_dir / uploaded_csv.name
                with open(csv_path, "wb") as f:
                    f.write(uploaded_csv.getbuffer())
                
                st.session_state.csv_path = csv_path
                # Clear Airtable data when CSV is uploaded
                st.session_state.airtable_url = None
                st.session_state.airtable_api_key = None
            
                # Display preview
                try:
                    df = pd.read_csv(csv_path, encoding="utf-8-sig")
                    st.success(f"CSV loaded: {len(df)} rows")
                    st.dataframe(df.head(10), use_container_width=True)
                
                    # Check required columns
                    required_cols = ["First Name", "Last Name"]
                    missing_cols = [col for col in required_cols if col not in df.columns]
                    if missing_cols:
                        st.error(f"Missing required columns: {', '.join(missing_cols)}")
                    else:
                        st.info("Required columns found")
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
                st.info("**API Key Setup:** Add your Airtable API key in Streamlit Cloud secrets as `airtable_api_key`, or enter it below.")
                airtable_api_key = st.text_input(
                    "Airtable API Key",
                    type="password",
                    help="Get your API key from https://airtable.com/create/tokens",
                    value=airtable_api_key
                )
            else:
                st.success("API key loaded from secrets")
            
            if airtable_url and airtable_api_key:
                if st.button("Test Airtable Connection", type="primary"):
                    loading_placeholder = st.empty()
                    loading_placeholder.markdown(show_hacker_loader("TESTING CONNECTION...", 0.3), unsafe_allow_html=True)
                    try:
                        from generate_flashcards import parse_airtable_url
                        parsed = parse_airtable_url(airtable_url)
                        if parsed:
                            base_id, table_id = parsed
                            loading_placeholder.markdown(show_hacker_loader("AUTHENTICATING...", 0.6), unsafe_allow_html=True)
                            import time
                            time.sleep(0.3)
                            
                            loading_placeholder.markdown(show_hacker_loader("FETCHING DATA...", 0.9), unsafe_allow_html=True)
                            
                            # Try to fetch a sample record
                            try:
                                from pyairtable import Api
                                api = Api(airtable_api_key)
                                table = api.table(base_id, table_id)
                                sample = table.first()
                                
                                loading_placeholder.empty()
                                if sample:
                                    st.success(f"URL parsed successfully!")
                                    st.info(f"**Base ID:** `{base_id[:8]}...`  **Table ID:** `{table_id[:8]}...`")
                                    st.success(f"Connection successful! Found table with fields.")
                                    if "fields" in sample:
                                        st.info(f"**Available fields:** {', '.join(list(sample['fields'].keys())[:10])}")
                            except Exception as e:
                                loading_placeholder.empty()
                                st.error(f"Could not connect to Airtable: {e}")
                                st.info("Make sure your API key has access to this base.")
                        else:
                            loading_placeholder.empty()
                            st.error("Could not parse Airtable URL. Make sure it's a valid Airtable link.")
                    except Exception as e:
                        loading_placeholder.empty()
                        st.error(f"Error: {e}")
            
            # Store in session state for later use
            if airtable_url and airtable_api_key:
                st.session_state.airtable_url = airtable_url
                st.session_state.airtable_api_key = airtable_api_key
                # Clear CSV data when Airtable is used
                st.session_state.csv_path = None
                # Clean up any existing temp files
                if st.session_state.temp_base_dir and st.session_state.temp_base_dir.exists():
                    try:
                        import shutil
                        for item in st.session_state.temp_base_dir.iterdir():
                            if item.is_file() and item.suffix == '.csv':
                                item.unlink()
                    except Exception:
                        pass

        # Headshot Directory Selection
        st.subheader("Headshot Images")
        st.markdown("""
        <div style="background: rgba(255, 107, 53, 0.05); border-left: 3px solid #FF6B35; padding: 1rem; margin-bottom: 1rem; font-family: 'Courier New', monospace; border-radius: 0px;">
            <strong style="color: #FF6B35; text-shadow: none;">> [INFO]</strong> <span style="color: #FF6B35;">Images are stored temporarily in session memory and will be cleared when you switch data sources or close the session.</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Always use session temp directory for images
        if st.session_state.headshot_dir is None:
            session_dir = get_temp_session_dir()
            headshots_dir = session_dir / "headshots"
            headshots_dir.mkdir(exist_ok=True)
            st.session_state.headshot_dir = headshots_dir
        
        if st.session_state.headshot_dir.exists():
            image_count = len(list(st.session_state.headshot_dir.glob("*")))
            st.info(f"Temporary session directory: {len(list(st.session_state.headshot_dir.glob('*')))} images")

    with tab2:
        st.header("Manage Headshot Images")
        
        if st.session_state.headshot_dir is None:
            st.warning("Please upload a CSV or connect to Airtable first to initialize the session.")
        else:
            headshot_dir = st.session_state.headshot_dir
            
            st.markdown("""
            <div style="background: rgba(255, 107, 53, 0.05); border-left: 3px solid #FF6B35; padding: 1rem; margin-bottom: 1rem; font-family: 'Courier New', monospace; border-radius: 0px;">
                <strong style="color: #FF6B35; text-shadow: none;">> [NOTE]</strong> <span style="color: #FF6B35;">Images are stored in a temporary session directory and will be automatically cleared when you switch data sources.</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Download images from URLs
            st.subheader("Download Images from URLs")
            st.markdown("""
            <div style="background: rgba(255, 107, 53, 0.05); border-left: 3px solid #FF6B35; padding: 1rem; margin-bottom: 1rem; font-family: 'Courier New', monospace; border-radius: 0px;">
                <strong style="color: #FF6B35; text-shadow: none;">> [INFO]</strong> <span style="color: #FF6B35;">Enter image URLs below. Images will be downloaded and saved with the filename format: FirstName_LastName.ext</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Single URL input
            image_url = st.text_input(
                "Image URL",
                placeholder="https://example.com/images/John_Doe.jpg",
                help="Enter the full URL of the image to download",
                key="single_image_url"
            )
            
            if st.button("Download Image", key="download_single"):
                if image_url:
                    loading_placeholder = st.empty()
                    loading_placeholder.markdown(show_hacker_loader("DOWNLOADING IMAGE...", 0.3), unsafe_allow_html=True)
                    import time
                    time.sleep(0.2)
                    
                    # Extract filename from URL or prompt for name
                    parsed_url = urlparse(image_url)
                    url_filename = Path(parsed_url.path).name
                    
                    if not url_filename or '.' not in url_filename:
                        # Prompt for filename
                        filename = st.text_input(
                            "Enter filename (FirstName_LastName.ext)",
                            key="url_filename_input",
                            help="Enter filename in format: FirstName_LastName.jpg"
                        )
                        if filename:
                            loading_placeholder.markdown(show_hacker_loader("SAVING IMAGE...", 0.7), unsafe_allow_html=True)
                            time.sleep(0.2)
                            file_path = download_image_from_url(image_url, headshot_dir, filename)
                            loading_placeholder.empty()
                            if file_path:
                                st.success(f"Downloaded: {file_path.name}")
                            else:
                                st.error("Failed to download image. Check URL and try again.")
                    else:
                        loading_placeholder.markdown(show_hacker_loader("SAVING IMAGE...", 0.7), unsafe_allow_html=True)
                        time.sleep(0.2)
                        file_path = download_image_from_url(image_url, headshot_dir, url_filename)
                        loading_placeholder.empty()
                        if file_path:
                            st.success(f"Downloaded: {file_path.name}")
                        else:
                            st.error("Failed to download image. Check URL and try again.")
                else:
                    st.warning("Please enter an image URL")
            
            st.markdown("---")
            
            # Bulk URL input
            st.subheader("Bulk Download from URLs")
            url_text = st.text_area(
                "Enter image URLs (one per line)",
                placeholder="https://example.com/images/John_Doe.jpg\nhttps://example.com/images/Jane_Smith.png",
                help="Enter multiple image URLs, one per line. Filenames will be extracted from URLs.",
                height=150
            )
            
            if st.button("Download All Images", key="download_bulk"):
                if url_text:
                    urls = [url.strip() for url in url_text.split('\n') if url.strip()]
                    if urls:
                        loading_placeholder = st.empty()
                        total = len(urls)
                        success_count = 0
                        
                        for idx, url in enumerate(urls):
                            progress = (idx + 1) / total
                            loading_placeholder.markdown(show_hacker_loader(f"DOWNLOADING [{idx+1}/{total}]...", progress * 0.9), unsafe_allow_html=True)
                            
                            parsed_url = urlparse(url)
                            url_filename = Path(parsed_url.path).name
                            
                            if url_filename and '.' in url_filename:
                                file_path = download_image_from_url(url, headshot_dir, url_filename)
                                if file_path:
                                    success_count += 1
                            else:
                                st.warning(f"Skipped {url} - could not determine filename")
                            
                            import time
                            time.sleep(0.1)
                        
                        loading_placeholder.markdown(show_hacker_loader("COMPLETE", 1.0), unsafe_allow_html=True)
                        time.sleep(0.3)
                        loading_placeholder.empty()
                        st.success(f"Downloaded {success_count} of {total} images")
                    else:
                        st.warning("No valid URLs found")
                else:
                    st.warning("Please enter image URLs")
            
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
                                if st.button("Delete", key=f"delete_{idx}", help="Delete image"):
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
            st.warning("Please upload CSV or connect to Airtable, and set headshots directory first.")
        else:
            if st.button("Load & Match Attendees"):
                loading_placeholder = st.empty()
                
                try:
                    # Load from Airtable or CSV
                    if st.session_state.airtable_url and st.session_state.airtable_api_key:
                        loading_placeholder.markdown(show_hacker_loader("CONNECTING TO AIRTABLE...", 0.1), unsafe_allow_html=True)
                        import time
                        time.sleep(0.3)
                        
                        loading_placeholder.markdown(show_hacker_loader("PARSING URL...", 0.2), unsafe_allow_html=True)
                        time.sleep(0.2)
                        
                        loading_placeholder.markdown(show_hacker_loader("AUTHENTICATING...", 0.3), unsafe_allow_html=True)
                        time.sleep(0.3)
                        
                        loading_placeholder.markdown(show_hacker_loader("FETCHING RECORDS...", 0.5), unsafe_allow_html=True)
                        attendees = load_attendees_from_airtable(
                            st.session_state.airtable_url,
                            st.session_state.airtable_api_key,
                            st.session_state.headshot_dir,
                        )
                        
                        loading_placeholder.markdown(show_hacker_loader("PROCESSING IMAGES...", 0.7), unsafe_allow_html=True)
                        time.sleep(0.3)
                        
                        loading_placeholder.markdown(show_hacker_loader("MATCHING HEADSHOTS...", 0.9), unsafe_allow_html=True)
                        time.sleep(0.2)
                        
                        loading_placeholder.empty()
                        st.info("Loaded from Airtable")
                    elif st.session_state.csv_path:
                        loading_placeholder.markdown(show_hacker_loader("PARSING CSV...", 0.2), unsafe_allow_html=True)
                        import time
                        time.sleep(0.2)
                        
                        loading_placeholder.markdown(show_hacker_loader("LOADING ATTENDEES...", 0.4), unsafe_allow_html=True)
                        attendees = load_attendees(
                            st.session_state.csv_path,
                            st.session_state.headshot_dir,
                        )
                        
                        loading_placeholder.markdown(show_hacker_loader("PROCESSING IMAGES...", 0.7), unsafe_allow_html=True)
                        time.sleep(0.3)
                        
                        loading_placeholder.markdown(show_hacker_loader("MATCHING HEADSHOTS...", 0.9), unsafe_allow_html=True)
                        time.sleep(0.2)
                        
                        loading_placeholder.empty()
                        st.info("Loaded from CSV")
                    else:
                        st.error("No data source available")
                        attendees = []
                    
                    # Apply FAI exclusion if enabled
                    if exclude_fai:
                        original_count = len(attendees)
                        attendees = filter_attendees(attendees, DEFAULT_EXCLUDED_ORGANIZATIONS)
                        excluded_count = original_count - len(attendees)
                        if excluded_count > 0:
                            st.info(f"Excluded {excluded_count} attendee(s) from Foundation for American Innovation")
                    
                    st.session_state.attendees_data = attendees
                    
                    if attendees:
                        st.success(f"Matched {len(attendees)} attendees with images")
                    else:
                        st.error("No attendees matched. Check data format and image filenames.")
                except Exception as e:
                    loading_placeholder.empty()
                    st.error(f"Error loading attendees: {e}")
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
            st.warning("Please load attendees in the Review Attendees tab first.")
        else:
            attendees = st.session_state.attendees_data
            
            # Apply FAI exclusion if enabled (in case it wasn't applied during load)
            if exclude_fai:
                original_count = len(attendees)
                attendees = filter_attendees(attendees, DEFAULT_EXCLUDED_ORGANIZATIONS)
                excluded_count = original_count - len(attendees)
                if excluded_count > 0:
                    st.info(f"Excluding {excluded_count} attendee(s) from Foundation for American Innovation")
            
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
            
            if st.button("Generate PDFs", type="primary"):
                loading_placeholder = st.empty()
                loading_placeholder.markdown(show_hacker_loader("INITIALIZING PDF GENERATION...", 0.1), unsafe_allow_html=True)
                import time
                time.sleep(0.2)
                
                attendees_to_use = attendees[:limit_cards] if limit_cards > 0 else attendees
                
                temp_dir = Path(tempfile.mkdtemp())
                pdf_files = {}
                
                try:
                    total_tasks = sum([generate_combined, generate_fronts, generate_backs, generate_guides, generate_facebooks])
                    current_task = 0
                    
                    if generate_combined:
                        current_task += 1
                        loading_placeholder.markdown(show_hacker_loader(f"GENERATING COMBINED PDF... [{current_task}/{total_tasks}]", current_task / total_tasks), unsafe_allow_html=True)
                        combined_path = temp_dir / "flashcards_duplex.pdf"
                        draw_combined(attendees_to_use, combined_path, duplex_mode=duplex_mode)
                        pdf_files["Combined PDF"] = combined_path
                        time.sleep(0.2)
                    
                    if generate_fronts:
                        current_task += 1
                        loading_placeholder.markdown(show_hacker_loader(f"GENERATING FRONTS... [{current_task}/{total_tasks}]", current_task / total_tasks), unsafe_allow_html=True)
                        fronts_path = temp_dir / "flashcards_fronts.pdf"
                        draw_fronts(attendees_to_use, fronts_path)
                        pdf_files["Fronts PDF"] = fronts_path
                        time.sleep(0.2)
                    
                    if generate_backs:
                        current_task += 1
                        loading_placeholder.markdown(show_hacker_loader(f"GENERATING BACKS... [{current_task}/{total_tasks}]", current_task / total_tasks), unsafe_allow_html=True)
                        backs_path = temp_dir / "flashcards_backs.pdf"
                        draw_backs(attendees_to_use, backs_path, duplex_mode=duplex_mode)
                        pdf_files["Backs PDF"] = backs_path
                        time.sleep(0.2)
                    
                    if generate_guides:
                        current_task += 1
                        loading_placeholder.markdown(show_hacker_loader(f"GENERATING CUT GUIDES... [{current_task}/{total_tasks}]", current_task / total_tasks), unsafe_allow_html=True)
                        guides_path = temp_dir / "flashcards_cut_guides.pdf"
                        draw_guides(attendees_to_use, guides_path, duplex_mode=duplex_mode)
                        pdf_files["Cut Guides PDF"] = guides_path
                        time.sleep(0.2)
                    
                    if generate_facebooks:
                        current_task += 1
                        loading_placeholder.markdown(show_hacker_loader(f"GENERATING FACEBOOK PROOF... [{current_task}/{total_tasks}]", current_task / total_tasks), unsafe_allow_html=True)
                        facebooks_path = temp_dir / "facebook_proof.pdf"
                        draw_facebooks(attendees_to_use, facebooks_path)
                        pdf_files["Facebook Proof PDF"] = facebooks_path
                        time.sleep(0.2)
                    
                    loading_placeholder.markdown(show_hacker_loader("COMPLETE", 1.0), unsafe_allow_html=True)
                    time.sleep(0.5)
                    loading_placeholder.empty()
                    
                    # Display download buttons
                    st.success(f"Generated {len(pdf_files)} PDF file(s)")
                    
                    for pdf_name, pdf_path in pdf_files.items():
                        with open(pdf_path, "rb") as pdf_file:
                            st.download_button(
                                label=f"Download {pdf_name}",
                                data=pdf_file.read(),
                                file_name=pdf_path.name,
                                mime="application/pdf",
                                key=f"download_{pdf_name}",
                            )
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Error generating PDFs: {e}")
                    st.exception(e)


if __name__ == "__main__":
    main()



