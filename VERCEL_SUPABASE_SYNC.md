# 🔄 Vercel + Supabase Sync Guide

## 📊 Current Setup

You have Vercel integration connected:
- **Connection:** `ptd marketing elite ai → geminivideo`
- **Environments:** Production, Preview, Development (all enabled)
- **Prefix:** `NEXT_PUBLIC_`

---

## 🎯 What Gets Synced

Supabase automatically syncs these environment variables to Vercel:

### **Automatically Synced (with NEXT_PUBLIC_ prefix):**

1. **NEXT_PUBLIC_SUPABASE_URL**
   - Value: `https://akhirugwpozlxfvtqmvj.supabase.co`
   - Used by: Frontend (React/Next.js)

2. **NEXT_PUBLIC_SUPABASE_ANON_KEY**
   - Value: `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG`
   - Used by: Frontend (public API access)

### **What's NOT Synced (Server-side only):**

These should NOT be synced to Vercel (they're server-side only):
- ❌ `SUPABASE_SERVICE_ROLE_KEY` (never expose to frontend!)
- ❌ `SUPABASE_DB_URL` (database connection - server only)
- ❌ `SUPABASE_ACCESS_TOKEN` (for CLI/deployment only)

---

## ✅ What You Need to Add

### **1. Check Vercel Environment Variables**

Go to: **Vercel Dashboard → Your Project → Settings → Environment Variables**

Verify these are synced (they should be auto-synced):
- ✅ `NEXT_PUBLIC_SUPABASE_URL`
- ✅ `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### **2. Add Additional Variables (if needed)**

If your frontend needs other variables, add them in **Supabase → Edge Functions → Secrets**:

**For Frontend (with NEXT_PUBLIC_ prefix):**
- `NEXT_PUBLIC_API_URL` (if you have a custom API)
- `NEXT_PUBLIC_ENVIRONMENT` (production/preview/development)

**For Server-side (Vercel Serverless Functions):**
Add these in **Vercel Dashboard** (NOT in Supabase, as they won't sync):
- `SUPABASE_SERVICE_ROLE_KEY` (server-side only!)
- `DATABASE_URL` (if needed for server functions)

---

## 🔧 Configuration

### **Current Settings (from your dashboard):**

✅ **Production:** Synced  
✅ **Preview:** Synced  
✅ **Development:** Synced  
✅ **Prefix:** `NEXT_PUBLIC_`

### **How It Works:**

1. **Supabase → Vercel Sync:**
   - Supabase automatically pushes env vars to Vercel
   - Uses the `NEXT_PUBLIC_` prefix for public variables
   - Syncs to all enabled environments

2. **Vercel Deployment:**
   - Vercel uses these variables during build and runtime
   - Frontend can access `process.env.NEXT_PUBLIC_*`
   - Server functions can access all env vars

---

## 📝 Step-by-Step Setup

### **Step 1: Verify Supabase → Vercel Sync**

1. Go to: **Supabase Dashboard → Settings → Integrations → Vercel**
2. Verify connection: `ptd marketing elite ai → geminivideo`
3. Check all environments are enabled (Production, Preview, Development)

### **Step 2: Check Vercel Environment Variables**

1. Go to: **Vercel Dashboard → geminivideo → Settings → Environment Variables**
2. You should see:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### **Step 3: Add Server-Side Variables (if needed)**

If you have Vercel Serverless Functions that need server-side secrets:

1. Go to: **Vercel Dashboard → geminivideo → Settings → Environment Variables**
2. Add manually (these DON'T sync from Supabase):
   - `SUPABASE_SERVICE_ROLE_KEY` = `sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3`
   - `DATABASE_URL` = (your database connection string)

**⚠️ Important:** Only add server-side secrets in Vercel, NOT in Supabase Edge Function Secrets (those are for Edge Functions only).

---

## 🎯 Environment Variable Strategy

### **Frontend (React/Next.js) - Auto-synced:**
```typescript
// These are automatically synced from Supabase
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
```

### **Server-side (Vercel Functions) - Manual:**
```typescript
// Add these manually in Vercel Dashboard
const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const dbUrl = process.env.DATABASE_URL;
```

### **Edge Functions (Supabase) - Separate:**
```typescript
// These are in Supabase Edge Function Secrets
const supabaseUrl = Deno.env.get("SUPABASE_URL");
const supabaseKey = Deno.env.get("SUPABASE_ANON_KEY");
```

---

## ✅ Checklist

- [x] Vercel integration connected
- [x] All environments enabled (Production, Preview, Development)
- [x] Prefix set to `NEXT_PUBLIC_`
- [ ] Verify `NEXT_PUBLIC_SUPABASE_URL` in Vercel
- [ ] Verify `NEXT_PUBLIC_SUPABASE_ANON_KEY` in Vercel
- [ ] Add server-side secrets in Vercel (if needed)

---

## 🔄 How Sync Works

1. **Supabase → Vercel:**
   - Supabase pushes env vars to Vercel automatically
   - Only variables with `NEXT_PUBLIC_` prefix are synced
   - Syncs to all enabled environments

2. **Vercel Deployment:**
   - Vercel uses these variables during build
   - Frontend can access `NEXT_PUBLIC_*` variables
   - Server functions can access all variables

3. **Manual Variables:**
   - Server-side secrets must be added manually in Vercel
   - They don't sync from Supabase (by design, for security)

---

## 🚨 Important Notes

1. **Never expose service_role key to frontend:**
   - ❌ Don't add `SUPABASE_SERVICE_ROLE_KEY` with `NEXT_PUBLIC_` prefix
   - ✅ Only use it in server-side functions

2. **Prefix matters:**
   - Variables with `NEXT_PUBLIC_` prefix are exposed to browser
   - Variables without prefix are server-only

3. **Three separate systems:**
   - **Supabase Edge Functions:** Use Supabase Edge Function Secrets
   - **Vercel Frontend:** Use auto-synced `NEXT_PUBLIC_*` variables
   - **Vercel Server Functions:** Use manually added Vercel env vars

---

## 📚 Related

- **GitHub Secrets:** See `GITHUB_SECRETS_SETUP.md`
- **Edge Function Secrets:** See `EDGE_FUNCTION_SECRETS.md`
- **Environment Setup:** See `ENV_SETUP.md`

---

**Your Vercel integration is set up! Just verify the synced variables in Vercel Dashboard.** 🚀

