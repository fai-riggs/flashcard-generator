# Deployment Alternatives for FAI Document Generator

Since Vercel doesn't natively support Streamlit apps (it's designed for static sites and serverless functions), here are better alternatives that work with Streamlit:

## Recommended: Railway (Easiest Migration)

**Railway** is similar to Vercel but supports Python apps like Streamlit. It's free to start and very easy to use.

### Deploy to Railway:

1. **Sign up**: Go to https://railway.app/ and sign in with GitHub
2. **New Project**: Click "New Project" → "Deploy from GitHub repo"
3. **Select Repository**: Choose your `flashcard-generator` repository
4. **Auto-detect**: Railway will detect it's a Python app
5. **Configure**:
   - **Start Command**: `streamlit run fai_document_generator.py --server.port $PORT --server.address 0.0.0.0`
   - Railway will auto-detect Python and install from `requirements.txt`
6. **Deploy**: Click "Deploy" - it will build and deploy automatically
7. **Get URL**: Railway provides a URL like `https://your-app-name.up.railway.app`

### Create `Procfile` (optional, helps Railway):

Create a file named `Procfile` in the root directory:

```
web: streamlit run fai_document_generator.py --server.port $PORT --server.address 0.0.0.0
```

### Set Environment Variables (if needed):

In Railway dashboard → Variables:
- `STREAMLIT_SERVER_PORT=$PORT` (usually auto-set)
- Any secrets (like `app_password`) can be set as environment variables

**Cost**: Free tier includes $5/month credit (usually enough for small apps)

---

## Alternative: Render

**Render** is another great option, similar to Heroku but simpler.

### Deploy to Render:

1. **Sign up**: Go to https://render.com/ and sign in with GitHub
2. **New Web Service**: Click "New" → "Web Service"
3. **Connect Repository**: Select your GitHub repository
4. **Configure**:
   - **Name**: `fai-document-generator`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run fai_document_generator.py --server.port $PORT --server.address 0.0.0.0`
5. **Deploy**: Click "Create Web Service"
6. **Get URL**: Render provides a URL like `https://fai-document-generator.onrender.com`

**Cost**: Free tier available (may spin down after inactivity)

---

## Alternative: Fly.io

**Fly.io** is great for global deployment and has a generous free tier.

### Deploy to Fly.io:

1. **Install Fly CLI**: `curl -L https://fly.io/install.sh | sh`
2. **Sign up**: `fly auth signup`
3. **Create app**: `fly launch` (in your project directory)
4. **Configure**: Follow prompts, Fly will detect Python
5. **Deploy**: `fly deploy`

**Cost**: Free tier with generous limits

---

## If You Really Want Vercel

To use Vercel, you'd need to completely rewrite the app:

1. **Frontend**: Convert to Next.js (React) or another frontend framework
2. **Backend**: Create Python serverless functions (API routes) for:
   - CSV processing
   - PDF generation
   - Image handling
3. **File Storage**: Use Vercel Blob or external storage (S3, etc.) for uploaded files
4. **State Management**: Handle session state differently (no Streamlit session state)

**Estimated effort**: 2-3 weeks of development work

**Recommendation**: Stick with Streamlit Cloud or use Railway/Render - they're designed for this use case and much easier.

---

## Quick Comparison

| Platform | Free Tier | Streamlit Support | Ease of Use | Best For |
|----------|-----------|-------------------|-------------|----------|
| **Streamlit Cloud** | ✅ Yes | ✅ Native | ⭐⭐⭐⭐⭐ | Current setup |
| **Railway** | ✅ $5 credit | ✅ Yes | ⭐⭐⭐⭐⭐ | Easy migration |
| **Render** | ✅ Yes | ✅ Yes | ⭐⭐⭐⭐ | Simple deployment |
| **Fly.io** | ✅ Yes | ✅ Yes | ⭐⭐⭐ | Global deployment |
| **Vercel** | ✅ Yes | ❌ No | ⭐ | Static sites only |

---

## Recommendation

**Use Railway** - it's the closest to Vercel's experience but supports Streamlit natively. The migration is simple and it has a great free tier.

Would you like me to set up the Railway deployment files?

