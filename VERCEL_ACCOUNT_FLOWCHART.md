# 🔄 Vercel Account Troubleshooting Flowchart

## Quick Decision Tree

```
START: Is my Vercel project on the wrong account?
│
├─> 🤔 Not sure? 
│   └─> Run: ./scripts/check-vercel-account.sh
│       └─> See: VERCEL_ACCOUNT_QUICK_CHECK.md
│
├─> ✅ Everything looks correct
│   └─> 🎉 You're done! No action needed.
│
└─> ❌ Yes, it's on the wrong account
    │
    ├─> Do you have access to BOTH accounts?
    │   │
    │   ├─> ✅ YES → Use "Transfer Project" Method
    │   │   │
    │   │   └─> STEPS:
    │   │       1. Log into Vercel account with the project
    │   │       2. Project Settings → "Transfer Project"
    │   │       3. Enter new team/account name
    │   │       4. Confirm transfer
    │   │       5. ✅ Done! (Preserves everything)
    │   │       
    │   │       Details: VERCEL_ACCOUNT_DIAGNOSTIC_GUIDE.md
    │   │                → Part 4 → Option A
    │   │
    │   └─> ❌ NO → Use "Disconnect & Reconnect" Method
    │       │
    │       └─> STEPS:
    │           1. Disconnect in GitHub
    │              • Delete Vercel webhook
    │              • Remove Vercel GitHub App access
    │           
    │           2. Log into CORRECT Vercel account
    │              • Log out of wrong account
    │              • Log in with correct email
    │           
    │           3. Create new project / Import repo
    │              • New Project → Import Git Repository
    │              • Select your repository
    │              • Configure settings
    │           
    │           4. Add environment variables
    │              • Copy from old project (if accessible)
    │              • Or add manually
    │           
    │           5. Deploy and verify
    │              • Push test commit
    │              • Check automatic deployment
    │              • Test deployed app
    │           
    │           Details: VERCEL_ACCOUNT_DIAGNOSTIC_GUIDE.md
    │                    → Part 4 → Option B
```

---

## Diagnostic Checklist

### Level 1: Quick Check (2 minutes)

```
[ ] Open Vercel Dashboard
    └─> Check email in top-right corner
        ├─> ✅ Correct email? → Done!
        └─> ❌ Wrong email? → Continue to Level 2

[ ] Check if project appears in current account
    ├─> ✅ Yes → Verify it's the right project
    └─> ❌ No → Project is in different account
```

### Level 2: Detailed Diagnosis (5 minutes)

```
[ ] Vercel Dashboard
    ├─> Check current team/workspace
    ├─> Find your project
    └─> Settings → Git → Verify connected repo

[ ] GitHub Integration
    ├─> Settings → Installations → Find "Vercel"
    ├─> Check which account/org it's installed on
    └─> Verify repository access

[ ] Repository Webhooks
    └─> Repo → Settings → Webhooks → Check for Vercel
```

### Level 3: Comprehensive Audit (15 minutes)

```
[ ] Run automated script
    └─> ./scripts/check-vercel-account.sh

[ ] Follow complete guide
    └─> VERCEL_ACCOUNT_DIAGNOSTIC_GUIDE.md
        ├─> Part 1: Check Vercel Dashboard
        ├─> Part 2: Check GitHub Integration
        ├─> Part 3: Cross-Reference
        └─> Part 4: Switching Accounts (if needed)
```

---

## Problem Patterns

### Pattern 1: "Can't find my project"

```
Symptom: Project doesn't appear in Vercel dashboard

Cause: Viewing wrong account or team

Fix:
1. Click team/workspace dropdown (top-left)
2. Switch to different account/team
3. Look for project there

If still not found:
→ Project might be in another Vercel account entirely
→ Follow full diagnostic guide
```

### Pattern 2: "Deployments not triggering"

```
Symptom: Push to GitHub but no deployment in Vercel

Possible Causes:
├─> Webhook not configured
├─> Wrong account connected
├─> GitHub App not installed
└─> Repository access not granted

Fix:
1. Check GitHub webhooks → Should have Vercel webhook
2. Check recent webhook deliveries → Should be successful
3. Verify Vercel GitHub App has repo access
4. Push a test commit and watch webhook delivery
```

### Pattern 3: "Unknown user deploying"

```
Symptom: Deployments show "Deployed by" someone unknown

Cause: Project connected to wrong Vercel account

Fix:
→ This is a clear sign you need to switch accounts
→ Follow Part 4 of diagnostic guide
   ├─> Transfer project (if you have access)
   └─> Or disconnect/reconnect
```

### Pattern 4: "Environment variables missing"

```
Symptom: Deployment fails due to missing env vars

Common After: Switching Vercel accounts

Fix:
1. If you have access to old account:
   • Go to old project → Settings → Environment Variables
   • Copy all variables
   
2. If using Vercel CLI:
   vercel env pull .env.backup
   
3. Add to new account:
   • New project → Settings → Environment Variables
   • Add each variable for all environments
```

---

## Decision Matrix

Use this to quickly decide your approach:

| Your Situation | Recommended Action | Time | Difficulty |
|----------------|-------------------|------|------------|
| Have access to both accounts | ✅ **Transfer Project** | 5 min | Easy |
| Don't have access to wrong account | 🔄 **Disconnect & Reconnect** | 20 min | Medium |
| Team collaboration setup | ✅ **Transfer to Team** | 10 min | Easy |
| Want to preserve deployment history | ✅ **Transfer Project** | 5 min | Easy |
| Want clean slate | 🔄 **Disconnect & Reconnect** | 20 min | Medium |
| Custom domain configured | ✅ **Transfer Project** | 5 min | Easy |
| Multiple projects to migrate | 🔄 **Script each one** | Varies | Medium |

---

## Command Quick Reference

### Diagnostic Commands

```bash
# Check local Vercel project configuration
./scripts/check-vercel-account.sh

# Check Vercel CLI login
vercel whoami

# Check local project link
cat .vercel/project.json

# Check Git remote
git remote -v
```

### Fix Commands

```bash
# Vercel CLI: Log out
vercel logout

# Vercel CLI: Log in to correct account
vercel login

# Vercel CLI: Link to different project
vercel link

# Vercel CLI: Pull environment variables
vercel env pull .env.vercel

# GitHub CLI: Check webhooks
gh api repos/:owner/:repo/hooks
```

---

## Verification Checklist

After switching accounts, verify:

```
[ ] Vercel Dashboard
    ├─> [ ] Logged into correct account
    ├─> [ ] Project visible in correct team/workspace
    └─> [ ] Git repository connected

[ ] GitHub Integration
    ├─> [ ] Vercel GitHub App installed on correct account/org
    ├─> [ ] Repository has Vercel webhook
    └─> [ ] Webhook deliveries are successful

[ ] Deployment Test
    ├─> [ ] Push a test commit
    ├─> [ ] Deployment triggered automatically
    ├─> [ ] Build completed successfully
    └─> [ ] App works at deployed URL

[ ] Configuration
    ├─> [ ] All environment variables set
    ├─> [ ] Custom domain configured (if applicable)
    └─> [ ] Team members have correct access
```

---

## When to Use Each Guide

### Use Quick Check When:
- ⚡ You need fast diagnosis
- ⚡ You've done this before
- ⚡ You know what to look for

**File**: `VERCEL_ACCOUNT_QUICK_CHECK.md`

### Use Diagnostic Guide When:
- 📖 First time facing this issue
- 📖 Need step-by-step instructions
- 📖 Want to understand the details
- 📖 Dealing with complex setup

**File**: `VERCEL_ACCOUNT_DIAGNOSTIC_GUIDE.md`

### Use Diagnostic Script When:
- 🤖 Want automated checks
- 🤖 Need to verify local setup
- 🤖 Quick overview of configuration

**Command**: `./scripts/check-vercel-account.sh`

### Use Troubleshooting Index When:
- 📚 Looking for specific scenario
- 📚 Need command reference
- 📚 Want to see all available resources

**File**: `docs/vercel-troubleshooting.md`

---

## Emergency Quick Fixes

### "I need to fix this NOW!"

**5-Minute Emergency Fix** (if you have access to both accounts):

1. **Log into wrong account**
2. **Project Settings** → Scroll to bottom → **"Transfer Project"**
3. **Enter correct team/account name**
4. **Confirm**
5. ✅ **Done!**

---

**10-Minute Emergency Fix** (if you don't have access):

1. **GitHub**: Repo → Settings → Webhooks → **Delete Vercel webhook**
2. **Vercel**: Log out → **Log in with correct account**
3. **Vercel**: New Project → **Import Git Repository** → Select your repo
4. **Configure** & **Deploy**
5. **Add environment variables**
6. ✅ **Done!**

---

## Resources

### Documentation
- 📖 [Complete Diagnostic Guide](VERCEL_ACCOUNT_DIAGNOSTIC_GUIDE.md)
- ⚡ [Quick Check Guide](VERCEL_ACCOUNT_QUICK_CHECK.md)
- 📚 [Troubleshooting Index](docs/vercel-troubleshooting.md)

### Tools
- 🤖 [Diagnostic Script](scripts/check-vercel-account.sh)

### External Links
- 🌐 [Vercel Dashboard](https://vercel.com/dashboard)
- 🌐 [GitHub Webhooks](https://github.com/settings/installations)
- 🌐 [Vercel Docs](https://vercel.com/docs)

---

**Last Updated**: 2025-12-12
