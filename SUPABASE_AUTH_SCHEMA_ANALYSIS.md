# 🔐 Supabase Auth Schema Analysis

## 📋 What This Schema Shows

This is Supabase's **built-in authentication schema** (`auth` schema). It's automatically managed by Supabase and handles all authentication functionality.

---

## 🎯 Key Insights for Your Project

### 1. **Your `public.users` Table Should Reference `auth.users`**

You already have this set up correctly:
```sql
-- Your public.users table
CREATE TABLE public.users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email VARCHAR UNIQUE,
  full_name VARCHAR,
  ...
);
```

**Key Point:** Your `public.users.id` should match `auth.users.id` - this is the user's UUID from Supabase Auth.

---

### 2. **RLS Policies Should Use `auth.uid()`**

Your RLS policies correctly use this pattern:
```sql
CREATE POLICY "Users can view own data"
  ON campaigns FOR SELECT
  USING ((SELECT auth.uid()) = user_id);
```

**What `auth.uid()` does:**
- Returns the current authenticated user's UUID
- Returns `NULL` if not authenticated
- This is the `id` from `auth.users` table

---

### 3. **Available Auth Tables You Can Reference**

#### **`auth.users`** (Most Important)
- `id` - UUID (use this in your foreign keys)
- `email` - User's email
- `email_confirmed_at` - When email was confirmed
- `created_at` - Account creation time
- `raw_user_meta_data` - JSONB with custom user data
- `raw_app_meta_data` - JSONB with app-specific metadata

#### **`auth.identities`**
- Links users to authentication providers (email, OAuth, etc.)
- `user_id` → `auth.users.id`
- `provider` - 'email', 'google', 'github', etc.

#### **`auth.sessions`**
- Active user sessions
- `user_id` → `auth.users.id`
- `created_at`, `updated_at` - Session timestamps

---

## 🔗 How to Use in Your Code

### **In RLS Policies:**
```sql
-- Check if user is authenticated
USING (auth.uid() IS NOT NULL)

-- Check if user owns the record
USING (auth.uid() = user_id)

-- Check if user has specific role
USING (
  auth.uid() = user_id 
  AND EXISTS (
    SELECT 1 FROM auth.users 
    WHERE id = auth.uid() 
    AND raw_user_meta_data->>'role' = 'admin'
  )
)
```

### **In Your Application Code:**
```typescript
// Get current user
const { data: { user } } = await supabase.auth.getUser()

// User ID matches auth.users.id
const userId = user?.id

// Access user metadata
const userRole = user?.user_metadata?.role
const userEmail = user?.email
```

### **In Database Functions:**
```sql
CREATE FUNCTION get_current_user_id()
RETURNS UUID AS $$
  SELECT auth.uid();
$$ LANGUAGE sql SECURITY DEFINER;
```

---

## ⚠️ Important Notes

### **DO NOT:**
- ❌ Modify the `auth` schema directly
- ❌ Create tables in the `auth` schema
- ❌ Delete from `auth.users` directly (use Supabase Auth API)
- ❌ Manually insert into `auth` tables

### **DO:**
- ✅ Reference `auth.users.id` in your foreign keys
- ✅ Use `auth.uid()` in RLS policies
- ✅ Store user profile data in `public.users`
- ✅ Use Supabase Auth API for user management

---

## 🏗️ Recommended Architecture

```
auth.users (Supabase managed)
    ↓ (id)
public.users (Your profile table)
    ↓ (user_id)
public.campaigns (Your app data)
public.blueprints
public.videos
```

**Why this pattern?**
1. `auth.users` = Authentication (managed by Supabase)
2. `public.users` = User profile (your custom data)
3. Other tables = Your application data

---

## 🔍 What Each Auth Table Does

### **Core Tables:**
- `auth.users` - User accounts
- `auth.identities` - Authentication providers linked to users
- `auth.sessions` - Active login sessions
- `auth.refresh_tokens` - Token refresh management

### **OAuth Tables:**
- `auth.oauth_clients` - OAuth client applications
- `auth.oauth_authorizations` - OAuth authorization grants
- `auth.oauth_consents` - User consent records

### **MFA Tables:**
- `auth.mfa_factors` - Multi-factor authentication factors
- `auth.mfa_challenges` - MFA challenge attempts
- `auth.mfa_amr_claims` - Authentication method references

### **SAML Tables:**
- `auth.sso_providers` - SSO provider configuration
- `auth.saml_providers` - SAML provider details
- `auth.saml_relay_states` - SAML relay state management

### **Other:**
- `auth.flow_state` - OAuth/OIDC flow state
- `auth.one_time_tokens` - Password reset, email verification tokens
- `auth.audit_log_entries` - Authentication audit logs

---

## 💡 Practical Examples for Your Project

### **1. Get User's Email in RLS Policy:**
```sql
CREATE POLICY "Users can view own campaigns"
  ON campaigns FOR SELECT
  USING (
    auth.uid() = user_id
    AND EXISTS (
      SELECT 1 FROM auth.users 
      WHERE id = auth.uid() 
      AND email_confirmed_at IS NOT NULL
    )
  );
```

### **2. Check User Role:**
```sql
CREATE POLICY "Admins can view all"
  ON campaigns FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM auth.users 
      WHERE id = auth.uid() 
      AND raw_user_meta_data->>'role' = 'admin'
    )
  );
```

### **3. Link User Profile to Auth:**
```sql
-- When user signs up, create profile
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', '')
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

---

## 🚀 Next Steps

1. ✅ **Verify your foreign keys** reference `auth.users(id)`
2. ✅ **Check your RLS policies** use `auth.uid()` correctly
3. ✅ **Create trigger** to sync `auth.users` → `public.users` on signup
4. ✅ **Use `auth.uid()`** in all user-scoped queries

---

## 📚 Resources

- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [RLS with Auth](https://supabase.com/docs/guides/auth/row-level-security)
- [User Management](https://supabase.com/docs/guides/auth/users)

---

**This schema is for reference - don't modify it, just use it!** ✅

