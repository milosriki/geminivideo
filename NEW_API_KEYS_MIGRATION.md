# 🔄 Supabase New API Keys Migration Guide

## 📋 Important: API Keys Are Changing

Based on [Supabase's announcement](https://github.com/orgs/supabase/discussions/29260), Supabase is transitioning from legacy JWT-based keys to new API keys:

### **Old Format (Legacy):**
- `anon` key (JWT-based)
- `service_role` key (JWT-based)

### **New Format (Current):**
- `sb_publishable_...` (replaces `anon`)
- `sb_secret_...` (replaces `service_role`)

---

## ✅ Your Current Setup

You're already using the **new format**:
- ✅ **PUBLISH KEY:** `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG`
- ✅ **SECRET:** `sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3`

**This is correct!** You're ahead of the migration.

---

## 🎯 What Needs to Be Updated

### **1. GitHub Secrets**

Update your GitHub Secrets to use the new key names:

| Old Name | New Name | Your Value |
|----------|----------|------------|
| `SUPABASE_ANON_KEY` | `SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG` |
| `SUPABASE_SERVICE_ROLE_KEY` | `SUPABASE_SECRET_KEY` | `sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3` |

**OR** keep using the old names (they still work, but new names are recommended).

### **2. Vercel Environment Variables**

Your Vercel sync should use:
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` (instead of `NEXT_PUBLIC_SUPABASE_ANON_KEY`)

But Supabase auto-sync might still use the old name. Check your Vercel dashboard.

### **3. Edge Function Secrets**

Your Edge Function Secrets are correct:
- ✅ `SUPABASE_URL`
- ✅ `SUPABASE_ANON_KEY` (can keep this name, or rename to `SUPABASE_PUBLISHABLE_KEY`)
- ✅ `SUPABASE_SERVICE_ROLE_KEY` (can keep this name, or rename to `SUPABASE_SECRET_KEY`)

---

## 📝 Migration Checklist

### **GitHub Secrets (Update Recommended):**

1. Go to: https://github.com/milosriki/geminivideo/settings/secrets/actions
2. **Option A:** Keep existing names (they still work)
   - Keep: `SUPABASE_ANON_KEY`
   - Keep: `SUPABASE_SERVICE_ROLE_KEY`
   
3. **Option B:** Update to new names (recommended)
   - Add: `SUPABASE_PUBLISHABLE_KEY` = `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG`
   - Add: `SUPABASE_SECRET_KEY` = `sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3`
   - Update GitHub Actions workflow to use new names

### **Vercel Environment Variables:**

1. Check: Vercel Dashboard → Settings → Environment Variables
2. You should see:
   - `NEXT_PUBLIC_SUPABASE_URL` ✅
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` (might be auto-synced)
   - OR `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` (new format)

3. If you see the old name, you can:
   - Keep it (still works)
   - Or manually add the new name

### **Code Updates (If Needed):**

If your code references the old key names, update:

```typescript
// Old (still works)
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// New (recommended)
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
```

---

## 🔄 Timeline (From Supabase)

- **June 2025:** Early preview (you're here!)
- **July 2025:** Full feature launch
- **November 2025:** Legacy keys start being deprecated
- **Late 2026:** Legacy keys removed

**You have time, but it's good to migrate now!**

---

## ✅ What You Need to Do

### **Immediate (Optional but Recommended):**

1. **Update GitHub Actions workflow** to support both old and new key names
2. **Add new key names to GitHub Secrets** (as aliases)
3. **Update code** to use new key names (optional, old names still work)

### **Before November 2025 (Required):**

1. Migrate all code to use new key names
2. Update all environment variables
3. Remove references to `anon` and `service_role` keys

---

## 🎯 Quick Fix: Update GitHub Actions

I'll update the workflow to support both old and new key names for compatibility.

---

## 📚 References

- [Supabase Discussion](https://github.com/orgs/supabase/discussions/29260)
- [Supabase API Keys Docs](https://supabase.com/docs/guides/api/api-keys)

---

**You're already using the new keys! Just need to update naming in some places.** 🚀

