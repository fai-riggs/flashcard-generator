#!/bin/bash
# Quick launcher script for the FAI Document Generator app

echo "🚀 Starting FAI Document Generator..."
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the app
streamlit run fai_document_generator.py




