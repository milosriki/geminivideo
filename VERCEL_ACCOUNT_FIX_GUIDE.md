# 🔧 Vercel Account Connection Fix Guide

## 🚨 Problem Identified

The repository is currently connected to a **wrong Vercel account**. Documentation and configurations reference:
- ❌ `https://geminivideo-milos-projects-d46729ec.vercel.app`

This appears to be a **personal Vercel account** (`milos-projects-d46729ec`) instead of the intended organization or team account.

---

## 📋 Impact Analysis

### Files/Services Affected:
1. **Documentation** (Updated ✅)
   - ✅ `VERCEL_SUPABASE_CONNECTION.md` - Cleaned up
   - ✅ `SUPABASE_URL_CONFIG_CHECK.md` - Made generic
   
2. **Service Code** (Review Required)
   - ⚠️ `services/google-ads/src/index.ts` - Uses generic `geminivideo.vercel.app` (OK)
   - ⚠️ `services/tiktok-ads/src/index.ts` - Uses generic `geminivideo.vercel.app` (OK)
   - ⚠️ `services/meta-publisher/src/index.ts` - Uses generic `geminivideo.vercel.app` (OK)

3. **Configuration Scripts**
   - ⚠️ `add-vercel-env.sh` - Uses Vercel CLI (will use current login)

4. **Missing Configuration**
   - ❌ No `.vercel` directory (project not linked locally)
   - ❌ No explicit Vercel project configuration in repository

---

## ✅ Step-by-Step Fix Process

### Step 1: Identify the Correct Vercel Account

**Questions to Answer:**
1. What is the correct Vercel organization/team name?
2. Should this project be under:
   - Personal account?
   - Team/Organization account?
   - Different account entirely?

**Action Required:** Confirm with the team which Vercel account should host this project.

---

### Step 2: Disconnect from Wrong Account (If Currently Connected)

If the project is already deployed to the wrong Vercel account:

#### Option A: Via Vercel Dashboard
1. Log in to the **wrong** Vercel account
2. Go to: **Dashboard → Projects**
3. Find `geminivideo` project
4. Click **Settings** → **General**
5. Scroll down and click **"Delete Project"** (or keep it as backup)
6. Confirm deletion

#### Option B: Via Vercel CLI
```bash
# Login to the wrong account first
vercel login

# List projects
vercel list

# Remove the project (if you want to delete it)
vercel remove geminivideo
```

---

### Step 3: Connect to Correct Vercel Account

#### Option A: Via Vercel Dashboard (Recommended)

1. **Login to Correct Account:**
   - Go to https://vercel.com
   - Login with the **correct** account
   - If using team/org, switch to it in the dashboard

2. **Import Project:**
   - Click **"Add New..."** → **"Project"**
   - Select **"Import Git Repository"**
   - Authorize GitHub if needed
   - Select `milosriki/geminivideo` repository
   - Click **"Import"**

3. **Configure Project:**
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite (should auto-detect)
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - Click **"Deploy"**

4. **Add Environment Variables:**
   Go to: **Settings → Environment Variables**
   
   Add these for **all environments** (Production, Preview, Development):
   ```
   VITE_SUPABASE_URL=https://akhirugwpozlxfvtqmvj.supabase.co
   VITE_SUPABASE_ANON_KEY=sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG
   VITE_API_URL=<your-backend-api-url>
   ```

5. **Get Your New Project URL:**
   - After deployment completes, note the URL
   - It will be something like: `https://geminivideo.vercel.app` or `https://geminivideo-<team>.vercel.app`

#### Option B: Via Vercel CLI

```bash
# Install Vercel CLI (if not installed)
npm i -g vercel

# Login to the CORRECT account
vercel login
# Follow prompts and authenticate with the correct credentials

# Navigate to frontend directory
cd frontend

# Link to a new Vercel project
vercel link
# Select: Create a new project
# Project name: geminivideo
# Follow prompts

# Add environment variables
vercel env add VITE_SUPABASE_URL production
# Paste: https://akhirugwpozlxfvtqmvj.supabase.co

vercel env add VITE_SUPABASE_ANON_KEY production
# Paste: sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG

# Repeat for preview and development if needed
vercel env add VITE_SUPABASE_URL preview
vercel env add VITE_SUPABASE_ANON_KEY preview

# Deploy
vercel --prod
```

---

### Step 4: Update Supabase Configuration

Once you have your **new Vercel URL**, update Supabase:

1. **Go to Supabase Dashboard:**
   https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj

2. **Update Authentication URLs:**
   - Navigate to: **Authentication → URL Configuration**
   
3. **Update Site URL:**
   ```
   https://<your-new-vercel-url>.vercel.app
   ```

4. **Update Redirect URLs:**
   Add these patterns:
   ```
   https://<your-project>.vercel.app
   https://<your-project>.vercel.app/**
   https://<your-project>-*.vercel.app
   https://<your-project>-*.vercel.app/**
   ```
   
   Replace `<your-project>` with your actual Vercel project name.

5. **Save Changes**

---

### Step 5: Update Vercel + Supabase Integration (Optional)

For automatic environment variable syncing:

1. **Go to Supabase:**
   https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj/settings/integrations

2. **Connect Vercel Integration:**
   - Find **"Vercel"** integration
   - If already connected to wrong account:
     - Click **"Disconnect"**
   - Click **"Connect"** or **"Reconnect"**
   - Authorize with the **correct** Vercel account
   - Select your project: `geminivideo`
   - Choose environments: Production, Preview, Development
   - Choose prefix: `NEXT_PUBLIC_` (or `VITE_` if available)

3. **Verify Sync:**
   - Go to Vercel Dashboard → Settings → Environment Variables
   - You should see `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - Note: You may need to manually add `VITE_*` versions for Vite

---

### Step 6: Update Service CORS (If Needed)

If you get a custom Vercel domain (not `geminivideo.vercel.app`), update CORS in these files:

1. **File:** `services/google-ads/src/index.ts`
   - Add your new Vercel URL to `ALLOWED_ORIGINS`

2. **File:** `services/tiktok-ads/src/index.ts`
   - Add your new Vercel URL to `ALLOWED_ORIGINS`

3. **File:** `services/meta-publisher/src/index.ts`
   - Add your new Vercel URL to `ALLOWED_ORIGINS`

**Or better:** Set `ALLOWED_ORIGINS` environment variable in your backend services:
```bash
ALLOWED_ORIGINS=http://localhost:3000,https://your-new-url.vercel.app
```

---

### Step 7: Test the Connection

1. **Visit Your Vercel URL:**
   - Go to your new deployment URL
   - Open browser DevTools (F12)

2. **Check Console:**
   - Look for any errors related to Supabase connection
   - You should see successful API calls

3. **Test Authentication:**
   - Try to sign up or log in
   - Verify it connects to Supabase correctly

4. **Test Backend API:**
   - Try features that call your backend services
   - Verify CORS is working

---

## 🔍 Verification Checklist

- [ ] Correct Vercel account identified
- [ ] Old deployment removed (if needed)
- [ ] New project created in correct Vercel account
- [ ] Environment variables added to Vercel
- [ ] New deployment successful
- [ ] New Vercel URL obtained
- [ ] Supabase URLs updated
- [ ] Vercel + Supabase integration reconnected (optional)
- [ ] Service CORS updated (if needed)
- [ ] Frontend loads successfully
- [ ] Authentication works
- [ ] Backend API calls work

---

## 📝 What Was Changed in This PR

### Files Updated:
1. ✅ `VERCEL_SUPABASE_CONNECTION.md` - Removed hardcoded account-specific URL
2. ✅ `SUPABASE_URL_CONFIG_CHECK.md` - Made configuration generic
3. ✅ `VERCEL_ACCOUNT_FIX_GUIDE.md` - Created this comprehensive guide (NEW)

### Files Reviewed (No Changes Needed):
- ✅ `services/google-ads/src/index.ts` - Already uses generic URL
- ✅ `services/tiktok-ads/src/index.ts` - Already uses generic URL
- ✅ `services/meta-publisher/src/index.ts` - Already uses generic URL
- ✅ `add-vercel-env.sh` - Works with any account (uses current CLI login)

---

## 🚨 Important Notes

### Security Considerations:
1. **Never commit `.vercel` directory** to git (already in `.gitignore`)
2. **Never commit environment variables** with real values
3. **Use Vercel Dashboard or CLI** to manage secrets
4. **Keep service role keys** out of frontend environment variables

### Account Considerations:
1. **Team/Org accounts** provide:
   - Better collaboration
   - More deployment slots
   - Team billing
   - Access control

2. **Personal accounts** are suitable for:
   - Solo projects
   - Development/testing
   - Proof of concepts

### Cost Considerations:
1. **Hobby Plan (Free):**
   - 100GB bandwidth
   - Serverless function execution
   - Good for development

2. **Pro Plan ($20/month):**
   - Unlimited team members
   - More bandwidth
   - Production use

---

## 🔗 Useful Links

- **Vercel Dashboard:** https://vercel.com/dashboard
- **Supabase Dashboard:** https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj
- **Vercel CLI Docs:** https://vercel.com/docs/cli
- **Vercel Environment Variables:** https://vercel.com/docs/concepts/projects/environment-variables

---

## 🆘 Need Help?

If you encounter issues:

1. **Check Vercel Deployment Logs:**
   - Vercel Dashboard → Deployments → Click on deployment → View logs

2. **Check Browser Console:**
   - F12 → Console tab
   - Look for CORS or network errors

3. **Verify Environment Variables:**
   - Vercel Dashboard → Settings → Environment Variables
   - Ensure all required variables are set

4. **Test Backend Connectivity:**
   ```bash
   curl https://your-backend-api.run.app/health
   ```

5. **Contact Support:**
   - Vercel Support: https://vercel.com/support
   - Supabase Support: https://supabase.com/support

---

## ✅ Next Steps

1. **Determine the correct Vercel account** (personal vs. team/org)
2. **Follow steps above** to reconnect to correct account
3. **Update this document** with actual URLs and account details after migration
4. **Test thoroughly** before considering the migration complete
5. **Update team members** on the new deployment URLs

---

**Once reconnected to the correct account, all Vercel URLs should be consistent!** 🚀
