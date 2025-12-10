# 🔄 Complete Supabase Sync Workflow
## Local → GitHub → Supabase Cloud (Automated)

**For complex apps (300k+ LOC) with AI agents (Cursor)**

---

## 🎯 Overview

This workflow ensures **everything stays in sync**:
- ✅ Local development → Git commits
- ✅ Git pushes → GitHub
- ✅ GitHub merges → Auto-deploy to Supabase
- ✅ AI agents (Cursor) follow rules automatically

---

## 📋 Prerequisites

1. **Install Supabase CLI:**
   ```bash
   npm install -g supabase@latest
   ```

2. **Verify installation:**
   ```bash
   supabase --version
   ```

3. **Get Supabase project credentials:**
   - Go to: https://supabase.com/dashboard
   - Select your project: "ptd marketing elite ai"
   - Get:
     - Project Reference ID
     - Database URL (Settings → Database → Connection string)
     - Access Token (Account → Access Tokens)

---

## 🚀 Initial Setup (One-Time)

### 1. Initialize Supabase (if not already done)

```bash
cd /Users/milosvukovic/Downloads/geminivideo/geminivideo
supabase init
```

This creates:
- `supabase/config.toml`
- `supabase/migrations/` directory
- `supabase/functions/` directory

### 2. Link to your Supabase project

```bash
# Get your project ref from Supabase dashboard
supabase link --project-ref YOUR_PROJECT_REF
```

Or use environment variable:
```bash
export SUPABASE_PROJECT_REF="your-project-ref"
export SUPABASE_ACCESS_TOKEN="your-access-token"
```

### 3. Start local Supabase

```bash
supabase start
```

This gives you:
- Local PostgreSQL (port 54322)
- Supabase Studio (http://localhost:54323)
- Local API (http://localhost:54321)
- Local keys printed in terminal

### 4. Set up GitHub Secrets

Go to: `https://github.com/milosriki/geminivideo/settings/secrets/actions`

Add these secrets:

| Secret Name | Value | Where to Find |
|------------|-------|---------------|
| `SUPABASE_ACCESS_TOKEN` | Your access token | Supabase Dashboard → Account → Access Tokens |
| `SUPABASE_PROJECT_REF` | Your project ref | Supabase Dashboard → Project Settings → General |
| `SUPABASE_DB_URL` | Database connection string | Supabase Dashboard → Settings → Database → Connection string (use "Pooled" or "Direct") |

---

## 🔄 Daily Workflow

### **Making Database Changes**

#### Step 1: Start local Supabase
```bash
supabase start
```

#### Step 2: Make changes
You can make changes in two ways:

**Option A: Via SQL Editor (Supabase Studio)**
1. Open: http://localhost:54323
2. Go to SQL Editor
3. Write your SQL
4. Run it

**Option B: Direct SQL file**
```bash
# Edit a SQL file
nano my_changes.sql
```

#### Step 3: Generate migration
```bash
# This compares your local DB to the shadow DB and creates a migration
supabase db diff -f add_users_table
```

This creates: `supabase/migrations/20251209120000_add_users_table.sql`

#### Step 4: Review migration
```bash
# Check what was generated
cat supabase/migrations/20251209120000_add_users_table.sql
```

#### Step 5: Apply locally
```bash
supabase migration up
```

Or reset everything (applies all migrations):
```bash
supabase db reset
```

#### Step 6: Test locally
- Test your changes work
- Test RLS policies
- Test indexes

#### Step 7: Commit to Git
```bash
git add supabase/migrations/
git commit -m "feat: add users table with RLS"
git push
```

#### Step 8: Auto-deploy
- GitHub Actions automatically runs on push to `main`
- Migrations are applied to Supabase cloud
- No manual steps needed!

---

### **Creating Edge Functions**

#### Step 1: Create function
```bash
supabase functions new my-function
```

This creates: `supabase/functions/my-function/index.ts`

#### Step 2: Write function code
```typescript
// supabase/functions/my-function/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.0";

serve(async (req) => {
  const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
  const supabaseKey = Deno.env.get("SUPABASE_ANON_KEY")!;
  const supabase = createClient(supabaseUrl, supabaseKey);

  const { data } = await req.json();
  
  // Your logic here
  const result = await supabase.from("my_table").select("*");

  return new Response(
    JSON.stringify({ success: true, data: result.data }),
    { headers: { "Content-Type": "application/json" } }
  );
});
```

#### Step 3: Serve locally
```bash
supabase functions serve my-function
```

Test with:
```bash
curl -X POST http://localhost:54321/functions/v1/my-function \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"data": "test"}'
```

#### Step 4: Commit to Git
```bash
git add supabase/functions/my-function/
git commit -m "feat: add my-function edge function"
git push
```

#### Step 5: Auto-deploy
- GitHub Actions automatically deploys on merge to `main`
- Function is live in Supabase cloud!

---

## 🤖 Using Cursor AI Agents

### **Cursor automatically follows rules**

The `.cursorrules` file tells Cursor:
- ✅ Never edit production DB directly
- ✅ Always create migrations via `supabase db diff`
- ✅ Always enable RLS on tables
- ✅ Always create indexes
- ✅ Always use pinned imports

### **Example prompts for Cursor:**

1. **Create a new table:**
   ```
   Create a SQL migration for a new "products" table with:
   - id (UUID primary key)
   - user_id (foreign key to auth.users)
   - name (text)
   - price (numeric)
   - Enable RLS with policies for authenticated users
   - Add indexes for user_id and created_at
   - Generate via: supabase db diff -f add_products_table
   ```

2. **Create an Edge Function:**
   ```
   Create an Edge Function "process-payment" that:
   - Validates JSON input
   - Uses npm:@supabase/supabase-js@2.45.0
   - Writes to "payments" table
   - Returns success/error response
   - Place in: supabase/functions/process-payment/index.ts
   ```

3. **Add RLS policy:**
   ```
   Add an RLS policy to "products" table that allows:
   - Users to SELECT their own products (user_id = auth.uid())
   - Users to INSERT their own products
   - Users to UPDATE their own products
   - Create migration: supabase db diff -f add_products_rls
   ```

---

## 🔐 Security Best Practices

### **1. RLS (Row Level Security)**

Every table MUST have:
```sql
ALTER TABLE my_table ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own data"
    ON my_table FOR SELECT
    USING ((SELECT auth.uid()) = user_id);
```

### **2. Indexes**

Always index:
- Foreign keys
- Columns in WHERE clauses
- Columns in RLS policies

```sql
CREATE INDEX idx_my_table_user_id ON my_table(user_id);
```

### **3. Secrets**

Never commit secrets:
- Use `supabase secrets set` for Edge Functions
- Use `.env.local` for local dev (gitignored)
- Use GitHub Secrets for CI/CD

---

## 📊 Monitoring & Debugging

### **Check migration status:**
```bash
supabase migration list
```

### **View local logs:**
```bash
supabase logs
```

### **Check function logs:**
```bash
supabase functions logs my-function
```

### **View in Supabase Dashboard:**
- Go to: https://supabase.com/dashboard/project/YOUR_PROJECT_REF
- Check:
  - Database → Tables
  - Database → Migrations
  - Edge Functions → Functions
  - Logs → API Logs

---

## 🚨 Troubleshooting

### **Migration fails:**
```bash
# Check what migrations are applied
supabase migration list

# Reset local DB and reapply
supabase db reset
```

### **Function won't deploy:**
```bash
# Check function syntax
deno check supabase/functions/my-function/index.ts

# Test locally first
supabase functions serve my-function
```

### **RLS blocking queries:**
```bash
# Test with service role (bypasses RLS)
# Use SUPABASE_SERVICE_ROLE_KEY in your code
```

### **GitHub Actions failing:**
1. Check secrets are set correctly
2. Check project ref is correct
3. Check database URL is accessible
4. View Actions logs: `https://github.com/milosriki/geminivideo/actions`

---

## 📚 Quick Reference

### **Common Commands:**

```bash
# Start local Supabase
supabase start

# Stop local Supabase
supabase stop

# Create migration from changes
supabase db diff -f <name>

# Apply migrations
supabase migration up

# Reset local DB (applies all migrations + seed)
supabase db reset

# Create Edge Function
supabase functions new <name>

# Serve function locally
supabase functions serve <name>

# Deploy function to cloud
supabase functions deploy <name>

# Set secrets
supabase secrets set KEY=value

# Link project
supabase link --project-ref <ref>

# Pull cloud schema (for comparison only)
supabase db pull
```

---

## ✅ Checklist

Before pushing to `main`:

- [ ] Migration created via `supabase db diff`
- [ ] Migration tested locally with `supabase db reset`
- [ ] RLS enabled on all new tables
- [ ] Policies created for all operations
- [ ] Indexes created for foreign keys
- [ ] Edge Functions use pinned imports
- [ ] Edge Functions tested locally
- [ ] No secrets committed
- [ ] Code follows `.cursorrules`

---

## 🎯 What Happens Automatically

1. **You commit to Git** → Push to GitHub
2. **GitHub Actions runs** → Checks for changes in `supabase/migrations/` or `supabase/functions/`
3. **Migrations applied** → Runs all SQL migrations in order
4. **Functions deployed** → Deploys all Edge Functions
5. **Secrets set** → Sets function secrets (if configured)
6. **Done!** → Everything is live in Supabase cloud

**No manual steps needed!** 🚀

---

## 📖 Additional Resources

- [Supabase CLI Docs](https://supabase.com/docs/reference/cli)
- [Supabase Migrations Guide](https://supabase.com/docs/guides/cli/local-development#database-migrations)
- [Edge Functions Guide](https://supabase.com/docs/guides/functions)
- [RLS Guide](https://supabase.com/docs/guides/auth/row-level-security)

---

**Your Supabase is now fully synced with GitHub!** ✅

