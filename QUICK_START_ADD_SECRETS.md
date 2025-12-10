# 🚀 Quick Start: Add Secrets Automatically

## ✅ Ready to Go!

I've created scripts that can add all secrets to GitHub automatically once you provide a GitHub Personal Access Token.

---

## Method 1: Python Script (Recommended - Most Reliable)

### Step 1: Install Dependencies

```bash
pip3 install PyNaCl requests
```

### Step 2: Get GitHub PAT

1. Go to: **https://github.com/settings/tokens**
2. Click **"Generate new token (classic)"**
3. Name: `Add Supabase Secrets`
4. Scopes: ✅ **repo** ✅ **workflow**
5. Click **"Generate token"**
6. Copy the token (starts with `ghp_...`)

### Step 3: Run Script

```bash
export GITHUB_TOKEN=ghp_your_token_here
python3 add_github_secrets.py
```

**That's it!** The script will:
- ✅ Verify your token
- ✅ Add `SUPABASE_SECRET_KEY`
- ✅ Add `SUPABASE_ACCESS_TOKEN`
- ✅ Prompt you for `SUPABASE_DB_URL` if you have it

---

## Method 2: Shell Script (Alternative)

```bash
export GITHUB_TOKEN=ghp_your_token_here
./add-secrets-with-pat.sh
```

---

## Method 3: GitHub CLI (If Installed)

```bash
# Install GitHub CLI
brew install gh
gh auth login

# Add secrets directly
echo "sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3" | gh secret set SUPABASE_SECRET_KEY --repo milosriki/geminivideo
echo "sbp_125c933334f63cbb1dbbe0d77bb6c29afc4ee0a8" | gh secret set SUPABASE_ACCESS_TOKEN --repo milosriki/geminivideo
```

---

## 🔐 What You Need

1. **GitHub PAT** with `repo` and `workflow` scopes
   - Get from: https://github.com/settings/tokens

2. **SUPABASE_DB_URL** (optional - can add later)
   - Get from: https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj/settings/database

---

## ✅ After Adding Secrets

Once all secrets are added:
- ✅ GitHub Actions will auto-deploy on push to `main`
- ✅ Migrations will apply automatically
- ✅ Edge Functions will deploy automatically

Verify at: **https://github.com/milosriki/geminivideo/settings/secrets/actions**

---

**Ready? Just provide your GitHub PAT and I'll add everything!** 🚀

