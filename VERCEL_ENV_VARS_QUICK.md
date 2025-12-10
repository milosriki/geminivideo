# ⚡ Vercel Environment Variables - Quick Setup

## 🎯 What You Need to Add

**Go to:** https://vercel.com/dashboard → Your Project → Settings → Environment Variables

### **Add These 2 Variables:**

#### **1. VITE_SUPABASE_URL**
```
Name:  VITE_SUPABASE_URL
Value: https://akhirugwpozlxfvtqmvj.supabase.co
```

#### **2. VITE_SUPABASE_ANON_KEY**
```
Name:  VITE_SUPABASE_ANON_KEY
Value: sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG
```

**Important:** Add to **ALL environments** (Production, Preview, Development)

---

## 📝 Step-by-Step

1. **Go to Vercel Dashboard**
   - https://vercel.com/dashboard

2. **Select Your Project**
   - Click on `geminivideo` project

3. **Navigate to Settings**
   - Click **Settings** tab
   - Click **Environment Variables** in left sidebar

4. **Add First Variable**
   - Click **"Add New"**
   - **Key:** `VITE_SUPABASE_URL`
   - **Value:** `https://akhirugwpozlxfvtqmvj.supabase.co`
   - **Environment:** Select all (Production, Preview, Development)
   - Click **"Save"**

5. **Add Second Variable**
   - Click **"Add New"** again
   - **Key:** `VITE_SUPABASE_ANON_KEY`
   - **Value:** `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG`
   - **Environment:** Select all (Production, Preview, Development)
   - Click **"Save"**

6. **Redeploy**
   - Go to **Deployments** tab
   - Click **"..."** on latest deployment
   - Click **"Redeploy"**
   - Or just push a new commit to trigger auto-deploy

---

## ✅ Verification

After adding, you should see:
- ✅ `VITE_SUPABASE_URL` in the list
- ✅ `VITE_SUPABASE_ANON_KEY` in the list
- ✅ Both marked for all environments

---

## 🚀 That's It!

Once added and redeployed, your frontend will connect to Supabase automatically!

**Time needed: ~5 minutes**

