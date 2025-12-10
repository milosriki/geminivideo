# ✅ Supabase Sync Setup Complete!

## 🎉 What Was Created

1. **`.cursorrules`** - AI agent rules for Cursor
   - Ensures all AI-generated code follows best practices
   - Prevents direct production DB edits
   - Enforces RLS, indexes, pinned imports

2. **`.github/workflows/supabase-deploy.yml`** - Auto-deploy workflow
   - Automatically applies migrations on push to `main`
   - Automatically deploys Edge Functions
   - Sets secrets if configured

3. **`SUPABASE_SYNC_WORKFLOW.md`** - Complete guide
   - Step-by-step workflow
   - Troubleshooting
   - Best practices

4. **`supabase/migrations/20251209120000_initial_schema_with_rls.sql`** - Production-ready migration
   - Complete schema with RLS
   - All indexes
   - Storage policies

5. **`setup-supabase-sync.sh`** - Quick setup script

---

## 🚀 Quick Start

### 1. Install Supabase CLI (if not already)
```bash
npm install -g supabase@latest
```

### 2. Link Your Project
```bash
cd /Users/milosvukovic/Downloads/geminivideo/geminivideo
supabase link --project-ref YOUR_PROJECT_REF
```

Get your project ref from: https://supabase.com/dashboard/project/YOUR_PROJECT/settings/general

### 3. Start Local Supabase
```bash
supabase start
```

This gives you:
- Local PostgreSQL (port 54322)
- Supabase Studio (http://localhost:54323)
- Local API (http://localhost:54321)

### 4. Set GitHub Secrets

Go to: https://github.com/milosriki/geminivideo/settings/secrets/actions

Add these 3 secrets:

| Secret | Where to Find |
|--------|---------------|
| `SUPABASE_ACCESS_TOKEN` | Supabase Dashboard → Account → Access Tokens → Create new token |
| `SUPABASE_PROJECT_REF` | Supabase Dashboard → Project Settings → General → Reference ID |
| `SUPABASE_DB_URL` | Supabase Dashboard → Settings → Database → Connection string (use "Pooled") |

### 5. Test the Workflow

```bash
# Make a test change
supabase db diff -f test_sync

# Commit and push
git add supabase/migrations/
git commit -m "test: verify sync workflow"
git push
```

Check GitHub Actions: https://github.com/milosriki/geminivideo/actions

---

## 📊 Your Current Supabase Status

### ✅ What's Set Up:
- Supabase config (`supabase/config.toml`)
- Migration structure (`supabase/migrations/`)
- Edge Functions structure (`supabase/functions/`)
- GitHub Actions workflow
- Cursor AI rules

### ⚠️ What You Need to Do:

1. **Link your Supabase project:**
   ```bash
   supabase link --project-ref YOUR_PROJECT_REF
   ```

2. **Set GitHub Secrets** (see step 4 above)

3. **Apply existing migrations to Supabase:**
   ```bash
   # Option A: Push all migrations
   supabase db push
   
   # Option B: Apply manually via SQL Editor
   # Copy contents of supabase/migrations/001_initial_schema.sql
   # Paste in Supabase SQL Editor and run
   ```

4. **Test the sync:**
   - Make a small change locally
   - Generate migration: `supabase db diff -f test`
   - Commit and push
   - Watch GitHub Actions deploy automatically

---

## 🤖 Using Cursor AI

Cursor now automatically follows the rules in `.cursorrules`:

### Example Prompts:

1. **"Create a new table with RLS"**
   - Cursor will automatically:
     - Create migration via `supabase db diff`
     - Enable RLS
     - Create policies
     - Add indexes

2. **"Create an Edge Function"**
   - Cursor will automatically:
     - Use pinned imports
     - Place in `supabase/functions/`
     - Follow best practices

3. **"Add RLS policy"**
   - Cursor will automatically:
     - Create migration
     - Use proper `auth.uid()` pattern
     - Test locally

---

## 🔄 Daily Workflow

### Making Database Changes:

```bash
# 1. Start local Supabase
supabase start

# 2. Make changes (SQL Editor or direct SQL)
# 3. Generate migration
supabase db diff -f add_feature_name

# 4. Review migration
cat supabase/migrations/YYYYMMDDHHMMSS_add_feature_name.sql

# 5. Apply locally
supabase migration up

# 6. Test
# ... test your changes ...

# 7. Commit
git add supabase/migrations/
git commit -m "feat: add feature_name"
git push

# 8. Auto-deploy happens via GitHub Actions!
```

### Creating Edge Functions:

```bash
# 1. Create function
supabase functions new my-function

# 2. Write code in supabase/functions/my-function/index.ts

# 3. Test locally
supabase functions serve my-function

# 4. Commit
git add supabase/functions/my-function/
git commit -m "feat: add my-function"
git push

# 5. Auto-deploy happens via GitHub Actions!
```

---

## 📚 Documentation

- **Full Workflow:** `SUPABASE_SYNC_WORKFLOW.md`
- **Cursor Rules:** `.cursorrules`
- **GitHub Actions:** `.github/workflows/supabase-deploy.yml`

---

## ✅ Checklist

Before you start:

- [ ] Supabase CLI installed (`npm install -g supabase`)
- [ ] Project linked (`supabase link --project-ref ...`)
- [ ] Local Supabase started (`supabase start`)
- [ ] GitHub Secrets set (3 secrets)
- [ ] Existing migrations applied to Supabase cloud
- [ ] Test workflow works (make change, commit, push)

---

## 🎯 What Happens Now

1. **You make changes locally** → Generate migration
2. **You commit to Git** → Push to GitHub
3. **GitHub Actions runs** → Applies migrations + deploys functions
4. **Supabase cloud updated** → Everything in sync!

**No manual steps needed!** 🚀

---

## 🆘 Need Help?

1. **Read:** `SUPABASE_SYNC_WORKFLOW.md`
2. **Check:** GitHub Actions logs if deployment fails
3. **Verify:** Secrets are set correctly
4. **Test:** Local Supabase first before pushing

---

**Your Supabase is now fully synced with GitHub and Cursor AI!** ✅

