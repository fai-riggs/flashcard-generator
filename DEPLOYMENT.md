# Deployment Guide: Streamlit Cloud

This guide will help you deploy the Flashcard & Facebook Generator app to Streamlit Cloud (free hosting).

## Prerequisites

1. A GitHub account (free)
2. Your code pushed to a GitHub repository

## Step 1: Push Code to GitHub

1. Initialize a git repository (if not already):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Flashcard & Facebook Generator"
   ```

2. Create a new repository on GitHub (https://github.com/new)
   - Name it something like `flashcard-generator` or `gala-headshots`
   - Make it public (required for free Streamlit Cloud)
   - Don't initialize with README (you already have one)

3. Push your code:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Sign in with your GitHub account
3. Click "New app"
4. Fill in the details:
   - **Repository**: Select your repository
   - **Branch**: `main` (or `master`)
   - **Main file path**: `flashcard_app.py`
   - **App URL**: Choose a custom subdomain (e.g., `gala-flashcards`)
5. Click "Deploy!"

## Step 3: Get Your App URL

After deployment (takes 1-2 minutes), you'll get a URL like:
```
https://YOUR_APP_NAME.streamlit.app
```

## Step 4: Add Link to Google Sites

1. Go to your Google Sites page: https://sites.google.com/thefai.org/faiwiki/events
2. Edit the page
3. Add a text or button element
4. Insert your Streamlit app URL as a link
5. Save the page

### Example Link Text:
- "Flashcard & Facebook Generator"
- "Generate Event Flashcards"
- "📇 Create Flashcards & Facebooks"

## Important Notes

- **Free tier**: Streamlit Cloud free tier is perfect for this app
- **File uploads**: Users can upload CSV and images directly in the app
- **No data storage**: Files are processed in memory and not stored permanently
- **Public repository**: Free tier requires a public GitHub repo
- **Updates**: Push changes to GitHub and Streamlit will auto-deploy

## Troubleshooting

### App won't deploy
- Check that `requirements.txt` includes all dependencies
- Ensure `flashcard_app.py` is in the root directory
- Verify the main file path is correct

### Import errors
- Make sure `generate_flashcards.py` is in the same directory as `flashcard_app.py`
- Check that all imports in `requirements.txt` are correct

### App is slow
- This is normal for free tier (shared resources)
- Consider upgrading to paid tier for better performance

## Alternative: Self-Hosted Options

If you prefer to host elsewhere:
- **Heroku**: Requires Procfile and additional setup
- **AWS/Azure/GCP**: More complex, requires server management
- **DigitalOcean App Platform**: Simple but costs money
- **Railway**: Good free tier alternative

Streamlit Cloud is recommended for easiest deployment.

