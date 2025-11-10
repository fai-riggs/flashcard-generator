#!/bin/bash
# Quick launcher script for the Flashcard Generator app

echo "🚀 Starting Flashcard Generator..."
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the app
streamlit run flashcard_app.py



