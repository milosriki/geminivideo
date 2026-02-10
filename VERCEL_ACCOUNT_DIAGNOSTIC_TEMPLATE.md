# 📝 Vercel Account Diagnostic Template

Use this template to document your findings as you work through the diagnostic process. This helps you organize information and makes it easier to ask for help if needed.

---

## 📅 Diagnostic Session

**Date**: _______________  
**Time**: _______________  
**Completed by**: _______________

---

## 🎯 Problem Statement

**Issue Description**:
```
Describe what's wrong (e.g., "My deployments are going to the wrong account")
```

**Expected Behavior**:
```
What should be happening?
```

**Actual Behavior**:
```
What is actually happening?
```

---

## 📊 Current Configuration

### Repository Information

- **GitHub Repository URL**: _______________________________________________
- **GitHub Account/Org**: __________________________________________________
- **Repository Name**: _____________________________________________________
- **Default Branch**: ______________________________________________________

### Vercel Project Information

- **Vercel Project Name**: _________________________________________________
- **Project URL**: _________________________________________________________
- **Correct Vercel Email Should Be**: ______________________________________
- **Wrong Vercel Email (Currently)**: ______________________________________

---

## 🔍 Diagnostic Findings

### Part 1: Vercel Dashboard Check

**1.1 Current Login**
- [ ] Checked Vercel Dashboard: https://vercel.com/dashboard
- Logged in as: ___________________________________________________________
- Display name: ___________________________________________________________

**1.2 Team/Account Scope**
- Current team/workspace: _________________________________________________
- Available teams/workspaces:
  - [ ] ___________________________________________________________________
  - [ ] ___________________________________________________________________
  - [ ] ___________________________________________________________________

**1.3 Project Location**
- [ ] Found project in Personal Account
- [ ] Found project in Team: ______________________________________________
- [ ] Project not found

**1.4 Project Settings**
```
Project Name: _____________________________________________________________
Framework: ________________________________________________________________
Root Directory: ___________________________________________________________
Build Command: ____________________________________________________________
Output Directory: _________________________________________________________
```

**1.5 Git Configuration**
```
Connected Repository: _____________________________________________________
Production Branch: ________________________________________________________
Git Provider: _____________________________________________________________
```

**Status**: 
- [ ] ✅ Everything looks correct
- [ ] ❌ Issues found (describe below):

**Issues**:
```
[Describe any issues found in Vercel Dashboard]
```

---

### Part 2: GitHub Integration Check

**2.1 GitHub App Installation**
- [ ] Checked: https://github.com/settings/installations
- [ ] Vercel GitHub App is installed
- [ ] Vercel GitHub App is NOT installed

**If installed:**
- Installed on account/org: _______________________________________________
- Repository access:
  - [ ] All repositories
  - [ ] Only select repositories
- Is your repo included? 
  - [ ] Yes
  - [ ] No

**2.2 Repository Webhooks**
- [ ] Checked: https://github.com/[OWNER]/[REPO]/settings/hooks
- [ ] Vercel webhook exists
- Webhook URL: ____________________________________________________________
- Recent deliveries status:
  - [ ] ✅ Successful
  - [ ] ❌ Failed
  - [ ] ⚠️ None

**2.3 OAuth Authorization**
- [ ] Checked: https://github.com/settings/applications
- [ ] Vercel is in "Authorized OAuth Apps"
- Authorized on: __________________________________________________________
- Organization access: ____________________________________________________

**Status**:
- [ ] ✅ GitHub integration looks correct
- [ ] ❌ Issues found (describe below):

**Issues**:
```
[Describe any issues found with GitHub integration]
```

---

### Part 3: Local Configuration Check

**3.1 Automated Script Results**

Ran script: [ ] Yes  [ ] No

```bash
# Command run:
./scripts/check-vercel-account.sh

# Key findings:
```

**3.2 Local Vercel Configuration**

**`.vercel/project.json` contents**:
```json
[Paste contents here if exists, or write "Not found"]
```

**3.3 Vercel CLI Status**

```bash
# vercel whoami output:
```

**3.4 Environment Files Found**
- [ ] .env
- [ ] .env.local
- [ ] .env.production
- [ ] .env.example
- [ ] Other: _______________________________________________________________

---

### Part 4: Recent Deployment Activity

**Recent Deployments**:

| Date | Deployed By | Trigger | Status | Notes |
|------|-------------|---------|--------|-------|
|      |             |         |        |       |
|      |             |         |        |       |
|      |             |         |        |       |

**Pattern Observed**:
```
[Describe any patterns, e.g., "All deployments by unknown@example.com"]
```

---

## 🎯 Root Cause Analysis

**Primary Issue Identified**:
- [ ] Project is in wrong Vercel account
- [ ] GitHub App installed on wrong account/org
- [ ] Webhook pointing to wrong project
- [ ] CLI linked to wrong account
- [ ] Other: _______________________________________________________________

**Why This Happened** (if known):
```
[Explain how this situation occurred, if you know]
```

---

## 🛠️ Proposed Solution

**Selected Approach**:
- [ ] Option A: Transfer Project (within Vercel)
- [ ] Option B: Disconnect & Reconnect
- [ ] Other: _______________________________________________________________

**Reason for Selection**:
```
[Why did you choose this approach?]
```

**Prerequisites Checked**:
- [ ] Have access to current (wrong) account
- [ ] Have access to correct account
- [ ] Have admin rights to GitHub repository
- [ ] Have exported/documented environment variables
- [ ] Have documented current configuration
- [ ] Team members notified (if applicable)

---

## 📋 Implementation Steps

**Step 1**: ________________________________________________________________
- [ ] Completed
- Notes: __________________________________________________________________

**Step 2**: ________________________________________________________________
- [ ] Completed
- Notes: __________________________________________________________________

**Step 3**: ________________________________________________________________
- [ ] Completed
- Notes: __________________________________________________________________

**Step 4**: ________________________________________________________________
- [ ] Completed
- Notes: __________________________________________________________________

**Step 5**: ________________________________________________________________
- [ ] Completed
- Notes: __________________________________________________________________

**Additional Steps**:
```
[Add more steps as needed]
```

---

## ✅ Verification Checklist

### Vercel Dashboard
- [ ] Logged into correct Vercel account
- [ ] Project appears in correct team/workspace
- [ ] Git repository correctly connected
- [ ] Project settings are correct
- [ ] All environment variables are set

### GitHub Integration
- [ ] Vercel GitHub App installed on correct account/org
- [ ] Repository has access granted to Vercel App
- [ ] Webhook exists and is active
- [ ] Recent webhook deliveries are successful

### Deployment Test
- [ ] Pushed test commit to GitHub
- [ ] Deployment triggered automatically
- [ ] Build completed successfully
- [ ] No errors in build logs
- [ ] Visited deployed URL - app works correctly

### Configuration
- [ ] All environment variables verified
- [ ] Custom domain configured (if applicable)
- [ ] SSL certificate active (if custom domain)
- [ ] Team members have correct access
- [ ] Old project archived/deleted (if applicable)

### Documentation
- [ ] Updated team documentation
- [ ] Notified team members
- [ ] Documented any configuration changes

---

## 🐛 Issues Encountered

### Issue 1
**Description**: ___________________________________________________________
**Error Message**: _________________________________________________________
**Resolution**: ____________________________________________________________
**Time to resolve**: _______________________________________________________

### Issue 2
**Description**: ___________________________________________________________
**Error Message**: _________________________________________________________
**Resolution**: ____________________________________________________________
**Time to resolve**: _______________________________________________________

### Issue 3
**Description**: ___________________________________________________________
**Error Message**: _________________________________________________________
**Resolution**: ____________________________________________________________
**Time to resolve**: _______________________________________________________

---

## 📊 Summary

**Total Time Spent**: ______________________________________________________

**Final Status**:
- [ ] ✅ Successfully resolved - project on correct account
- [ ] ⚠️ Partially resolved - requires additional work
- [ ] ❌ Not resolved - need help

**What Worked**:
```
[Describe what worked well]
```

**What Didn't Work**:
```
[Describe what didn't work or was challenging]
```

**Lessons Learned**:
```
[What did you learn from this experience?]
```

---

## 📞 Support Notes

**Need Help?**

If you need to ask for support, include:
- [ ] This completed template
- [ ] Screenshots of error messages
- [ ] Build logs (if relevant)
- [ ] Webhook delivery logs (if relevant)

**Where to Get Help**:
- Vercel Support: https://vercel.com/support
- GitHub Support: https://support.github.com
- Internal team: __________________________________________________________

---

## 🔒 Security Checklist

**Sensitive Information Handled**:
- [ ] Environment variables backed up securely
- [ ] API keys rotated (if needed)
- [ ] Database passwords updated (if needed)
- [ ] OAuth secrets verified
- [ ] No secrets exposed in logs or screenshots

**Access Control**:
- [ ] Reviewed team member access
- [ ] Removed unnecessary permissions
- [ ] Verified only authorized users have access

---

## 📝 Additional Notes

```
[Any additional observations, thoughts, or information that might be useful]
```

---

## 🔗 References Used

- [ ] VERCEL_ACCOUNT_DIAGNOSTIC_GUIDE.md
- [ ] VERCEL_ACCOUNT_QUICK_CHECK.md
- [ ] VERCEL_ACCOUNT_FLOWCHART.md
- [ ] scripts/check-vercel-account.sh
- [ ] Vercel Documentation
- [ ] GitHub Documentation
- [ ] Other: _______________________________________________________________

---

**Template Version**: 1.0  
**Last Updated**: 2025-12-12

---

## 💾 Save This File

Save a copy of this completed template for your records:

**Suggested filename**: `vercel-diagnostic-[DATE]-[PROJECT-NAME].md`

**Example**: `vercel-diagnostic-2025-12-12-geminivideo.md`
