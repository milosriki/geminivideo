# 🔐 GitHub Personal Access Token Setup

## Quick Setup (2 minutes)

### Step 1: Generate GitHub PAT

1. Go to: **https://github.com/settings/tokens**
2. Click **"Generate new token (classic)"**
3. Give it a name: `Add Supabase Secrets`
4. Set expiration: `90 days` (or `No expiration` if you prefer)
5. Select scopes:
   - ✅ **repo** (Full control of private repositories)
     - This includes: `repo:status`, `repo_deployment`, `public_repo`, `repo:invite`, `security_events`
   - ✅ **workflow** (Update GitHub Action workflows)
6. Click **"Generate token"**
7. **IMPORTANT**: Copy the token immediately (starts with `ghp_...`)
   - You won't be able to see it again!

### Step 2: Run the Script

```bash
# Set the token
export GITHUB_TOKEN=ghp_your_token_here

# Run the script
./add-secrets-with-pat.sh
```

The script will:
- ✅ Verify your token
- ✅ Add `SUPABASE_SECRET_KEY`
- ✅ Add `SUPABASE_ACCESS_TOKEN`
- ✅ Prompt you for `SUPABASE_DB_URL` if you have it

---

## Alternative: Install GitHub CLI (Recommended)

If you install GitHub CLI, the script will use it for better encryption:

```bash
# Install GitHub CLI
brew install gh

# Authenticate
gh auth login

# Then run the script (it will use gh automatically)
./add-secrets-with-pat.sh
```

---

## Security Notes

- ⚠️ **Never commit your GitHub PAT to git**
- ⚠️ **Don't share your PAT publicly**
- ✅ **Use environment variables** (`export GITHUB_TOKEN=...`)
- ✅ **Revoke the token** after adding secrets if you want
- ✅ **Set expiration** for extra security

---

## What the Script Does

1. Verifies your GitHub token works
2. Gets the repository's public encryption key
3. Encrypts and adds each secret via GitHub API
4. Confirms each secret was added successfully

---

## Troubleshooting

### "Bad credentials"
- Check that your token is correct
- Make sure you copied the entire token (starts with `ghp_`)

### "Repository not found"
- Verify you have access to `milosriki/geminivideo`
- Check that the token has `repo` scope

### "Failed to get public key"
- Make sure the token has `repo` scope
- Try regenerating the token

### Encryption errors
- Install GitHub CLI: `brew install gh`
- Or the script will use a fallback method

---

**Ready? Generate your token and run the script!** 🚀

