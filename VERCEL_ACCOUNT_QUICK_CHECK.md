# ⚡ Vercel Account Quick Check

**Use this for rapid diagnosis - detailed guide available in [VERCEL_ACCOUNT_DIAGNOSTIC_GUIDE.md](VERCEL_ACCOUNT_DIAGNOSTIC_GUIDE.md)**

---

## 🎯 30-Second Check: Is Your Project on the Wrong Account?

### Quick Test

1. **Open Vercel Dashboard**: https://vercel.com/dashboard
2. **Check top-right email** → Is this your correct account? 
   - ✅ Yes → Done, you're on the right account
   - ❌ No → Continue below

---

## 🔍 5-Minute Diagnosis

### Step 1: Identify Current Account (1 min)

Visit **Vercel Dashboard** and note:
- [ ] Email shown in profile (top-right)
- [ ] Current team/workspace (top-left dropdown)
- [ ] Does your project appear here?

### Step 2: Check Git Connection (2 min)

In **Vercel → Your Project → Settings → Git**:
- [ ] Connected repository: `_______________`
- [ ] Is this the correct repo?

### Step 3: Check GitHub Integration (2 min)

Visit **GitHub → Settings → Installations**:
- [ ] Is "Vercel" app installed?
- [ ] Which account/org owns this installation?
- [ ] Does it have access to your repo?

---

## ⚠️ Red Flags - You're Probably on the Wrong Account

- ❌ Vercel email doesn't match your primary GitHub email
- ❌ Project is in a team you don't recognize
- ❌ Can't find your project in current Vercel account
- ❌ GitHub shows Vercel app installed on different account than expected
- ❌ Deployments triggered by unknown users

---

## 🛠️ Quick Fixes

### Fix 1: You Have Access to Both Accounts

**Use Vercel's built-in transfer:**

1. Log into account that currently has the project
2. Project Settings → **"Transfer Project"** (bottom of page)
3. Enter new team/account name
4. Confirm
5. ✅ Done! (Preserves everything)

### Fix 2: You Don't Have Access to Wrong Account

**Disconnect and reconnect:**

1. **In GitHub**: Delete Vercel webhook
   - Repo → Settings → Webhooks → Delete Vercel webhook

2. **Log into correct Vercel account**
   - Log out of current account
   - Log in with correct email

3. **Import project again**
   - New Project → Import Git Repository
   - Select your repo
   - Configure & deploy

4. **Add environment variables back**

---

## 📋 Critical URLs

- **Vercel Dashboard**: https://vercel.com/dashboard
- **GitHub Webhooks**: `https://github.com/<user>/<repo>/settings/hooks`
- **GitHub Installed Apps**: https://github.com/settings/installations
- **GitHub OAuth Apps**: https://github.com/settings/applications

---

## 🆘 Emergency Commands

### Check which Vercel account your CLI is using:
```bash
vercel whoami
```

### Check which project your local folder is linked to:
```bash
cat .vercel/project.json
```

### Pull environment variables from Vercel:
```bash
vercel env pull .env.vercel
```

---

## 📞 Need More Help?

See the **[Complete Diagnostic Guide](VERCEL_ACCOUNT_DIAGNOSTIC_GUIDE.md)** for:
- ✅ Step-by-step detailed checks
- ✅ Troubleshooting common issues
- ✅ Safe disconnect/reconnect procedures
- ✅ Security considerations
- ✅ Post-migration verification

---

## ✅ Post-Fix Verification (5 min)

After switching accounts:

1. **Push a test commit** to GitHub
2. **Check Vercel Dashboard** → Deployments tab
3. **Verify deployment triggered automatically**
4. **Visit deployed URL** → Does it work?

If all ✅ → You're done! 🎉

---

**Last Updated**: 2025-12-12
