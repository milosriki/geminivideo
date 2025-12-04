# Knowledge Injection CLI - Quick Reference

Bulk load winning ad patterns into your knowledge base from multiple sources.

## Installation

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Run database migration
psql $DATABASE_URL -f database_migrations/002_feedback_and_knowledge.sql
```

## Configuration

Set these environment variables:

```bash
# Required
export DATABASE_URL=postgresql://user:pass@localhost:5432/geminivideo

# Optional - Add as many as you have
export META_ACCESS_TOKEN=your_token        # FREE
export FOREPLAY_API_KEY=your_key           # PAID - 100M+ ads
export YOUTUBE_API_KEY=your_key            # FREE
export TIKTOK_API_KEY=your_key             # FREE
```

## Quick Start

```bash
# 1. Check configured sources
python scripts/inject_knowledge.py status

# 2. Inject patterns
python scripts/inject_knowledge.py inject \
  --query "fitness supplements" \
  --industry health \
  --limit 100

# 3. View results
python scripts/inject_knowledge.py status
```

## Commands

### Inject Knowledge

```bash
# Basic injection
python scripts/inject_knowledge.py inject \
  --query "fitness supplements" \
  --industry health \
  --limit 100

# Specific sources only
python scripts/inject_knowledge.py inject \
  --query "skincare routine" \
  --industry beauty \
  --sources foreplay,meta \
  --limit 200

# Dry run (test without inserting)
python scripts/inject_knowledge.py inject \
  --query "meal prep" \
  --industry food \
  --dry-run
```

### Check Status

```bash
python scripts/inject_knowledge.py status
```

**Output:**
- Configured data sources (✓ = available, ✗ = not configured)
- Total patterns in database
- Patterns by source
- Top industries
- Recent injections

### Export Backup

```bash
# Export all patterns
python scripts/inject_knowledge.py export -o backup.jsonl

# Export specific industry
python scripts/inject_knowledge.py export \
  --industry health \
  --limit 1000 \
  -o health_patterns.jsonl
```

### Import from CSV

```bash
python scripts/inject_knowledge.py import \
  -i data/competitor_ads.csv \
  --industry health
```

**CSV Format:**
```csv
source,hook_text,hook_type,emotional_triggers,performance_tier,industry,ctr
foreplay,"Lose 10 lbs in 14 days",urgency_scarcity,"urgency,transformation",top_10_percent,health,0.045
meta,"Secret revealed",curiosity_gap,"curiosity,desire",top_1_percent,beauty,0.068
```

Template: `/home/user/geminivideo/data/knowledge_import_template.csv`

### Clear Namespace

```bash
# Delete patterns from a source
python scripts/inject_knowledge.py clear \
  --namespace test_data \
  --force
```

## Data Sources

| Source | Cost | Coverage | Setup |
|--------|------|----------|-------|
| **Foreplay** | PAID | 100M+ ads | Get API key from foreplay.co |
| **Meta Ads Library** | FREE | All Meta ads | Get token from developers.facebook.com |
| **Internal** | FREE | Your tracked ads | No setup needed |
| **YouTube** | FREE | Trending ads | Get key from console.cloud.google.com |
| **TikTok** | FREE | Top TikTok ads | Get key from ads.tiktok.com |
| **Kaggle** | FREE | Datasets | Coming soon |

## Usage Examples

### Example 1: Inject Fitness Patterns

```bash
python scripts/inject_knowledge.py inject \
  --query "fitness supplements" \
  --industry health \
  --limit 500 \
  --sources foreplay,meta
```

### Example 2: Batch Multiple Industries

```bash
# Create batch script
cat > inject_batch.sh << 'EOF'
#!/bin/bash
for query in "fitness supplements" "protein powder" "workout plans"; do
  python scripts/inject_knowledge.py inject \
    --query "$query" \
    --industry health \
    --limit 200
  sleep 5
done
EOF

chmod +x inject_batch.sh
./inject_batch.sh
```

### Example 3: Daily Automation

Add to crontab:
```bash
# Daily at 2 AM
0 2 * * * cd /home/user/geminivideo && python scripts/inject_knowledge.py inject --query "trending fitness" --industry health --limit 100
```

## Features

### Progress Tracking
- Real-time progress bars with `tqdm`
- Per-source status updates
- ETA calculations

### Parallel Fetching
- Fetch from multiple sources simultaneously
- 3-10x faster than sequential
- Use `--sequential` to disable

### Retry Logic
- Exponential backoff (1s → 2s → 4s → ...)
- Max 3 retries per source
- Detailed error logging

### Logging
- Console output (INFO level)
- File logging (DEBUG level)
- Logs saved to `/home/user/geminivideo/logs/`
- Use `-v` for verbose console output

### Dry Run Mode
- Test without database insertion
- Verify API connections
- Preview pattern counts

## Troubleshooting

### No data from sources

Check configuration:
```bash
python scripts/inject_knowledge.py status
```

Look for ✓ next to sources. ✗ means API key not configured.

### Database errors

Verify migration ran:
```bash
psql $DATABASE_URL -c "\d winning_patterns"
```

### API rate limits

Use smaller batches:
```bash
python scripts/inject_knowledge.py inject \
  --query "your query" \
  --industry health \
  --limit 50 \
  --sequential
```

### View detailed logs

```bash
# Find latest log file
ls -lt /home/user/geminivideo/logs/ | head -5

# View log
tail -f /home/user/geminivideo/logs/knowledge_injection_YYYYMMDD_HHMMSS.log
```

## Performance

### Benchmarks

| Patterns | Sources | Time (Parallel) | Time (Sequential) |
|----------|---------|-----------------|-------------------|
| 100 | 3 | 8-12s | 25-35s |
| 500 | 5 | 25-40s | 90-150s |
| 1000 | 5 | 45-70s | 180-300s |

### Optimization Tips

1. **Use parallel mode** (default) - 3-5x faster
2. **Limit per source** - Use `--limit 100-200` for most cases
3. **Filter sources** - Use `--sources` to skip unavailable sources
4. **Batch operations** - Inject multiple queries in one session

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Knowledge Injection CLI                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │   Foreplay   │   │   Meta Ads   │   │   Internal   │    │
│  │  Connector   │   │  Connector   │   │  Connector   │    │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘    │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                           │                                 │
│                  ┌────────▼─────────┐                       │
│                  │  KnowledgePattern│                       │
│                  │   Data Model     │                       │
│                  └────────┬─────────┘                       │
│                           │                                 │
│                  ┌────────▼─────────┐                       │
│                  │  DatabaseManager │                       │
│                  │   + Retry Logic  │                       │
│                  └────────┬─────────┘                       │
│                           │                                 │
│                  ┌────────▼─────────┐                       │
│                  │   PostgreSQL     │                       │
│                  │ winning_patterns │                       │
│                  └──────────────────┘                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

The script uses these PostgreSQL tables:

### `winning_patterns`
Stores ad patterns for RAG-based generation.

**Key columns:**
- `source` - Data source (foreplay, meta, internal, etc.)
- `hook_type` - Classification (curiosity_gap, urgency, etc.)
- `emotional_triggers` - Array of trigger types
- `transcript` - Full ad text
- `performance_tier` - Performance classification
- `industry` - Industry category
- `ctr` - Click-through rate
- `raw_data` - JSONB with full source data

### `knowledge_injections`
Logs all injection operations.

**Key columns:**
- `query` - Search query used
- `industry` - Target industry
- `foreplay_count`, `meta_count`, etc. - Per-source counts
- `total_patterns` - Total patterns inserted
- `errors` - Array of error messages
- `created_at` - Timestamp

## Related Documentation

- **Full Guide:** `/home/user/geminivideo/scripts/INJECT_KNOWLEDGE_GUIDE.md`
- **Architecture:** `/home/user/geminivideo/10X_ROI_ARCHITECTURE.md`
- **Database Schema:** `/home/user/geminivideo/database_migrations/002_feedback_and_knowledge.sql`
- **Market Intel Service:** `/home/user/geminivideo/services/market-intel/README.md`

## Support

For detailed documentation, see:
- **Full guide:** `scripts/INJECT_KNOWLEDGE_GUIDE.md`
- **Logs:** `/home/user/geminivideo/logs/`
- **Database:** `database_migrations/002_feedback_and_knowledge.sql`

---

**Script:** `/home/user/geminivideo/scripts/inject_knowledge.py`
**Version:** 1.0.0
**Updated:** 2025-12-03
