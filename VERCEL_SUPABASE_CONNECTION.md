# 🔗 Vercel + Supabase Connection Setup

## 📋 Current Status

**Frontend Framework:** Vite (React)  
**Supabase Client:** Already configured in `frontend/src/utils/supabase.ts`  
**Vercel Config:** `frontend/vercel.json` exists

---

## 🎯 Required Environment Variables

Your frontend needs these (Vite uses `VITE_` prefix):

1. **VITE_SUPABASE_URL**
   - Value: `https://akhirugwpozlxfvtqmvj.supabase.co`
   - Used by: Frontend Supabase client

2. **VITE_SUPABASE_ANON_KEY**
   - Value: `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG` (or legacy anon key)
   - Used by: Frontend Supabase client

---

## 🔧 Setup Methods

### **Method 1: Vercel Dashboard (Recommended)**

1. Go to: **Vercel Dashboard → Your Project → Settings → Environment Variables**

2. Add these variables for **all environments** (Production, Preview, Development):

   **Variable 1:**
   - Name: `VITE_SUPABASE_URL`
   - Value: `https://akhirugwpozlxfvtqmvj.supabase.co`
   - Environment: ✅ Production ✅ Preview ✅ Development

   **Variable 2:**
   - Name: `VITE_SUPABASE_ANON_KEY`
   - Value: `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG`
   - Environment: ✅ Production ✅ Preview ✅ Development

3. Click **"Save"**

4. **Redeploy** your project (Vercel will use new env vars on next deployment)

---

### **Method 2: Supabase → Vercel Integration (Auto-sync)**

If you have Supabase integration connected:

1. Go to: **Supabase Dashboard → Settings → Integrations → Vercel**

2. **Connect Vercel** (if not already connected):
   - Click **"Connect Vercel"**
   - Authorize Supabase to access Vercel
   - Select your project: `geminivideo`

3. **Configure Sync:**
   - Enable: ✅ Production ✅ Preview ✅ Development
   - **Note:** Supabase syncs `NEXT_PUBLIC_*` by default, but you need `VITE_*`
   - You may need to add these manually in Vercel (see Method 1)

---

### **Method 3: Vercel CLI**

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Add environment variables
vercel env add VITE_SUPABASE_URL production
# Paste: https://akhirugwpozlxfvtqmvj.supabase.co

vercel env add VITE_SUPABASE_ANON_KEY production
# Paste: sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG

# Repeat for preview and development
vercel env add VITE_SUPABASE_URL preview
vercel env add VITE_SUPABASE_ANON_KEY preview

vercel env add VITE_SUPABASE_URL development
vercel env add VITE_SUPABASE_ANON_KEY development
```

---

## ✅ Verify Setup

### **1. Check Vercel Environment Variables**

Go to: **Vercel Dashboard → Your Project → Settings → Environment Variables**

You should see:
- ✅ `VITE_SUPABASE_URL`
- ✅ `VITE_SUPABASE_ANON_KEY`

### **2. Test in Your Code**

Your `frontend/src/utils/supabase.ts` should work:

```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

// This should work now!
export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

### **3. Redeploy**

After adding env vars, trigger a new deployment:
- Push a commit, or
- Go to **Vercel Dashboard → Deployments → Redeploy**

---

## 🔐 Additional Variables (Optional)

If your frontend needs other variables:

**API Gateway:**
- `VITE_API_URL` - Your backend API URL
- `VITE_API_BASE_URL` - Alternative API URL

**Environment:**
- `VITE_ENVIRONMENT` - `production`, `preview`, or `development`

**Add these the same way in Vercel Dashboard.**

---

## 🚨 Important Notes

### **Prefix Difference:**
- **Next.js:** Uses `NEXT_PUBLIC_*` prefix
- **Vite:** Uses `VITE_*` prefix
- **Your project:** Uses Vite, so use `VITE_*`

### **Security:**
- ✅ `VITE_SUPABASE_ANON_KEY` is safe for frontend (public)
- ❌ Never expose `SUPABASE_SERVICE_ROLE_KEY` to frontend
- ❌ Never expose `SUPABASE_DB_URL` to frontend

### **Server-side Functions:**
If you have Vercel Serverless Functions (in `api/` folder), they can access:
- All `VITE_*` variables (but shouldn't use them)
- Server-only variables (add manually without `VITE_` prefix)

---

## 📋 Quick Checklist

- [ ] Add `VITE_SUPABASE_URL` to Vercel (all environments)
- [ ] Add `VITE_SUPABASE_ANON_KEY` to Vercel (all environments)
- [ ] Redeploy project
- [ ] Verify Supabase client works in browser console
- [ ] Test authentication flow

---

## 🔗 Quick Links

- **Vercel Dashboard:** https://vercel.com/dashboard
- **Supabase Dashboard:** https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj
- **Your Vercel Project:** Check your Vercel dashboard for the correct URL

---

**Once env vars are added, your frontend will connect to Supabase automatically!** 🚀

