# 🛡️ Data Protection & Backup Plan

## 🎯 Goal: Never Lose Data

This plan ensures your data is protected, backed up, and recoverable.

---

## ✅ Current Protection Status

### **1. Database (Supabase)**
- ✅ **Automatic Backups:** Supabase provides daily backups
- ✅ **Point-in-Time Recovery (PITR):** Available on paid plans
- ✅ **RLS Policies:** Row Level Security protects data access
- ⚠️ **Manual Backups:** Should set up regular exports

### **2. Code (GitHub)**
- ✅ **Version Control:** All code in Git
- ✅ **Remote Repository:** Pushed to GitHub
- ✅ **Branch Protection:** Can enable branch protection rules

### **3. Environment Variables**
- ✅ **GitHub Secrets:** Stored securely
- ✅ **Vercel Env Vars:** Stored in Vercel
- ⚠️ **Local .env:** Should be in .gitignore (already done)

---

## 🔐 Immediate Actions (Do Now)

### **1. Enable Supabase Backups**

#### **Check Current Backup Status:**
1. Go to: **Supabase Dashboard → Settings → Database**
2. Check **"Backups"** section
3. Verify **"Point-in-Time Recovery"** is enabled (if on paid plan)

#### **If Not Enabled:**
- **Free Plan:** Daily backups (automatic, 7-day retention)
- **Pro Plan:** PITR available (up to 7 days)
- **Team/Enterprise:** Extended retention options

### **2. Set Up Manual Database Exports**

Create a backup script:

```bash
# Export database schema + data
pg_dump "postgres://postgres.akhirugwpozlxfvtqmvj:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres" \
  --format=custom \
  --file=backup_$(date +%Y%m%d_%H%M%S).dump

# Or export as SQL
pg_dump "postgres://postgres.akhirugwpozlxfvtqmvj:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres" \
  --file=backup_$(date +%Y%m%d_%H%M%S).sql
```

### **3. Protect Critical Data**

#### **Enable Branch Protection (GitHub):**
1. Go to: **GitHub → Settings → Branches**
2. Add rule for `main` branch:
   - ✅ Require pull request reviews
   - ✅ Require status checks
   - ✅ Require branches to be up to date
   - ✅ Do not allow force pushes
   - ✅ Do not allow deletions

### **4. Document Recovery Procedures**

Create recovery runbooks (see below).

---

## 📋 Backup Strategy

### **Daily Backups (Automatic - Supabase)**
- ✅ **Automatic:** Supabase handles this
- ✅ **Retention:** 7 days (free), up to 7 days PITR (paid)
- ✅ **Location:** Managed by Supabase

### **Weekly Manual Backups (Recommended)**
- 📅 **Schedule:** Every Sunday
- 📦 **What:** Full database dump
- 💾 **Storage:** Google Drive, S3, or local
- 🔄 **Retention:** Keep last 4 weeks

### **Before Major Changes**
- 📦 **What:** Database schema + data
- 💾 **When:** Before migrations, deployments, schema changes
- 🔄 **Retention:** Keep until change is verified

---

## 🔧 Implementation

### **1. Create Backup Script**

```bash
#!/bin/bash
# scripts/backup-database.sh

set -e

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Get connection string from env
DB_URL="${SUPABASE_DB_URL}"

if [ -z "$DB_URL" ]; then
    echo "❌ SUPABASE_DB_URL not set"
    exit 1
fi

echo "📦 Creating backup..."
pg_dump "$DB_URL" --file="$BACKUP_FILE" --verbose

echo "✅ Backup created: $BACKUP_FILE"
echo "📊 Size: $(du -h "$BACKUP_FILE" | cut -f1)"

# Compress backup
gzip "$BACKUP_FILE"
echo "✅ Compressed: ${BACKUP_FILE}.gz"

# Keep only last 10 backups
cd "$BACKUP_DIR"
ls -t backup_*.sql.gz | tail -n +11 | xargs rm -f

echo "✅ Backup complete!"
```

### **2. Schedule Automated Backups**

#### **Option A: GitHub Actions (Recommended)**

```yaml
# .github/workflows/backup-database.yml
name: Database Backup

on:
  schedule:
    - cron: '0 2 * * 0'  # Every Sunday at 2 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup PostgreSQL
        uses: harmon758/postgresql-action@v1
        with:
          postgresql version: '15'
      
      - name: Create backup
        env:
          DB_URL: ${{ secrets.SUPABASE_DB_URL }}
        run: |
          pg_dump "$DB_URL" --file=backup_$(date +%Y%m%d).sql
          gzip backup_*.sql
      
      - name: Upload to GitHub Releases
        uses: softprops/action-gh-release@v1
        with:
          files: backup_*.sql.gz
          tag_name: backup-${{ github.run_number }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

#### **Option B: Cron Job (Local)**

```bash
# Add to crontab (crontab -e)
0 2 * * 0 /path/to/scripts/backup-database.sh
```

### **3. Store Backups Securely**

#### **Options:**
1. **GitHub Releases** (for small backups)
2. **Google Cloud Storage** (recommended)
3. **AWS S3** (if using AWS)
4. **Local + External Drive** (for critical data)

---

## 🔄 Recovery Procedures

### **1. Restore from Supabase Backup**

#### **Point-in-Time Recovery:**
1. Go to: **Supabase Dashboard → Database → Backups**
2. Select **"Point-in-Time Recovery"**
3. Choose restore point
4. Click **"Restore"**

#### **From Manual Backup:**
```bash
# Restore from SQL dump
psql "$SUPABASE_DB_URL" < backup_20251209_120000.sql

# Or from compressed
gunzip < backup_20251209_120000.sql.gz | psql "$SUPABASE_DB_URL"
```

### **2. Restore Specific Tables**

```bash
# Restore single table
pg_restore -d "$SUPABASE_DB_URL" \
  --table=users \
  backup_20251209_120000.dump
```

### **3. Test Restore Procedure**

**Regularly test:**
- ✅ Backup creation works
- ✅ Restore procedure works
- ✅ Data integrity after restore

---

## 🚨 Disaster Recovery Plan

### **Scenario 1: Database Corruption**
1. ✅ Stop all writes (if possible)
2. ✅ Create immediate backup of current state
3. ✅ Restore from last known good backup
4. ✅ Verify data integrity
5. ✅ Resume operations

### **Scenario 2: Accidental Deletion**
1. ✅ Check Supabase PITR (if available)
2. ✅ Restore from backup
3. ✅ Verify data
4. ✅ Re-enable RLS policies

### **Scenario 3: Code Loss**
1. ✅ Restore from GitHub
2. ✅ Checkout last known good commit
3. ✅ Verify deployment

---

## 📊 Monitoring & Alerts

### **Set Up Alerts:**
1. **Database Size:** Alert if growing too fast
2. **Backup Failures:** Alert if backup fails
3. **Connection Issues:** Alert if DB unreachable
4. **Disk Space:** Alert if running low

### **Regular Checks:**
- ✅ Weekly: Verify backups are created
- ✅ Monthly: Test restore procedure
- ✅ Quarterly: Review backup retention

---

## ✅ Checklist

### **Immediate (Do Now):**
- [ ] Verify Supabase backups are enabled
- [ ] Create backup script
- [ ] Set up GitHub Actions backup workflow
- [ ] Enable branch protection on `main`
- [ ] Document recovery procedures

### **This Week:**
- [ ] Test backup creation
- [ ] Test restore procedure
- [ ] Set up backup storage (GCS/S3)
- [ ] Schedule regular backups

### **Ongoing:**
- [ ] Weekly backup verification
- [ ] Monthly restore testing
- [ ] Quarterly backup review

---

## 🔗 Resources

- **Supabase Backups:** https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj/settings/database
- **GitHub Branch Protection:** https://github.com/milosriki/geminivideo/settings/branches
- **Backup Scripts:** `scripts/backup-database.sh`

---

**This plan ensures your data is protected and recoverable!** 🛡️

