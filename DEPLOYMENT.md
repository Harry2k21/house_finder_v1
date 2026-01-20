# Netlify Deployment Guide

This guide will help you deploy the House Finder application to Netlify.

## Prerequisites

- A GitHub/GitLab/Bitbucket account with your code repository
- A Netlify account (free tier is sufficient)
- Environment variables ready (see below)

## Step-by-Step Deployment

### 1. Prepare Your Repository

Make sure your repository has:
- ✅ `netlify/functions/` directory with all function files
- ✅ `public/` directory with static files (index.html, style.css, script.js, etc.)
- ✅ `netlify.toml` configuration file
- ✅ `requirements.txt` with Python dependencies

### 2. Push to Git

```bash
git add .
git commit -m "Prepare for Netlify deployment"
git push
```

### 3. Connect to Netlify

1. Go to [Netlify Dashboard](https://app.netlify.com)
2. Click **"New site from Git"**
3. Choose your Git provider (GitHub/GitLab/Bitbucket)
4. Select your repository

### 4. Configure Build Settings

Netlify should automatically detect the settings from `netlify.toml`, but verify:
- **Build command:** Leave empty (or `echo "No build step required"`)
- **Publish directory:** `public`
- **Functions directory:** `netlify/functions`

### 5. Set Environment Variables

Go to **Site settings > Environment variables** and add:

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing secret (min 32 chars) | `your-random-secret-key-here-min-32-chars` |
| `GROQ_API_KEY` | Groq AI API key | `gsk_...` |
| `TURSO_AUTH_TOKEN` | Turso database auth token | `eyJ...` |
| `TURSO_DATABASE_URL` | Turso database URL | `libsql://...` |

### 6. Deploy

Click **"Deploy site"**. Netlify will:
1. Install Python dependencies from `requirements.txt`
2. Build your site (static files from `public/`)
3. Set up serverless functions from `netlify/functions/`

### 7. Initialize Database (One-Time)

After deployment, you need to initialize the database tables. You have two options:

**Option A: Via Netlify CLI**
```bash
npm install -g netlify-cli
netlify login
netlify functions:invoke init_db --no-identity
```

**Option B: Create a temporary endpoint**
Add this to one of your functions temporarily to run the init:
```python
# Add to any function temporarily
from init_db import init_db
init_db()
```

### 8. Test Your Deployment

Visit your Netlify site URL. The frontend should:
- ✅ Load correctly
- ✅ Connect to Netlify Functions (automatically via `/netlify/functions/...`)
- ✅ Allow user registration/login
- ✅ Function properly with all features

## Function Endpoints

After deployment, your functions will be available at:
- `/.netlify/functions/register` - User registration
- `/.netlify/functions/login` - User authentication
- `/.netlify/functions/verify_token` - Token verification
- `/.netlify/functions/scrape` - Property scraping
- `/.netlify/functions/history` - Search history
- `/.netlify/functions/requirements` - Requirements management
- `/.netlify/functions/shortlist` - Shortlist management
- `/.netlify/functions/geocode` - Geocoding service
- `/.netlify/functions/ask_expert` - AI expert chat

## Troubleshooting

### Functions not working

1. Check Netlify Function logs: **Site settings > Functions > Logs**
2. Verify environment variables are set correctly
3. Check that `requirements.txt` includes all dependencies
4. Ensure function files have correct `handler(event, context)` signature

### CORS errors

The functions already include CORS headers. If you see CORS errors:
- Check that the function is returning proper headers
- Verify the frontend is making requests to the correct endpoints

### Database connection errors

1. Verify `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` are correct
2. Check that database tables are initialized
3. Test database connection manually

### Authentication issues

1. Verify `SECRET_KEY` is set and is at least 32 characters
2. Check that JWT tokens are being generated correctly
3. Ensure tokens are being sent in request headers

## Local Testing

To test Netlify Functions locally:

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Run local development server
netlify dev
```

This will:
- Start a local server for static files
- Run functions locally
- Simulate Netlify environment

## Updating Your Site

Simply push changes to your Git repository, and Netlify will automatically redeploy!

```bash
git add .
git commit -m "Update feature"
git push
```

## Additional Resources

- [Netlify Functions Documentation](https://docs.netlify.com/functions/overview/)
- [Netlify Python Functions](https://docs.netlify.com/functions/create-functions/python/)
- [Netlify Environment Variables](https://docs.netlify.com/environment-variables/overview/)

