# DEPLOY BACKEND TO CLOUD RUN

## Option 1: One-Click Deploy (Recommended)

Run these commands in Google Cloud Shell:

```bash
# 1. Clone and navigate
git clone https://github.com/milosriki/geminivideo
cd geminivideo/services/titan-core

# 2. Set your project
gcloud config set project YOUR_PROJECT_ID

# 3. Deploy to Cloud Run
gcloud run deploy titan-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars "GEMINI_API_KEY=$GEMINI_API_KEY" \
  --set-env-vars "OPENAI_API_KEY=$OPENAI_API_KEY" \
  --set-env-vars "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" \
  --set-env-vars "SUPABASE_URL=$SUPABASE_URL" \
  --set-env-vars "SUPABASE_KEY=$SUPABASE_KEY" \
  --set-env-vars "REDIS_URL=$REDIS_URL"

# 4. Copy the URL it gives you (like: https://titan-api-xxxxx.run.app)
```

## Option 2: From Google Cloud Console

1. Go to: https://console.cloud.google.com/run
2. Click **"Create Service"**
3. Select **"Continuously deploy from a repository"**
4. Connect GitHub → Select `geminivideo` repo
5. Set source: `services/titan-core`
6. Set these environment variables from your .env.production file:
   - GEMINI_API_KEY
   - OPENAI_API_KEY
   - ANTHROPIC_API_KEY
   - SUPABASE_URL
   - SUPABASE_KEY
   - REDIS_URL

## After Deploy

Update your Vercel frontend with the Cloud Run URL:

```bash
vercel env add VITE_API_BASE_URL production
# Enter: https://titan-api-xxxxx.run.app
vercel deploy --prod
```

## What Gets Deployed

- FastAPI server with all endpoints
- AI Council (Gemini, Claude, GPT-4o)
- Video processing pipeline
- WebSocket for real-time updates
- ROAS prediction engine
