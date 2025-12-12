# 🔧 Fix: Duplicate Vercel Projects Issue

## 🚨 Problem Identified

You have **TWO Vercel projects** from the same GitHub repository:

1. **"frontend"** → `frontend-amber-three-12.vercel.app` ✅ (probably working)
2. **"geminivideo"** → `geminivideo.vercel.app` ❌ (showing 404)

**Why this happened:**
- The "geminivideo" project is trying to build from the **root directory** (which has no buildable frontend)
- The "frontend" project is probably correctly configured with **Root Directory = `frontend`**

---

## ✅ Solution: Consolidate to ONE Project

### Step 1: Fix the "geminivideo" Project Configuration

1. **Go to Vercel Dashboard:**
   - https://vercel.com/dashboard
   - Click on **"geminivideo"** project

2. **Update Root Directory:**
   - Go to: **Settings → General**
   - Scroll to **"Root Directory"**
   - Click **"Edit"**
   - Change from `./` to `frontend`
   - Click **"Save"**

3. **Verify Build Settings:**
   - **Framework Preset:** Should be "Vite" (auto-detected)
   - **Build Command:** `npm run build` (from `frontend/vercel.json`)
   - **Output Directory:** `dist` (from `frontend/vercel.json`)
   - **Install Command:** `npm install`

4. **Add Environment Variables:**
   - Go to: **Settings → Environment Variables**
   - Add these for **all environments** (Production, Preview, Development):
     
     ```
     VITE_SUPABASE_URL = https://akhirugwpozlxfvtqmvj.supabase.co
     VITE_SUPABASE_ANON_KEY = sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG
     ```

5. **Redeploy:**
   - Go to: **Deployments**
   - Click **"Redeploy"** on the latest deployment
   - Or push a new commit to trigger deployment

---

### Step 2: Delete the "frontend" Project (Optional)

Once "geminivideo" is working:

1. **Go to "frontend" project:**
   - Vercel Dashboard → Click "frontend" project

2. **Delete it:**
   - Go to: **Settings → General**
   - Scroll to bottom
   - Click **"Delete Project"**
   - Type project name to confirm
   - Click **"Delete"**

**OR** keep it as a backup and just stop using it.

---

## 🎯 Quick Fix (5 minutes)

### Option A: Fix "geminivideo" Project (Recommended)

1. Vercel Dashboard → **geminivideo** project
2. Settings → General → **Root Directory** → Change to `frontend`
3. Settings → Environment Variables → Add `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`
4. Deployments → **Redeploy**

### Option B: Use "frontend" Project (If it's already working)

1. Vercel Dashboard → **frontend** project
2. Settings → Domains → Add custom domain `geminivideo.vercel.app` (if you want)
3. Delete the "geminivideo" project

---

## 📋 Verification Checklist

After fixing:

- [ ] "geminivideo" project has Root Directory = `frontend`
- [ ] Environment variables are set (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY)
- [ ] Latest deployment is successful (green checkmark)
- [ ] `geminivideo.vercel.app` loads without 404
- [ ] Frontend routes work (try `/login`, `/dashboard`)
- [ ] Supabase connection works (check browser console)

---

## 🔍 Why This Happened

**Root Cause:**
- When you import a GitHub repo, Vercel defaults to root directory (`./`)
- Your frontend code is in `frontend/` subdirectory
- Without setting Root Directory, Vercel tries to build from root → finds no buildable code → 404

**Solution:**
- Set Root Directory to `frontend` so Vercel knows where your buildable code is

---

## 💡 Best Practice Going Forward

**One Project Per Repository:**
- ✅ One Vercel project for `geminivideo` repo
- ✅ Root Directory = `frontend`
- ✅ All deployments go to one URL

**If you need multiple deployments:**
- Use **Preview Deployments** (automatic for each PR)
- Use **Branch Deployments** (for different branches)
- Don't create separate projects

---

## 🆘 Still Getting 404?

1. **Check Build Logs:**
   - Vercel Dashboard → Deployments → Click deployment → View logs
   - Look for build errors

2. **Verify vercel.json:**
   - Should be in `frontend/vercel.json`
   - Should have SPA rewrite rule (already fixed ✅)

3. **Check Environment Variables:**
   - Make sure they're set for the correct environment
   - Redeploy after adding variables

4. **Test Locally:**
   ```bash
   cd frontend
   npm install
   npm run build
   npm run preview
   ```
   - If this works, Vercel should work too

---

**After fixing, you'll have ONE working project instead of two!** 🚀

