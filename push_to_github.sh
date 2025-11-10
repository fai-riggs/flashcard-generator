#!/bin/bash
# Script to push to GitHub
# Run this after creating your GitHub repository

echo "📦 Ready to push to GitHub!"
echo ""
echo "Step 1: Create a new repository on GitHub:"
echo "   → Go to https://github.com/new"
echo "   → Name it (e.g., 'flashcard-generator' or 'gala-headshots')"
echo "   → Make it PUBLIC (required for free Streamlit Cloud)"
echo "   → DON'T initialize with README (you already have one)"
echo ""
echo "Step 2: Copy the repository URL (HTTPS format)"
echo ""
read -p "Enter your GitHub repository URL (e.g., https://github.com/username/repo-name.git): " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "❌ No URL provided. Exiting."
    exit 1
fi

echo ""
echo "🚀 Adding remote and pushing..."
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "Next steps:"
    echo "1. Go to https://share.streamlit.io/"
    echo "2. Sign in with GitHub"
    echo "3. Click 'New app' and select your repository"
    echo "4. Set main file to: flashcard_app.py"
    echo "5. Deploy!"
else
    echo ""
    echo "❌ Push failed. Make sure:"
    echo "   - The repository exists on GitHub"
    echo "   - You have push access"
    echo "   - You're authenticated with GitHub (use 'gh auth login' if using GitHub CLI)"
fi

