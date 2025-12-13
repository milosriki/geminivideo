# 🔍 Vercel Account Connection Diagnostic Guide

## Problem Statement
You suspect your Vercel project is connected to the **wrong Vercel account**, and you need to:
1. Confirm which Vercel account is currently linked to your GitHub repo
2. Identify which account should be used for deployments
3. Safely switch to the correct Vercel account

---

## 📋 Information Checklist

Before starting, gather this information:

- **GitHub Repository URL**: `<your-repo-url>`
- **Vercel Project Name**: `<project-name>`
- **Correct Vercel Account Email**: `<correct-email@example.com>`
- **Wrong Vercel Account Email** (suspected): `<wrong-email@example.com>`
- **GitHub Account/Org**: Where the repo is hosted

---

## 🎯 Step-by-Step Diagnostic Process

### Part 1: Check Vercel Dashboard - Identify Active Account

#### Step 1.1: Confirm Which Vercel Account You're Logged Into

1. **Open Vercel Dashboard**
   - Go to: https://vercel.com/dashboard

2. **Check Top-Right Corner**
   - Click on your **profile picture/avatar** (top-right)
   - You'll see:
     - ✅ **Email address** of logged-in account
     - ✅ **Display name**
     - ✅ **Team/Workspace** dropdown (if applicable)

3. **Record This Information**
   ```
   Currently logged in as: _________________
   Current team/workspace: _________________
   ```

#### Step 1.2: Check Account/Team Scope

1. **Look at the top-left dropdown** (next to Vercel logo)
   - Shows current **Team** or **Personal Account**
   - If you see multiple teams, note which one you're viewing

2. **Switch Between Accounts** (if you have multiple)
   - Click the dropdown
   - You may have:
     - **Personal Account** (your email)
     - **Team Account(s)** (company/org names)

3. **Find Your Project**
   - Does your project appear under:
     - ✅ Personal Account?
     - ✅ Team Account A?
     - ✅ Team Account B?

4. **Record This Information**
   ```
   Project is under account/team: _________________
   ```

#### Step 1.3: Check Project Settings

1. **Navigate to Your Project**
   - Vercel Dashboard → Select your project

2. **Go to Settings**
   - Click **Settings** tab (left sidebar)

3. **Check "General" Section**
   - **Project Name**: Verify it matches
   - **Framework**: Should show your framework (e.g., Vite, Next.js)
   - **Root Directory**: Where your code lives
   - **Build Command**: Your build script

4. **Check "Git" Section** ⚠️ **CRITICAL**
   - **Connected Git Repository**: Should show:
     ```
     GitHub: <username>/<repo-name>
     ```
   - **Production Branch**: Usually `main` or `master`
   - **Git Provider**: Should be "GitHub"

5. **Record This Information**
   ```
   Connected repo: _________________
   Production branch: _________________
   Git provider: _________________
   ```

---

### Part 2: Check GitHub Integration

#### Step 2.1: Verify Vercel GitHub App Installation

1. **Go to GitHub Settings**
   - Navigate to: https://github.com/settings/installations

2. **Find "Vercel" in Installed GitHub Apps**
   - You should see **"Vercel"** in the list
   - If you don't see it, the integration is not installed

3. **Click "Configure" next to Vercel**
   - Check **"Repository access"**:
     - ✅ All repositories? OR
     - ✅ Only select repositories?
   - If "Only select repositories," verify your repo is in the list

4. **Check Which Account This App Belongs To**
   - Look at the **"Installed by"** or **"Installation"** details
   - This tells you which GitHub account/org has the Vercel app installed

5. **Record This Information**
   ```
   Vercel GitHub App installed: ☐ Yes  ☐ No
   Repository access: ☐ All  ☐ Selected
   Your repo included: ☐ Yes  ☐ No
   Installed on: _________________
   ```

#### Step 2.2: Check Repository Webhooks

1. **Go to Your GitHub Repository**
   - Navigate to: `https://github.com/<username>/<repo-name>`

2. **Settings → Webhooks**
   - You should see a webhook with URL: `https://vercel.com/...`
   - **Payload URL** should point to Vercel

3. **Check Recent Deliveries**
   - Click on the webhook
   - Check **"Recent Deliveries"** tab
   - Look for:
     - ✅ Successful deliveries (green checkmark)
     - ❌ Failed deliveries (red X)

4. **Record This Information**
   ```
   Vercel webhook exists: ☐ Yes  ☐ No
   Recent deliveries: ☐ Success  ☐ Failed  ☐ None
   ```

#### Step 2.3: Verify GitHub OAuth Authorization

1. **Go to GitHub → Settings → Applications**
   - Navigate to: https://github.com/settings/applications

2. **Click "Authorized OAuth Apps" tab**
   - Find **"Vercel"** in the list

3. **Click on "Vercel"**
   - Check **"Authorized"** date
   - Check **"Organization access"** (if applicable)
   - Verify permissions granted

4. **Record This Information**
   ```
   Vercel OAuth authorized: ☐ Yes  ☐ No
   Date authorized: _________________
   Org access granted: _________________
   ```

---

### Part 3: Cross-Reference Vercel Account & GitHub Connection

#### Step 3.1: Match Email Addresses

Compare the email addresses you've recorded:

| Item | Email Address |
|------|---------------|
| Vercel account currently viewing project | _____________ |
| GitHub account that owns the repo | _____________ |
| Expected/correct Vercel account | _____________ |

**Question**: Do they match?
- ✅ **Yes** → Your accounts are correctly linked
- ❌ **No** → Continue to Part 4 (Switching Accounts)

#### Step 3.2: Check Recent Deployment Activity

1. **Vercel Dashboard → Your Project → Deployments**
   - Check recent deployments
   - Look at **"Deployed by"** column
   - This shows which Vercel user triggered each deployment

2. **Check Deployment Triggers**
   - **Git Push**: Triggered by GitHub webhook
   - **Manual**: Triggered by Vercel user
   - **Vercel CLI**: Triggered by local CLI

3. **Record This Information**
   ```
   Recent deployments by: _________________
   Deployment trigger: _________________
   ```

#### Step 3.3: Check Vercel CLI Configuration (if applicable)

If you deploy via Vercel CLI:

1. **Check Local `.vercel` Folder**
   ```bash
   cat .vercel/project.json
   ```
   - Shows **projectId** and **orgId**

2. **Check CLI Login**
   ```bash
   vercel whoami
   ```
   - Shows which Vercel account you're logged in as

3. **Record This Information**
   ```
   CLI logged in as: _________________
   Project ID: _________________
   Org ID: _________________
   ```

---

### Part 4: Switching to the Correct Vercel Account

If you've confirmed the project is on the **wrong** Vercel account, follow these steps to safely switch:

#### Option A: Transfer Project Within Vercel (Recommended)

**Use Case**: You have access to both Vercel accounts (personal + team, or two teams)

1. **Log into the Vercel account that currently owns the project**

2. **Go to Project Settings**
   - Vercel Dashboard → Your Project → Settings

3. **Scroll to "Transfer Project"** (bottom of General settings)
   - Click **"Transfer Project"**
   - Enter the **new team/account name**
   - Confirm transfer

4. **Benefits**:
   - ✅ Preserves deployment history
   - ✅ Keeps environment variables
   - ✅ Maintains domain configuration
   - ✅ No downtime

#### Option B: Disconnect & Reconnect (Clean Start)

**Use Case**: You don't have access to the wrong account, or you want a clean slate

##### Step B.1: Disconnect from Wrong Account

1. **Disconnect Git Repository**
   - **In Vercel (wrong account)**:
     - Project Settings → Git → **"Disconnect"**
     - This removes the Git integration but keeps the project

2. **Remove GitHub Webhook**
   - **In GitHub**:
     - Repo → Settings → Webhooks
     - Find Vercel webhook → **"Delete"**

3. **Uninstall Vercel GitHub App** (if needed)
   - **In GitHub**:
     - Settings → Applications → Installed GitHub Apps
     - Configure Vercel → Remove access to this repo

##### Step B.2: Connect to Correct Account

1. **Log out of wrong Vercel account**
   - Vercel Dashboard → Profile → **"Log Out"**

2. **Log into correct Vercel account**
   - Go to: https://vercel.com/login
   - Use correct email address

3. **Create New Project** or **Import Existing**
   - Click **"Add New..." → "Project"**
   - Click **"Import Git Repository"**
   - **Connect GitHub Account** (if not already connected)
   - Select your repository

4. **Configure Project Settings**
   - **Framework Preset**: Auto-detected or select manually
   - **Root Directory**: If monorepo, specify (e.g., `frontend`)
   - **Build Command**: e.g., `npm run build`
   - **Output Directory**: e.g., `dist` (Vite) or `build` (CRA)
   - **Install Command**: e.g., `npm install`

5. **Add Environment Variables**
   - Settings → Environment Variables
   - Add all necessary env vars (see your `.env.example`)
   - Select environments: Production, Preview, Development

6. **Deploy**
   - Click **"Deploy"**
   - Wait for first deployment to complete

##### Step B.3: Update DNS (if using custom domain)

1. **Remove old domain** from wrong Vercel account (if possible)

2. **Add domain** to new Vercel project
   - New project → Settings → Domains
   - Add your custom domain
   - Update DNS records (if needed)

---

### Part 5: Verify Correct Setup

After switching accounts, verify everything works:

#### Checklist

- [ ] **Vercel Dashboard**
  - [ ] Logged into correct account
  - [ ] Project appears in correct team/workspace
  - [ ] Git repository connected correctly

- [ ] **GitHub Integration**
  - [ ] Vercel GitHub App installed on correct account/org
  - [ ] Repository webhook pointing to correct Vercel project
  - [ ] OAuth authorization active

- [ ] **Deployments**
  - [ ] Push a test commit to GitHub
  - [ ] Verify automatic deployment triggers
  - [ ] Check deployment logs for errors
  - [ ] Visit deployed URL and test functionality

- [ ] **Environment Variables**
  - [ ] All necessary env vars added to new project
  - [ ] Verify by checking logs or testing features

- [ ] **Domains**
  - [ ] Custom domain configured (if applicable)
  - [ ] SSL certificate active
  - [ ] DNS propagated (may take up to 24-48 hours)

---

## 🔧 Common Issues & Troubleshooting

### Issue 1: "Project appears in both accounts"

**Cause**: Project was transferred but old deployment still exists

**Solution**:
1. Delete old project from wrong account
2. Verify new project is the only one receiving deployments

### Issue 2: "Deployments still going to wrong account after disconnect"

**Cause**: GitHub webhook still pointing to old project

**Solution**:
1. GitHub → Repo → Settings → Webhooks
2. Delete all Vercel webhooks
3. Reconnect GitHub in correct Vercel account
4. This will create a new webhook

### Issue 3: "Can't see my team/org in Vercel"

**Cause**: Not invited to team, or viewing wrong account

**Solution**:
1. Ask team owner to invite you to the team
2. Check email for invitation
3. Accept invitation
4. Refresh Vercel dashboard

### Issue 4: "Environment variables missing after transfer"

**Cause**: Env vars don't always transfer automatically

**Solution**:
1. Export env vars from old project (if you have access):
   ```bash
   vercel env pull .env.vercel
   ```
2. Add them manually to new project via dashboard or CLI

### Issue 5: "Build failing on new account but worked on old account"

**Cause**: Different Node.js version, missing env vars, or different build settings

**Solution**:
1. Check build logs for specific error
2. Compare project settings between old and new
3. Verify Node.js version in `package.json`:
   ```json
   {
     "engines": {
       "node": "18.x"
     }
   }
   ```
4. Check all environment variables are set

---

## 📊 Decision Matrix

Use this to decide which approach to take:

| Scenario | Recommended Action |
|----------|-------------------|
| Have access to both accounts | **Transfer project** (Option A) |
| Don't have access to wrong account | **Disconnect & reconnect** (Option B) |
| Need to preserve deployment history | **Transfer project** (Option A) |
| Want clean slate | **Disconnect & reconnect** (Option B) |
| Team collaboration needed | **Transfer to team account** (Option A) |
| Personal project | Can use either approach |

---

## 🔐 Security Considerations

### Before Disconnecting:

1. **Backup Environment Variables**
   ```bash
   # If you have Vercel CLI access
   vercel env pull .env.backup
   ```

2. **Document Domain Configuration**
   - DNS records
   - SSL certificates
   - Custom headers/redirects

3. **Export Deployment History** (if needed)
   - Take screenshots of important deployments
   - Note any critical deployment dates

### After Reconnecting:

1. **Rotate Sensitive Keys** (optional but recommended)
   - API keys
   - Database passwords
   - OAuth secrets

2. **Review Team Access**
   - Remove team members who shouldn't have access
   - Add new team members if needed

---

## 📞 Getting Help

### Vercel Support

- **Documentation**: https://vercel.com/docs
- **Support**: https://vercel.com/support
- **Discord**: https://vercel.com/discord

### GitHub Support

- **Documentation**: https://docs.github.com
- **Support**: https://support.github.com

---

## ✅ Final Checklist

Before you consider the switch complete:

- [ ] Confirmed correct Vercel account is now connected
- [ ] Verified GitHub integration is working
- [ ] Tested automatic deployment on Git push
- [ ] All environment variables are set
- [ ] Custom domain configured (if applicable)
- [ ] Team members have correct access
- [ ] Documented the change for your team
- [ ] Removed/archived old project (if applicable)

---

## 📝 Template: Document Your Current Setup

Use this template to record your findings:

```markdown
## Current Vercel Account Connection Status

**Date Checked**: _____________

### Vercel Account Details
- Logged in as: _____________
- Team/Workspace: _____________
- Project name: _____________
- Project URL: _____________

### GitHub Integration
- Repository: _____________
- GitHub account/org: _____________
- Vercel GitHub App installed: ☐ Yes  ☐ No
- Webhook active: ☐ Yes  ☐ No

### Assessment
- Is this the correct account? ☐ Yes  ☐ No
- Action needed: _____________

### Next Steps
1. _____________
2. _____________
3. _____________
```

---

**Good luck with your Vercel account troubleshooting!** 🚀

If you encounter any issues not covered here, please consult [Vercel's official documentation](https://vercel.com/docs) or reach out to their support team.
