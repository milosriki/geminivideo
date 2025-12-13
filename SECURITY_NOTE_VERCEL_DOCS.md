# 🔐 Security Note - Vercel Documentation

## About Credentials in Documentation

This repository's documentation contains references to:

1. **Supabase Project URL:** `https://akhirugwpozlxfvtqmvj.supabase.co`
2. **Supabase Anon Key:** `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG`
3. **Vercel Account ID:** `milos-projects-d46729ec` (wrong account - needs to be changed)

### ✅ These Are Intentionally Public

**Supabase URL and Anon Key:**
- ✅ **Designed to be public** - These credentials are meant for frontend use
- ✅ **Protected by RLS** - Supabase Row Level Security controls data access
- ✅ **Safe for browser** - The anon key has limited permissions
- ✅ **Industry standard** - This is how Supabase is designed to work

**From Supabase Documentation:**
> "The anon key is safe to use in a browser context. It has limited permissions and should be used for client-side applications."

### ⚠️ Credentials NOT in Documentation

These credentials are **NOT** in the documentation (and should never be):

- ❌ `SUPABASE_SERVICE_ROLE_KEY` - Server-side only, never exposed
- ❌ `SUPABASE_DB_URL` - Database connection, server-side only  
- ❌ `SUPABASE_ACCESS_TOKEN` - CLI/deployment only, never in frontend
- ❌ Meta API tokens - Private credentials
- ❌ Google API credentials - Private credentials
- ❌ TikTok API tokens - Private credentials

### 🔒 Security Measures in Place

1. **Row Level Security (RLS):**
   - Supabase tables use RLS policies
   - Anon key can only access permitted data
   - User-specific data is protected

2. **Environment Variables:**
   - Sensitive keys stored in environment variables
   - Never committed to git
   - Managed via Vercel Dashboard or CLI

3. **CORS Protection:**
   - Backend services use CORS to limit origins
   - Only allowed domains can make API calls

4. **Authentication:**
   - User authentication required for protected data
   - JWT tokens for session management
   - Secure session handling

### 📝 Why Vercel Account ID is Visible

The Vercel account ID (`milos-projects-d46729ec`) is visible because:
- It's part of the public deployment URL
- It's already in existing documentation (pre-dating this audit)
- **This is the WRONG account** - that's why we're documenting it
- It will be replaced once migrated to correct account

### ✅ What to Do

1. **Don't worry about public Supabase credentials:**
   - They're designed to be public
   - Protected by RLS and authentication
   - Standard industry practice

2. **Do protect service role keys:**
   - Never commit to git
   - Store in environment variables only
   - Use Vercel Dashboard or secrets management

3. **Update Vercel account:**
   - Follow the migration guide
   - Connect to correct account
   - Update documentation with new (public) URL

### 🔗 References

- **Supabase Security:** https://supabase.com/docs/guides/api#api-keys
- **Vercel Security:** https://vercel.com/docs/concepts/projects/environment-variables#security
- **Row Level Security:** https://supabase.com/docs/guides/auth/row-level-security

---

## Summary

✅ **Public credentials in docs are intentional and safe**  
✅ **Protected by RLS, CORS, and authentication**  
✅ **Follows industry best practices**  
⚠️ **Service role keys are kept private** (not in docs)  
⏳ **Vercel account will be updated** (follow migration guide)

---

**Last Updated:** December 12, 2024  
**Status:** Documented as part of Vercel account audit
