# ✅ Secrets Ready to Add

## What I Have

From your Supabase dashboard, I have:

1. ✅ **SUPABASE_SECRET_KEY**: `sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3`
2. ✅ **SUPABASE_ACCESS_TOKEN**: `sbp_125c933334f63cbb1dbbe0d77bb6c29afc4ee0a8`
3. ✅ **SUPABASE_SERVICE_ROLE_KEY**: (JWT token - already in GitHub)

## Project Info Retrieved

- **Project Ref**: `akhirugwpozlxfvtqmvj`
- **Region**: `ap-southeast-1`
- **Database Host**: `db.akhirugwpozlxfvtqmvj.supabase.co`

## ⚠️ Still Need: SUPABASE_DB_URL

The DB connection string requires your database password, which I can't retrieve via API for security reasons.

**Format will be:**
```
postgres://postgres.akhirugwpozlxfvtqmvj:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

**Get it from:**
1. Go to: https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj/settings/database
2. Scroll to **"Connection string"**
3. Select **"Transaction mode"** (port 6543) or **"Session mode"** (port 5432)
4. Copy the full connection string

---

## 🚀 Add These 2 Secrets Now

### Go to GitHub Secrets:
**https://github.com/milosriki/geminivideo/settings/secrets/actions**

### Secret 1: SUPABASE_SECRET_KEY
- **Name**: `SUPABASE_SECRET_KEY`
- **Value**: `sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3`
- Click **"Add secret"**

### Secret 2: SUPABASE_ACCESS_TOKEN
- **Name**: `SUPABASE_ACCESS_TOKEN`
- **Value**: `sbp_125c933334f63cbb1dbbe0d77bb6c29afc4ee0a8`
- Click **"Add secret"**

### Secret 3: SUPABASE_DB_URL (after you get it)
- **Name**: `SUPABASE_DB_URL`
- **Value**: (paste connection string from dashboard)
- Click **"Add secret"**

---

## ✅ Final Status

After adding all 3, you'll have:
- ✅ All required secrets for GitHub Actions
- ✅ Auto-deployment on push to `main`
- ✅ Migrations will apply automatically
- ✅ Edge Functions will deploy automatically

---

**Quick Links:**
- **Database Settings**: https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj/settings/database
- **GitHub Secrets**: https://github.com/milosriki/geminivideo/settings/secrets/actions

