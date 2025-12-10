# 🔐 Final Secret Needed: SUPABASE_DB_URL

## ✅ What's Already Added

1. ✅ `SUPABASE_SECRET_KEY` - Added to GitHub
2. ✅ `SUPABASE_ACCESS_TOKEN` - Added to GitHub

## ⚠️ Still Need

3. ❌ `SUPABASE_DB_URL` - Database connection string

---

## 🔍 Connection String Info

I've retrieved from Supabase:
- **Project Ref**: `akhirugwpozlxfvtqmvj`
- **Region**: `ap-southeast-1`
- **Host**: `db.akhirugwpozlxfvtqmvj.supabase.co`

**Connection String Format:**
```
postgres://postgres.akhirugwpozlxfvtqmvj:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

---

## 📋 How to Get It

### Option 1: From Supabase Dashboard (Easiest)

1. Go to: **https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj/settings/database**
2. Scroll to **"Connection string"**
3. Select **"Transaction mode"** (port 6543) - recommended for serverless
4. Copy the **full connection string** (includes password)

### Option 2: If You Know the Password

Replace `[YOUR-PASSWORD]` in the format above with your actual database password.

---

## 🚀 Add to GitHub

Once you have the full connection string:

### Method 1: I'll Add It (If You Provide)

Just paste the connection string here and I'll add it automatically.

### Method 2: Manual

1. Go to: **https://github.com/milosriki/geminivideo/settings/secrets/actions**
2. Click **"New repository secret"**
3. Name: `SUPABASE_DB_URL`
4. Value: (paste the full connection string)
5. Click **"Add secret"**

---

## ✅ After Adding

Once `SUPABASE_DB_URL` is added:
- ✅ All 3 required secrets will be complete
- ✅ GitHub Actions will auto-deploy on push
- ✅ Migrations will apply automatically
- ✅ Edge Functions will deploy automatically

---

**Quick Link:** https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj/settings/database

