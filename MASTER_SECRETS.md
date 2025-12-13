# 🔐 Master Secrets Guide for Vercel & GitHub

Since I cannot access your Vercel/GitHub accounts directly, please add these secrets manually.

## 1. Vercel Environment Variables
**Go to:** [Vercel Dashboard](https://vercel.com/dashboard) → Select Project → Settings → Environment Variables

Add these to **Production**, **Preview**, and **Development**:

| Variable Name | Value |
| :--- | :--- |
| `VITE_SUPABASE_URL` | `https://akhirugwpozlxfvtqmvj.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG` |

---

## 2. GitHub Secrets
**Go to:** [GitHub Repo Settings](https://github.com/milosriki/geminivideo/settings/secrets/actions) → New repository secret

| Secret Name | Value |
| :--- | :--- |
| `SUPABASE_URL` | `https://akhirugwpozlxfvtqmvj.supabase.co` |
| `SUPABASE_ANON_KEY` | `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG` |
| `SUPABASE_SERVICE_ROLE_KEY` | `sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3` |
| `SUPABASE_DB_URL` | `postgresql://postgres:Pazi1stazelis%40@db.akhirugwpozlxfvtqmvj.supabase.co:5432/postgres` |
| `SUPABASE_ACCESS_TOKEN` | *(Generate this in Supabase: Account -> Access Tokens)* |

## 3. Local Setup (Already Done ✅)
I have already updated your `frontend/.env` file with these values.
