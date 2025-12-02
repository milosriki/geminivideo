#!/bin/bash
# ===========================================
# GEMINIVIDEO FULL DEPLOYMENT SCRIPT
# Run this after logging in to Vercel CLI
# ===========================================

echo "🚀 Starting GeminiVideo Full Deployment..."

# Step 1: Deploy Frontend to Vercel
echo ""
echo "📦 Step 1: Deploying Frontend to Vercel..."
cd /home/user/geminivideo/frontend

# Build if not already built
if [ ! -d "dist" ]; then
    echo "Building frontend..."
    npm install
    npm run build
fi

# Deploy to Vercel
echo "Deploying to Vercel..."
vercel deploy --prod --yes

echo "✅ Frontend deployed!"

# Step 2: Get the deployment URL
echo ""
echo "📝 NEXT STEPS:"
echo ""
echo "1. Copy your Vercel deployment URL"
echo ""
echo "2. Go to Vercel Dashboard → Your Project → Settings → Environment Variables"
echo "   Add these variables:"
echo ""
echo "   VITE_SUPABASE_URL=https://akhirugwpozlxfvtqmvj.supabase.co"
echo "   VITE_SUPABASE_ANON_KEY=sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG"
echo "   VITE_GEMINI_API_KEY=AIzaSyDRynwFYxvHY34mLHXhxmKMVwx2wCyXUwI"
echo "   VITE_FIREBASE_API_KEY=AIzaSyCamMhfOYNAqnKnK-nQ78f1u5o8VDx9IaU"
echo "   VITE_FIREBASE_AUTH_DOMAIN=ptd-fitness-demo.firebaseapp.com"
echo "   VITE_FIREBASE_PROJECT_ID=ptd-fitness-demo"
echo ""
echo "3. Go to Supabase Dashboard → SQL Editor → Run the schema from:"
echo "   /home/user/geminivideo/supabase/SCHEMA.sql"
echo ""
echo "🎉 Done! Your app should be live."
