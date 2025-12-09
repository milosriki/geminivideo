# 📋 INSTRUCTIONS FOR GOOGLE CLOUD STUDIO
## Prevent Overwrites - Keep Everything Aligned

**IMPORTANT**: Read this before making any changes in Google Cloud Studio!

---

## ⚠️ CRITICAL RULES

### 1. ALWAYS Pull First
```bash
git pull origin main
```

### 2. NEVER Force Push
```bash
# ❌ DON'T DO THIS:
git push --force origin main

# ✅ DO THIS INSTEAD:
git pull origin main
git push origin main
```

### 3. Use Feature Branches
```bash
# Create a branch for your work
git checkout -b cloud-studio-feature

# Make your changes
# ... edit files ...

# Commit and push
git add .
git commit -m "Changes from Cloud Studio"
git push origin cloud-studio-feature

# Merge later via PR or locally
```

---

## 🔄 SYNC WORKFLOW

### Before Making Changes

```bash
# 1. Fetch latest
git fetch origin

# 2. Check status
git status

# 3. Pull if needed
git pull origin main

# 4. Create feature branch
git checkout -b cloud-studio-$(date +%Y%m%d)
```

### After Making Changes

```bash
# 1. Check what changed
git status
git diff

# 2. Add changes
git add .

# 3. Commit
git commit -m "Description of changes"

# 4. Push to feature branch
git push origin cloud-studio-$(date +%Y%m%d)
```

---

## ✅ VERIFICATION

### Check Alignment

```bash
# Check if you're aligned
git fetch origin
git status

# Should show:
# "Your branch is up to date with 'origin/main'"
```

### Check for Conflicts

```bash
# See what's different
git log HEAD..origin/main --oneline  # Remote has, you don't
git log origin/main..HEAD --oneline  # You have, remote doesn't
```

---

## 🚨 IF YOU SEE CONFLICTS

### If Remote Has New Commits

```bash
# Pull and rebase
git pull --rebase origin main

# Resolve any conflicts
# Then continue
git rebase --continue
```

### If You Have Unpushed Commits

```bash
# Push your changes first
git push origin main

# Or create a branch
git checkout -b my-changes
git push origin my-changes
```

---

## 📝 QUICK REFERENCE

### Safe Commands
```bash
git pull origin main          # ✅ Safe - gets latest
git push origin main          # ✅ Safe - if you're ahead
git fetch origin              # ✅ Safe - just checks
git status                    # ✅ Safe - just shows status
```

### Dangerous Commands
```bash
git push --force origin main  # ❌ DANGEROUS - can overwrite
git reset --hard              # ❌ DANGEROUS - loses changes
git push -f origin main       # ❌ DANGEROUS - force push
```

---

## 🎯 CURRENT STATUS

**Repository**: `https://github.com/milosriki/geminivideo.git`  
**Branch**: `main`  
**Status**: ✅ All code is aligned and pushed

**Last Sync**: Check with:
```bash
git log -1 --format="%h - %s (%ar)"
```

---

## 📞 NEED HELP?

If you see conflicts or issues:

1. **Don't force push!**
2. **Pull first**: `git pull origin main`
3. **Resolve conflicts** if any
4. **Push normally**: `git push origin main`

If still stuck, create a feature branch and push that instead.

---

## ✅ CHECKLIST

Before making changes:
- [ ] `git pull origin main`
- [ ] `git status` shows clean
- [ ] Created feature branch (recommended)

After making changes:
- [ ] `git add .`
- [ ] `git commit -m "Description"`
- [ ] `git push origin <branch-name>`

---

**Remember**: Always pull before push, never force push to main! 🛡️

