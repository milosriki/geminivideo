# Knowledge Injection CLI Guide

Complete guide for using the `inject_knowledge.py` script to bulk-load winning ad patterns into your knowledge base.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Commands](#commands)
5. [Data Sources](#data-sources)
6. [Usage Examples](#usage-examples)
7. [CSV Import Format](#csv-import-format)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r scripts/requirements.txt

# 2. Set environment variables
export DATABASE_URL=postgresql://user:pass@localhost:5432/geminivideo
export META_ACCESS_TOKEN=your_meta_token  # Optional - for Meta Ads Library
export FOREPLAY_API_KEY=your_key          # Optional - for Foreplay API

# 3. Run database migration
psql $DATABASE_URL -f database_migrations/002_feedback_and_knowledge.sql

# 4. Inject knowledge
python scripts/inject_knowledge.py inject \
  --query "fitness supplements" \
  --industry health \
  --limit 100

# 5. Check status
python scripts/inject_knowledge.py status
```

---

## Installation

### Dependencies

```bash
cd /home/user/geminivideo
pip install -r scripts/requirements.txt
```

Required packages:
- `tqdm` - Progress bars
- `psycopg2-binary` - PostgreSQL database connector
- `pandas` - CSV import/export
- `requests` - HTTP API calls
- `python-dotenv` - Environment variable loading

### Database Setup

The script requires the `winning_patterns` and `knowledge_injections` tables:

```bash
psql $DATABASE_URL -f database_migrations/002_feedback_and_knowledge.sql
```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | **Yes** | PostgreSQL connection string |
| `FOREPLAY_API_KEY` | No | Foreplay API key (PAID - 100M+ ads) |
| `META_ACCESS_TOKEN` | No | Meta Graph API access token (FREE) |
| `YOUTUBE_API_KEY` | No | YouTube Data API key (FREE) |
| `TIKTOK_API_KEY` | No | TikTok API key (FREE) |

### Example `.env` file

```bash
# Required
DATABASE_URL=postgresql://user:password@localhost:5432/geminivideo

# Optional - Add as many as you have
META_ACCESS_TOKEN=your_meta_token_here
FOREPLAY_API_KEY=your_foreplay_key_here
YOUTUBE_API_KEY=your_youtube_key_here
```

---

## Commands

### 1. `inject` - Inject Knowledge

Fetch winning ad patterns from multiple sources and inject into database.

**Syntax:**
```bash
python scripts/inject_knowledge.py inject \
  --query "SEARCH_QUERY" \
  --industry INDUSTRY \
  [--limit N] \
  [--sources source1,source2] \
  [--dry-run] \
  [--sequential]
```

**Options:**
- `--query` (required) - Search query (e.g., "fitness supplements", "skincare routine")
- `--industry` (required) - Industry category (health, beauty, ecommerce, food, etc.)
- `--limit` - Max patterns per source (default: 100)
- `--sources` - Comma-separated list of sources (default: all available)
- `--dry-run` - Fetch but don't insert into database
- `--sequential` - Fetch sources one at a time (default: parallel)

**Available Sources:**
- `foreplay` - Foreplay API (PAID - requires API key)
- `meta` - Meta Ads Library (FREE - requires access token)
- `youtube` - YouTube Trending (FREE - requires API key)
- `tiktok` - TikTok Creative Center (FREE - requires API key)
- `internal` - CompetitorTracker data (FREE - local data)
- `kaggle` - Kaggle datasets (FREE - coming soon)

---

### 2. `status` - Show Status

Display knowledge base statistics and configured sources.

**Syntax:**
```bash
python scripts/inject_knowledge.py status
```

**Output:**
- Configured data sources
- Total patterns in database
- Patterns by source
- Top industries
- Recent injection operations

---

### 3. `export` - Export Patterns

Export patterns to JSONL file for backup or analysis.

**Syntax:**
```bash
python scripts/inject_knowledge.py export \
  [-o OUTPUT_FILE] \
  [--industry INDUSTRY] \
  [--source SOURCE] \
  [--limit N]
```

**Options:**
- `-o, --output` - Output file path (default: auto-generated)
- `--industry` - Filter by industry
- `--source` - Filter by source
- `--limit` - Limit number of patterns

---

### 4. `import` - Import from File

Import patterns from CSV or JSONL file.

**Syntax:**
```bash
python scripts/inject_knowledge.py import \
  -i INPUT_FILE \
  [--industry INDUSTRY] \
  [--dry-run]
```

**Options:**
- `-i, --input` (required) - Input file path (.csv or .jsonl)
- `--industry` - Industry category (default: "general")
- `--dry-run` - Load but don't insert into database

---

### 5. `clear` - Clear Namespace

Delete all patterns from a specific source namespace.

**Syntax:**
```bash
python scripts/inject_knowledge.py clear \
  --namespace NAMESPACE \
  [--force]
```

**Options:**
- `--namespace` (required) - Namespace to clear (source name)
- `--force` - Skip confirmation prompt

---

## Data Sources

### PAID Sources

#### Foreplay API
- **Cost:** Paid subscription
- **Coverage:** 100M+ ads from Meta, TikTok, YouTube
- **Data Quality:** High - curated winning ads
- **Setup:** Get API key from [foreplay.co](https://foreplay.co)
- **Environment:** `FOREPLAY_API_KEY=your_key`

### FREE Sources

#### Meta Ads Library
- **Cost:** Free
- **Coverage:** All active Meta ads (searchable)
- **Data Quality:** Medium - no performance metrics
- **Setup:** Get access token from [Meta for Developers](https://developers.facebook.com)
- **Environment:** `META_ACCESS_TOKEN=your_token`

#### Internal (CompetitorTracker)
- **Cost:** Free
- **Coverage:** Your tracked competitor ads
- **Data Quality:** High - real tracked data
- **Setup:** No setup needed (uses local data)

#### YouTube Trending
- **Cost:** Free (quota limits apply)
- **Coverage:** Trending videos and ads
- **Setup:** Get API key from [Google Cloud Console](https://console.cloud.google.com)
- **Environment:** `YOUTUBE_API_KEY=your_key`

#### TikTok Creative Center
- **Cost:** Free
- **Coverage:** Top performing TikTok ads
- **Setup:** Get API key from [TikTok for Business](https://ads.tiktok.com)
- **Environment:** `TIKTOK_API_KEY=your_key`

---

## Usage Examples

### Example 1: Basic Injection

Inject fitness supplement patterns from all available sources:

```bash
python scripts/inject_knowledge.py inject \
  --query "fitness supplements" \
  --industry health \
  --limit 100
```

**Output:**
```
================================================================================
KNOWLEDGE INJECTION STARTED
  Query: fitness supplements
  Industry: health
  Limit per source: 100
  Dry run: False
================================================================================
Sources to query: foreplay, meta, internal

Fetching from sources: 100%|████████████████| 3/3 [00:12<00:00,  4.12s/it]

FETCH SUMMARY:
  foreplay       :  100 patterns
  meta           :   87 patterns
  internal       :   23 patterns
  TOTAL          :  210 patterns

✓ Inserted 210 patterns into database
✓ Logged injection operation (ID: 42)
================================================================================
INJECTION COMPLETE: 210 patterns
================================================================================
```

---

### Example 2: Specific Sources Only

Inject from Meta Ads Library and internal data only:

```bash
python scripts/inject_knowledge.py inject \
  --query "skincare routine" \
  --industry beauty \
  --sources meta,internal \
  --limit 200
```

---

### Example 3: Dry Run (Test Without Inserting)

Test fetching without inserting into database:

```bash
python scripts/inject_knowledge.py inject \
  --query "meal prep" \
  --industry food \
  --dry-run
```

---

### Example 4: Large Batch Injection

Inject 500 patterns per source for comprehensive coverage:

```bash
python scripts/inject_knowledge.py inject \
  --query "email marketing" \
  --industry ecommerce \
  --limit 500 \
  --sources foreplay,meta
```

---

### Example 5: Check Status

View knowledge base statistics:

```bash
python scripts/inject_knowledge.py status
```

**Output:**
```
================================================================================
KNOWLEDGE BASE STATUS
================================================================================

Configured sources:
  ✓ foreplay
  ✓ meta
  ✗ youtube
  ✗ tiktok
  ✓ kaggle
  ✓ internal

Database statistics:
  Total patterns: 1,247
  Average CTR:    0.0423

Patterns by source:
  foreplay       :   543
  meta           :   421
  internal       :   283

Top industries:
  health         :   487
  beauty         :   321
  ecommerce      :   198
  food           :   156
  fitness        :    85

Recent injections:
  2025-12-03 14:23 | fitness supplements  | health     |  210 patterns
  2025-12-03 12:15 | skincare routine     | beauty     |  156 patterns
  2025-12-02 18:45 | meal prep            | food       |   89 patterns
================================================================================
```

---

### Example 6: Export Backup

Export all patterns to backup file:

```bash
python scripts/inject_knowledge.py export -o backup.jsonl
```

Export specific industry:

```bash
python scripts/inject_knowledge.py export \
  --industry health \
  --limit 1000 \
  -o health_patterns.jsonl
```

---

### Example 7: Import from CSV

Import competitor ads from CSV file:

```bash
python scripts/inject_knowledge.py import \
  -i data/competitor_ads.csv \
  --industry health
```

---

### Example 8: Clear Test Data

Delete all patterns from a test namespace:

```bash
python scripts/inject_knowledge.py clear \
  --namespace test_import \
  --force
```

---

## CSV Import Format

### Required Columns

Create a CSV file with these columns for importing:

```csv
source,hook_text,hook_type,emotional_triggers,performance_tier,industry,ctr
foreplay,"Lose 10 lbs in 14 days",urgency_scarcity,"urgency,transformation",top_10_percent,health,0.045
meta,"Secret to clear skin revealed",curiosity_gap,"curiosity,desire",top_1_percent,beauty,0.068
internal,"Stop wasting money on supplements",problem_agitation,"pain,authority",average,health,0.032
```

### Column Definitions

| Column | Required | Description | Example |
|--------|----------|-------------|---------|
| `source` | Yes | Data source identifier | `foreplay`, `meta`, `internal` |
| `hook_text` | Yes | Ad hook/opening text | "Lose 10 lbs in 14 days" |
| `hook_type` | No | Hook classification | `urgency_scarcity`, `curiosity_gap` |
| `emotional_triggers` | No | Comma-separated triggers | `urgency,transformation` |
| `performance_tier` | No | Performance classification | `top_1_percent`, `top_10_percent` |
| `industry` | Yes | Industry category | `health`, `beauty`, `ecommerce` |
| `ctr` | No | Click-through rate | `0.045` (4.5%) |
| `transcript` | No | Full ad transcript | Full text content |
| `visual_style` | No | Visual description | `before_after`, `talking_head` |
| `pacing` | No | Pacing style | `fast`, `medium`, `slow` |
| `cta_style` | No | Call-to-action style | `urgent`, `soft_sell` |

### Sample CSV Template

Download template: `/home/user/geminivideo/data/competitor_ads_template.csv`

---

## Troubleshooting

### Issue: "psycopg2 not installed"

**Solution:**
```bash
pip install psycopg2-binary
```

### Issue: "DATABASE_URL not configured"

**Solution:**
```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/geminivideo
```

Or add to `.env` file:
```
DATABASE_URL=postgresql://user:password@localhost:5432/geminivideo
```

### Issue: "Table 'winning_patterns' does not exist"

**Solution:** Run database migration:
```bash
psql $DATABASE_URL -f database_migrations/002_feedback_and_knowledge.sql
```

### Issue: API rate limits

**For Meta Ads Library:**
- Rate limit: 200 calls per hour per user
- Solution: Use `--limit` to reduce batch size
- Add delays between calls with `--sequential` flag

**For Foreplay:**
- Rate limit: Varies by plan
- Solution: Contact Foreplay support for rate limit increase

### Issue: No data from sources

**Check configuration:**
```bash
python scripts/inject_knowledge.py status
```

Look for ✓ marks next to sources. ✗ means API key not configured.

### Issue: Low pattern counts

**Possible causes:**
1. Query too specific - Try broader terms
2. Industry mismatch - Check source has data for your industry
3. API limits - Check error logs

**Solution:**
```bash
# Use verbose logging to see detailed errors
python scripts/inject_knowledge.py inject \
  --query "your query" \
  --industry health \
  --verbose
```

Check log file in `/home/user/geminivideo/logs/` for detailed error messages.

---

## Advanced Usage

### Batch Processing Multiple Queries

Create a shell script:

```bash
#!/bin/bash
# inject_batch.sh

queries=(
  "fitness supplements:health"
  "skincare routine:beauty"
  "meal prep:food"
  "email templates:marketing"
)

for query_industry in "${queries[@]}"; do
  IFS=':' read -r query industry <<< "$query_industry"

  echo "Injecting: $query ($industry)"
  python scripts/inject_knowledge.py inject \
    --query "$query" \
    --industry "$industry" \
    --limit 200

  sleep 5  # Rate limit protection
done
```

### Scheduled Daily Injections

Add to crontab:

```bash
# Run daily at 2 AM
0 2 * * * cd /home/user/geminivideo && python scripts/inject_knowledge.py inject --query "trending fitness" --industry health --limit 100 >> /var/log/knowledge_injection.log 2>&1
```

### Integration with CI/CD

```yaml
# .github/workflows/knowledge_injection.yml
name: Daily Knowledge Injection

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC

jobs:
  inject:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install -r scripts/requirements.txt

      - name: Inject knowledge
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          META_ACCESS_TOKEN: ${{ secrets.META_ACCESS_TOKEN }}
        run: |
          python scripts/inject_knowledge.py inject \
            --query "fitness" \
            --industry health \
            --limit 100
```

---

## Support

For issues or questions:

1. Check logs in `/home/user/geminivideo/logs/`
2. Run with `--verbose` flag for detailed output
3. Review database migration: `database_migrations/002_feedback_and_knowledge.sql`
4. Check environment variables: `python scripts/inject_knowledge.py status`

---

## Related Documentation

- [10X ROI Architecture](/home/user/geminivideo/10X_ROI_ARCHITECTURE.md)
- [Database Schema](/home/user/geminivideo/database_schema.sql)
- [Meta Ads Pattern Miner](/home/user/geminivideo/scripts/meta_ads_library_pattern_miner.py)
- [Market Intel Service](/home/user/geminivideo/services/market-intel/README.md)
