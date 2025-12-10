# 🔧 Auth Integration Fixes Needed

## ⚠️ Issue Found in Your Schema

Your `public.users` table is **NOT** properly linked to `auth.users`:

```sql
-- Current (WRONG):
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- ❌ Generates new UUID
    email TEXT UNIQUE NOT NULL,
    ...
);
```

**Problem:** This creates a separate user table that doesn't match `auth.users.id`

---

## ✅ Correct Approach

### **Option 1: Link public.users to auth.users (Recommended)**

```sql
-- Fixed version:
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,  -- ✅ References auth.users
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Remove the DEFAULT gen_random_uuid() - ID comes from auth.users
```

**Then create a trigger to auto-create profile on signup:**
```sql
-- Function to handle new user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', '')
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on auth.users insert
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

### **Option 2: Use auth.users Directly (Simpler)**

If you don't need extra fields, just use `auth.users` directly:
- Remove `public.users` table
- Reference `auth.users(id)` in your foreign keys
- Use `auth.users.email`, `auth.users.raw_user_meta_data` for profile data

---

## 🔧 Migration to Fix

Create a new migration file:

```sql
-- Fix users table to reference auth.users
ALTER TABLE users 
  DROP CONSTRAINT IF EXISTS users_pkey,
  ALTER COLUMN id DROP DEFAULT,
  ADD CONSTRAINT users_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- Create trigger for new users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', '')
  )
  ON CONFLICT (id) DO UPDATE
  SET email = EXCLUDED.email,
      updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

---

## ✅ What You're Doing Right

1. ✅ **Foreign keys** correctly reference `auth.users(id)`:
   ```sql
   user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
   ```

2. ✅ **RLS policies** correctly use `auth.uid()`:
   ```sql
   USING (auth.uid() = user_id)
   ```

---

## 🎯 Key Learnings from Auth Schema

1. **`auth.users.id`** is the source of truth for user identity
2. **`auth.uid()`** returns the current authenticated user's ID
3. **Never modify `auth` schema** - it's managed by Supabase
4. **Always reference `auth.users(id)`** in foreign keys
5. **Use triggers** to sync `auth.users` → `public.users` on signup

---

## 📋 Action Items

1. ⚠️ Fix `public.users` table to reference `auth.users(id)`
2. ✅ Keep foreign keys referencing `auth.users(id)` (already correct)
3. ✅ Keep RLS policies using `auth.uid()` (already correct)
4. ➕ Add trigger to auto-create user profile on signup

---

**Want me to create the migration file to fix this?** 🚀

