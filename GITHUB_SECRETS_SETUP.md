# 🔐 GitHub Secrets Setup Guide
## Based on Your Supabase Dashboard

---

## 📋 From Your Supabase JWT Settings

You have:
- **PUBLISH KEY:** `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG`
- **SECRET:** `sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3`
- **URL:** `https://akhirugwpozlxfvtqmvj.supabase.co`

---

## 🎯 GitHub Secrets to Set

Go to: **https://github.com/milosriki/geminivideo/settings/secrets/actions**

Click **"New repository secret"** for each:

### **1. SUPABASE_URL**
```
https://akhirugwpozlxfvtqmvj.supabase.co
```
**From:** Your Supabase Dashboard → JWT Settings (shown above)

---

### **2. SUPABASE_ANON_KEY**
```
sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG
```
**From:** Your Supabase Dashboard → JWT Settings → PUBLISH KEY

**OR** if you have the old format:
Go to: **Supabase Dashboard → Project Settings → API**
Look for: **"anon public"** key

---

### **3. SUPABASE_SERVICE_ROLE_KEY**
```
sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3
```
**From:** Your Supabase Dashboard → JWT Settings → SECRET

**OR** if you have the old format:
Go to: **Supabase Dashboard → Project Settings → API**
Look for: **"service_role secret"** key

---

### **4. SUPABASE_PROJECT_REF**
```
akhirugwpozlxfvtqmvj
```
**From:** Your URL: `https://akhirugwpozlxfvtqmvj.supabase.co`
The part before `.supabase.co` is your project ref.

---

### **5. SUPABASE_ACCESS_TOKEN**
Go to: **Supabase Dashboard → Account → Access Tokens**
Click **"Generate new token"**
Copy the token and paste here.

---

### **6. SUPABASE_DB_URL**
Go to: **Supabase Dashboard → Settings → Database**
Scroll to **"Connection string"**
Select **"Pooled connection"** or **"Direct connection"**
Copy the connection string.

Format will be:
```
postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

**OR** for direct connection:
```
postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
```

---

## 📝 Quick Copy-Paste Checklist

1. **SUPABASE_URL**
   ```
   https://akhirugwpozlxfvtqmvj.supabase.co
   ```

2. **SUPABASE_ANON_KEY**
   ```
   sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG
   ```

3. **SUPABASE_SERVICE_ROLE_KEY**
   ```
   sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3
   ```

4. **SUPABASE_PROJECT_REF**
   ```
   akhirugwpozlxfvtqmvj
   ```

5. **SUPABASE_ACCESS_TOKEN**
   - Go to: Account → Access Tokens
   - Generate new token
   - Copy and paste

6. **SUPABASE_DB_URL**
   - Go to: Settings → Database → Connection string
   - Copy "Pooled connection" string
   - Paste here

---

## ✅ Verification

After setting all 6 secrets:

1. Go to: https://github.com/milosriki/geminivideo/actions
2. You should see the workflow running
3. Check if it succeeds or fails
4. If it fails, check the logs for which secret is missing

---

## 🔄 If You Have Old Format Keys

If your Supabase project still uses the old format:

1. Go to: **Supabase Dashboard → Project Settings → API**
2. Look for:
   - **"anon public"** → Use for `SUPABASE_ANON_KEY`
   - **"service_role secret"** → Use for `SUPABASE_SERVICE_ROLE_KEY`

The new format (publishable/secret) works the same way!

---

## 🎯 Summary

From your JWT Settings page, you can directly use:
- ✅ **URL** → `SUPABASE_URL`
- ✅ **PUBLISH KEY** → `SUPABASE_ANON_KEY`
- ✅ **SECRET** → `SUPABASE_SERVICE_ROLE_KEY`
- ✅ **Project Ref** → Extract from URL → `SUPABASE_PROJECT_REF`

You still need to get:
- ⚠️ **Access Token** → From Account → Access Tokens
- ⚠️ **Database URL** → From Settings → Database → Connection string

---

**Set these 6 secrets and GitHub Actions will auto-deploy!** 🚀

