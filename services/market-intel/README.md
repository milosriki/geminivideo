# Market Intelligence Service

## Overview

The Market Intelligence Service replaces fake/hardcoded data with REAL competitor ad tracking and analysis.

## Components

### 1. CSVImporter (`csv_importer.py`)
Imports competitor ad data from CSV files and performs real pattern analysis.

**Usage:**
```python
from services.market_intel import CSVImporter

# Import ads from CSV
ads = CSVImporter.import_competitor_ads('/path/to/ads.csv')

# Analyze patterns
patterns = CSVImporter.analyze_patterns(ads)
```

**CSV Format:**
```csv
brand,hook_text,engagement,platform,views,url
Brand Name,Hook text here,0.085,Meta,125000,https://...
```

### 2. CompetitorTracker (`competitor_tracker.py`)
Tracks competitor ads over time and analyzes trends.

**Usage:**
```python
from services.market_intel import CompetitorTracker

# Initialize tracker
tracker = CompetitorTracker()

# Track a new ad
tracker.track_ad({
    "brand": "Competitor X",
    "hook_text": "Amazing offer inside",
    "engagement": 0.075,
    "platform": "Meta",
    "views": 100000,
    "url": "https://..."
})

# Get trends
trends = tracker.analyze_trends(days=30)

# Get winning hooks
top_hooks = tracker.get_winning_hooks(top_n=10)
```

### 3. Pattern Miner (`scripts/meta_ads_library_pattern_miner.py`)
Analyzes patterns from real data sources (CSV or tracker).

**Usage:**
```bash
# Run with CSV data
python scripts/meta_ads_library_pattern_miner.py

# The script will automatically:
# 1. Look for data/competitor_ads.csv
# 2. Fall back to CompetitorTracker database
# 3. Analyze real patterns
# 4. Update hook configs with real metrics
```

## API Endpoints (Gateway Integration)

Add these endpoints to `services/gateway-api`:

### GET /api/market-intel/trends
Get current market trends from tracked competitors.

**Query Parameters:**
- `days` (default: 30): Analyze trends from last N days

**Response:**
```json
{
  "period_days": 30,
  "total_ads": 150,
  "hook_patterns": {
    "curiosity_gap": {"count": 45, "percentage": 30},
    "urgency": {"count": 38, "percentage": 25.3}
  },
  "platform_distribution": {"Meta": 85, "TikTok": 65},
  "data_source": "real_tracked_data"
}
```

### GET /api/market-intel/competitors/{brand}/ads
Get ads for a specific competitor.

**Response:**
```json
{
  "brand": "Competitor X",
  "total_ads": 25,
  "ads": [...]
}
```

### GET /api/market-intel/winning-hooks
Get top performing hooks based on real engagement data.

**Query Parameters:**
- `top_n` (default: 10): Number of top hooks to return

**Response:**
```json
{
  "top_hooks": [
    {
      "hook_text": "Discover the secret...",
      "brand": "Example",
      "engagement": 0.092,
      "platform": "Meta"
    }
  ]
}
```

### POST /api/market-intel/import-csv
Import competitor ads from CSV file.

**Body:** multipart/form-data with 'file' field

**Response:**
```json
{
  "imported": 50,
  "patterns": {...},
  "status": "success"
}
```

## Data Flow

```
CSV Import → CompetitorTracker → Pattern Miner → Hook Config Updates
     ↓              ↓                   ↓               ↓
   Ads DB    Trend Analysis      Real Patterns   Production Use
```

## Migration from Fake Data

### Before (FAKE):
- Hardcoded numbers (345, 289, 0.72...)
- No real competitor data
- Made-up success rates
- Fake visual analysis

### After (REAL):
- CSV imports of real ads
- Actual engagement metrics
- Real competitor tracking
- Data-driven pattern analysis

## Getting Started

1. **Prepare your data:**
   ```bash
   # Use the template
   cp data/competitor_ads_template.csv data/competitor_ads.csv

   # Edit with real competitor data
   ```

2. **Import data:**
   ```python
   from services.market_intel import CompetitorTracker, CSVImporter

   # Via CSV
   ads = CSVImporter.import_competitor_ads('data/competitor_ads.csv')

   # Track them
   tracker = CompetitorTracker()
   for ad in ads:
       tracker.track_ad(ad)
   ```

3. **Run analysis:**
   ```bash
   python scripts/meta_ads_library_pattern_miner.py
   ```

4. **Use insights:**
   - Pattern mining report: `logs/pattern_mining_report.json`
   - Updated hook configs: `shared/config/hooks/hook_templates.json`

## Future Enhancements

- [ ] Meta Ads Library API integration
- [ ] Automated scraping (Apify/PhantomBuster)
- [ ] Real-time competitor monitoring
- [ ] Computer vision for visual analysis
- [ ] Database backend (replace JSON files)
- [ ] Webhook notifications for new competitive insights
