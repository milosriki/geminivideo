# 🔧 Vercel Troubleshooting Documentation

This directory contains comprehensive guides for diagnosing and fixing Vercel account connection issues.

---

## 📚 Available Guides

### 1. [VERCEL_ACCOUNT_DIAGNOSTIC_GUIDE.md](../VERCEL_ACCOUNT_DIAGNOSTIC_GUIDE.md)
**📖 Complete Diagnostic Guide** - Use this for comprehensive troubleshooting

**When to use**: 
- You need step-by-step guidance
- First time dealing with this issue
- Want to understand all the details

**Covers**:
- ✅ Detailed Vercel dashboard checks
- ✅ GitHub integration verification
- ✅ Account/team scope identification
- ✅ Safe disconnect/reconnect procedures
- ✅ Common issues and solutions
- ✅ Security considerations
- ✅ Post-migration verification

**Time**: 15-30 minutes

---

### 2. [VERCEL_ACCOUNT_QUICK_CHECK.md](../VERCEL_ACCOUNT_QUICK_CHECK.md)
**⚡ Quick Reference Guide** - Use this for rapid diagnosis

**When to use**:
- You've done this before
- Need a quick reminder
- Want to skip the explanations

**Covers**:
- ✅ 30-second quick test
- ✅ 5-minute diagnosis steps
- ✅ Red flags to watch for
- ✅ Quick fixes
- ✅ Emergency commands

**Time**: 5-10 minutes

---

### 3. [Diagnostic Script](../scripts/check-vercel-account.sh)
**🤖 Automated Diagnostic Tool** - Run this for automatic checks

**When to use**:
- Want automated checks
- Need to verify CLI configuration
- Checking local project setup

**Usage**:
```bash
cd /path/to/your/project
./scripts/check-vercel-account.sh
```

**Checks**:
- ✅ Local .vercel configuration
- ✅ Vercel CLI authentication
- ✅ Git remote configuration
- ✅ Environment files
- ✅ vercel.json configuration

**Time**: 2-3 minutes

---

## 🎯 Recommended Workflow

### For First-Time Users:

1. **Start with the Script** (2 min)
   ```bash
   ./scripts/check-vercel-account.sh
   ```
   This gives you basic information about your local setup.

2. **Read the Quick Check Guide** (5 min)
   - [VERCEL_ACCOUNT_QUICK_CHECK.md](../VERCEL_ACCOUNT_QUICK_CHECK.md)
   - Identifies if you have a problem

3. **If issues found, use the Complete Guide** (20 min)
   - [VERCEL_ACCOUNT_DIAGNOSTIC_GUIDE.md](../VERCEL_ACCOUNT_DIAGNOSTIC_GUIDE.md)
   - Follow step-by-step instructions to fix

### For Experienced Users:

1. **Run the Quick Check** (5 min)
   - [VERCEL_ACCOUNT_QUICK_CHECK.md](../VERCEL_ACCOUNT_QUICK_CHECK.md)

2. **Apply Quick Fixes** (10 min)
   - Transfer project OR disconnect/reconnect

3. **Verify** (5 min)
   - Check the verification checklist

---

## 🆘 Common Scenarios

### Scenario 1: "I can't find my project"
→ Use **Quick Check Guide** → Step 1: Identify Current Account

### Scenario 2: "My deployments are going to the wrong account"
→ Use **Complete Guide** → Part 3: Cross-Reference

### Scenario 3: "I need to switch accounts"
→ Use **Complete Guide** → Part 4: Switching to the Correct Account

### Scenario 4: "I want to verify my local CLI setup"
→ Run the **Diagnostic Script**

### Scenario 5: "Build works locally but fails on Vercel"
→ Use **Complete Guide** → Troubleshooting → Issue 5

---

## 📋 Prerequisites

Before using these guides, make sure you have:

- [ ] Access to your Vercel account(s)
- [ ] Access to your GitHub account
- [ ] Admin/owner access to the repository
- [ ] (Optional) Vercel CLI installed: `npm i -g vercel`
- [ ] (Optional) GitHub CLI installed: `gh --version`

---

## 🔗 Related Documentation

### Internal Docs:
- [VERCEL_SETUP_QUICK.md](../VERCEL_SETUP_QUICK.md) - Initial Vercel setup
- [VERCEL_SUPABASE_CONNECTION.md](../VERCEL_SUPABASE_CONNECTION.md) - Supabase integration
- [DEPLOYMENT.md](../DEPLOYMENT.md) - General deployment guide

### External Resources:
- [Vercel Documentation](https://vercel.com/docs)
- [GitHub Apps Documentation](https://docs.github.com/en/apps)
- [Vercel CLI Documentation](https://vercel.com/docs/cli)

---

## 💡 Quick Commands Reference

### Vercel CLI Commands:
```bash
# Check who you're logged in as
vercel whoami

# Log out
vercel logout

# Log in
vercel login

# Link project to Vercel
vercel link

# Pull environment variables
vercel env pull

# Check project info
cat .vercel/project.json
```

### GitHub CLI Commands:
```bash
# Check repo webhooks
gh api repos/:owner/:repo/hooks

# Check installed apps
gh api /user/installations
```

---

## 🐛 Found a Bug or Issue?

If you encounter an issue not covered by these guides:

1. Check [existing issues](https://github.com/milosriki/geminivideo/issues)
2. Open a new issue with:
   - Which guide you were following
   - What step you were on
   - What error you encountered
   - Screenshots (if applicable)

---

## 📝 Contributing

Help improve these guides:

- Report unclear instructions
- Suggest additional scenarios
- Share solutions you discovered
- Fix typos or broken links

---

**Last Updated**: 2025-12-12  
**Maintainers**: DevOps Team
