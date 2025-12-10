# 🚀 Quick Setup: Vercel + Supabase

## ✅ What You Need

Add these 2 environment variables to Vercel:

1. **VITE_SUPABASE_URL** = `https://akhirugwpozlxfvtqmvj.supabase.co`
2. **VITE_SUPABASE_ANON_KEY** = `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG`

---

## 🎯 Fastest Method: Vercel Dashboard

### **Step 1: Go to Vercel**
https://vercel.com/dashboard → Your Project → Settings → Environment Variables

### **Step 2: Add Variables**

Click **"Add New"** for each:

**Variable 1:**
- Key: `VITE_SUPABASE_URL`
- Value: `https://akhirugwpozlxfvtqmvj.supabase.co`
- Environments: ✅ Production ✅ Preview ✅ Development
- Click **"Save"**

**Variable 2:**
- Key: `VITE_SUPABASE_ANON_KEY`
- Value: `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG`
- Environments: ✅ Production ✅ Preview ✅ Development
- Click **"Save"**

### **Step 3: Redeploy**
- Go to **Deployments**
- Click **"Redeploy"** on latest deployment
- Or push a new commit

---

## 🔧 Alternative: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Run the script
./add-vercel-env.sh
```

---

## ✅ Verify

1. Check Vercel Dashboard → Environment Variables
2. Redeploy your project
3. Check browser console - Supabase client should work!

---

**That's it! Your frontend will now connect to Supabase.** 🚀

