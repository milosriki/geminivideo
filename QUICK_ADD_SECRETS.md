# 🚀 Quick Guide: Add Missing GitHub Secrets

## What You Need (2 secrets)

1. **SUPABASE_DB_URL** - Database connection string
2. **SUPABASE_ACCESS_TOKEN** - Personal access token

---

## Method 1: Manual (Easiest - 2 minutes)

### Step 1: Get SUPABASE_DB_URL

1. Go to: **https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj/settings/database**
2. Scroll to **"Connection string"**
3. Select **"Pooled connection"** (recommended)
4. Copy the **full connection string**
   - Format: `postgresql://postgres.akhirugwpozlxfvtqmvj:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`

### Step 2: Get SUPABASE_ACCESS_TOKEN

1. Go to: **https://supabase.com/dashboard/account/tokens**
2. Click **"Generate new token"**
3. Name: `GitHub Actions`
4. Copy the token (starts with `sbp_...`)

### Step 3: Add to GitHub

1. Go to: **https://github.com/milosriki/geminivideo/settings/secrets/actions**
2. Click **"New repository secret"**
3. Add each secret:

   **Secret 1:**
   - Name: `SUPABASE_DB_URL`
   - Value: (paste connection string from Step 1)
   - Click **"Add secret"**

   **Secret 2:**
   - Name: `SUPABASE_ACCESS_TOKEN`
   - Value: (paste token from Step 2)
   - Click **"Add secret"**

---

## Method 2: Using Script (If GitHub CLI installed)

If you have GitHub CLI installed:

```bash
# Install GitHub CLI (if not installed)
brew install gh

# Authenticate
gh auth login

# Run the script
./add-github-secrets-simple.sh
```

---

## Method 3: Using GitHub CLI Directly

If you have `gh` CLI installed and authenticated:

```bash
# Add SUPABASE_DB_URL
echo "your_db_connection_string" | gh secret set SUPABASE_DB_URL --repo milosriki/geminivideo

# Add SUPABASE_ACCESS_TOKEN
echo "your_access_token" | gh secret set SUPABASE_ACCESS_TOKEN --repo milosriki/geminivideo
```

---

## ✅ Verify

After adding both secrets:

1. Go to: **https://github.com/milosriki/geminivideo/settings/secrets/actions**
2. You should see **8 secrets total**:
   - ✅ SUPABASE_URL
   - ✅ SUPABASE_ANON_KEY
   - ✅ SUPABASE_SERVICE_ROLE_KEY
   - ✅ SUPABASE_PROJECT_REF
   - ✅ SUPABASE_KEY (optional/legacy)
   - ✅ VITE_SUPABASE_URL (optional)
   - ✅ **SUPABASE_DB_URL** (newly added)
   - ✅ **SUPABASE_ACCESS_TOKEN** (newly added)

3. Test deployment:
   - Push a commit or manually trigger workflow
   - Check: **https://github.com/milosriki/geminivideo/actions**

---

## 🔍 Quick Links

- **Supabase Dashboard**: https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj
- **Database Settings**: https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj/settings/database
- **Access Tokens**: https://supabase.com/dashboard/account/tokens
- **GitHub Secrets**: https://github.com/milosriki/geminivideo/settings/secrets/actions

---

## ⚠️ Troubleshooting

### "Connection string not found"
- Make sure you're in the **Settings → Database** section
- Look for **"Connection string"** or **"Connection pooling"**
- Try **"Direct connection"** if pooled doesn't work

### "Access token not generating"
- Make sure you're logged into Supabase
- Go to **Account → Access Tokens** (not project settings)
- Click **"Generate new token"**

### "Secret not saving in GitHub"
- Make sure you have **admin access** to the repository
- Check that the secret name matches exactly (case-sensitive)
- Try refreshing the page

---

**That's it! Once both secrets are added, GitHub Actions will auto-deploy on push.** 🚀

