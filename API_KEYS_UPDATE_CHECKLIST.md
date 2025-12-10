# ✅ API Keys Update Checklist

## 📊 Current Status

You're using the **new API keys format**:
- ✅ `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG` (Publishable Key)
- ✅ `sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3` (Secret Key)

---

## 🎯 What to Add/Update

### **1. GitHub Secrets (Add New Names)**

Go to: https://github.com/milosriki/geminivideo/settings/secrets/actions

**Add these 2 new secrets (as aliases):**

1. **SUPABASE_PUBLISHABLE_KEY**
   - Value: `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG`
   - This is the new name for `SUPABASE_ANON_KEY`

2. **SUPABASE_SECRET_KEY**
   - Value: `sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3`
   - This is the new name for `SUPABASE_SERVICE_ROLE_KEY`

**Keep the old names too** (for backward compatibility):
- ✅ `SUPABASE_ANON_KEY` (keep existing)
- ✅ `SUPABASE_SERVICE_ROLE_KEY` (keep existing)

---

### **2. Vercel Environment Variables (Check)**

Go to: Vercel Dashboard → geminivideo → Settings → Environment Variables

**You should have:**
- ✅ `NEXT_PUBLIC_SUPABASE_URL`
- ✅ `NEXT_PUBLIC_SUPABASE_ANON_KEY` (or `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`)

**If missing, add:**
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` = `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG`

---

### **3. Edge Function Secrets (Already Correct)**

Your Edge Function Secrets are fine:
- ✅ `SUPABASE_URL`
- ✅ `SUPABASE_ANON_KEY` (works, or rename to `SUPABASE_PUBLISHABLE_KEY`)
- ✅ `SUPABASE_SERVICE_ROLE_KEY` (works, or rename to `SUPABASE_SECRET_KEY`)

---

## 📝 Complete Checklist

### **GitHub Secrets (6 total):**

- [x] `SUPABASE_DB_URL` - Set
- [x] `SUPABASE_URL` - Set
- [x] `SUPABASE_ANON_KEY` - Set (old name)
- [x] `SUPABASE_SERVICE_ROLE_KEY` - Set (old name)
- [ ] `SUPABASE_PUBLISHABLE_KEY` - **Add this** (new name)
- [ ] `SUPABASE_SECRET_KEY` - **Add this** (new name)
- [ ] `SUPABASE_PROJECT_REF` - **Add this** (`akhirugwpozlxfvtqmvj`)
- [ ] `SUPABASE_ACCESS_TOKEN` - **Add this** (from Supabase Dashboard)

### **Vercel Environment Variables:**

- [x] `NEXT_PUBLIC_SUPABASE_URL` - Auto-synced
- [ ] `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` - **Check/Add** (new format)

### **Edge Function Secrets:**

- [x] All 4 secrets set ✅

---

## 🚀 Quick Actions

### **1. Add GitHub Secrets (2 new + 2 missing):**

```
SUPABASE_PUBLISHABLE_KEY = sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG
SUPABASE_SECRET_KEY = sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3
SUPABASE_PROJECT_REF = akhirugwpozlxfvtqmvj
SUPABASE_ACCESS_TOKEN = [Get from Supabase Dashboard → Account → Access Tokens]
```

### **2. Check Vercel:**

Verify `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` exists (or add it).

---

## ✅ Summary

**You need to add 4 GitHub Secrets:**
1. `SUPABASE_PUBLISHABLE_KEY` (new format)
2. `SUPABASE_SECRET_KEY` (new format)
3. `SUPABASE_PROJECT_REF` (missing)
4. `SUPABASE_ACCESS_TOKEN` (missing)

**Everything else is already set!** 🎉

---

**Read:** `NEW_API_KEYS_MIGRATION.md` for full details on the migration.

