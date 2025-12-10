# ⚠️ Missing GitHub Secrets

## ✅ Already Set (4/6)

1. ✅ **SUPABASE_DB_URL** - Set ✓
2. ✅ **SUPABASE_URL** - Set ✓
3. ✅ **SUPABASE_ANON_KEY** - Set ✓
4. ✅ **SUPABASE_SERVICE_ROLE_KEY** - Set ✓

## ❌ Still Need (2/6)

### **5. SUPABASE_PROJECT_REF**

**Value:**
```
akhirugwpozlxfvtqmvj
```

**How to add:**
1. Go to: https://github.com/milosriki/geminivideo/settings/secrets/actions
2. Click **"New repository secret"**
3. Name: `SUPABASE_PROJECT_REF`
4. Value: `akhirugwpozlxfvtqmvj`
5. Click **"Add secret"**

---

### **6. SUPABASE_ACCESS_TOKEN**

**How to get:**
1. Go to: https://supabase.com/dashboard/account/tokens
2. Click **"Generate new token"**
3. Give it a name (e.g., "GitHub Actions")
4. Copy the token
5. Go to: https://github.com/milosriki/geminivideo/settings/secrets/actions
6. Click **"New repository secret"**
7. Name: `SUPABASE_ACCESS_TOKEN`
8. Paste the token
9. Click **"Add secret"**

---

## ✅ After Adding These 2 Secrets

1. Go to: https://github.com/milosriki/geminivideo/actions
2. The workflow should run automatically
3. Check if it succeeds

---

## 🎯 Quick Checklist

- [x] SUPABASE_DB_URL
- [x] SUPABASE_URL
- [x] SUPABASE_ANON_KEY
- [x] SUPABASE_SERVICE_ROLE_KEY
- [ ] SUPABASE_PROJECT_REF ← **Add this**
- [ ] SUPABASE_ACCESS_TOKEN ← **Add this**

---

**Once you add these 2 secrets, everything will deploy automatically!** 🚀

