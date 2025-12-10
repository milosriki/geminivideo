# 🚀 Add Secrets Now - Quick Guide

## ✅ What You've Provided

- ✅ **SUPABASE_SECRET_KEY**: `sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3`
- ✅ **SUPABASE_SERVICE_ROLE_KEY**: (JWT token provided)
- ✅ **SUPABASE_ACCESS_TOKEN**: `sbp_125c933334f63cbb1dbbe0d77bb6c29afc4ee0a8`

## ⚠️ Still Need

- ❌ **SUPABASE_DB_URL** - Database connection string

---

## Method 1: Manual (Fastest - 1 minute)

### Step 1: Get DB URL

1. Go to: **https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj/settings/database**
2. Scroll to **"Connection string"**
3. Select **"Pooled connection"**
4. Copy the full connection string

### Step 2: Add All Secrets to GitHub

1. Go to: **https://github.com/milosriki/geminivideo/settings/secrets/actions**
2. Click **"New repository secret"** for each:

   **Secret 1:**
   - Name: `SUPABASE_SECRET_KEY`
   - Value: `sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3`
   - Click **"Add secret"**

   **Secret 2:**
   - Name: `SUPABASE_ACCESS_TOKEN`
   - Value: `sbp_125c933334f63cbb1dbbe0d77bb6c29afc4ee0a8`
   - Click **"Add secret"**

   **Secret 3:**
   - Name: `SUPABASE_DB_URL`
   - Value: (paste connection string from Step 1)
   - Click **"Add secret"**

---

## Method 2: Using GitHub CLI (If Installed)

If you have `gh` CLI:

```bash
# Install if needed
brew install gh
gh auth login

# Add secrets
echo "sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3" | gh secret set SUPABASE_SECRET_KEY --repo milosriki/geminivideo
echo "sbp_125c933334f63cbb1dbbe0d77bb6c29afc4ee0a8" | gh secret set SUPABASE_ACCESS_TOKEN --repo milosriki/geminivideo
echo "your_db_connection_string" | gh secret set SUPABASE_DB_URL --repo milosriki/geminivideo
```

---

## ✅ Final Checklist

After adding, you should have **8 secrets total**:

- ✅ SUPABASE_URL
- ✅ SUPABASE_ANON_KEY
- ✅ SUPABASE_SERVICE_ROLE_KEY
- ✅ SUPABASE_PROJECT_REF
- ✅ SUPABASE_KEY (optional)
- ✅ VITE_SUPABASE_URL (optional)
- ✅ **SUPABASE_SECRET_KEY** (newly added)
- ✅ **SUPABASE_ACCESS_TOKEN** (newly added)
- ✅ **SUPABASE_DB_URL** (need to add)

---

## 🔗 Quick Links

- **Database Settings**: https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj/settings/database
- **GitHub Secrets**: https://github.com/milosriki/geminivideo/settings/secrets/actions

---

**Once all 3 are added, GitHub Actions will auto-deploy!** 🚀

