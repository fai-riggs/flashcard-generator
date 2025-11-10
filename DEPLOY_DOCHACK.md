# Deploy DocHack to Streamlit Cloud

Follow these steps to create a new Streamlit Cloud app called "DocHack".

## Step 1: Go to Streamlit Cloud

1. Open https://share.streamlit.io/ in your browser
2. Sign in with your GitHub account (the one connected to `fai-riggs/flashcard-generator`)

## Step 2: Create New App

1. Click the **"New app"** button (usually in the top right or on the dashboard)
2. You'll see a form to configure your app

## Step 3: Configure the App

Fill in the following details:

### Repository
- **Repository**: Select `fai-riggs/flashcard-generator` from the dropdown
- **Branch**: `main` (or `master` if that's your default branch)

### App Configuration
- **Main file path**: `fai_document_generator.py`
  - ⚠️ **Important**: Make sure this is exactly `fai_document_generator.py` (not `flashcard_app.py`)

### App URL
- **App URL**: `dochack`
  - This will create the URL: `https://dochack.streamlit.app`
  - If `dochack` is taken, try: `dochack-fai` or `dochack-docs`

### Advanced Settings (Optional)
- You can leave these as default for now

## Step 4: Deploy

1. Click the **"Deploy!"** button
2. Streamlit will start building your app (takes 1-2 minutes)
3. You'll see a progress indicator

## Step 5: Set Password (After First Deploy)

Once the app is deployed:

1. Go to your app's settings (click the app name, then "Settings" or the gear icon)
2. Click **"Secrets"** in the left sidebar
3. Add the following in the secrets editor:

```toml
app_password = "your-secure-password-here"
```

4. Click **"Save"**
5. The app will automatically redeploy with password protection

**Default password**: The app uses `pdfhack` as default if no secret is set.

## Step 6: Access Your App

Your app will be available at:
```
https://dochack.streamlit.app
```

(Or whatever subdomain you chose if `dochack` was taken)

## Troubleshooting

### App won't deploy
- ✅ Make sure `fai_document_generator.py` exists in your repository
- ✅ Check that `requirements.txt` is in the root directory
- ✅ Verify all dependencies are listed in `requirements.txt`

### Import errors
- ✅ Ensure `generate_flashcards.py` and `generate_documents.py` are in the same directory
- ✅ Check that all Python files are committed to GitHub

### App is slow to load
- This is normal on the free tier (shared resources)
- First load may take 30-60 seconds

## Next Steps

1. Test the app at your new URL
2. Update any bookmarks or links
3. Share the URL with your team!

---

**Your new app URL**: `https://dochack.streamlit.app` (or the subdomain you chose)

