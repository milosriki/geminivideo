# Campaign Performance Report Generator

**Agent 18** - Professional PDF & Excel Reports for Elite Marketers

## Overview

A comprehensive report generation system that creates investment-grade performance reports for showing to clients, stakeholders, board members, and investors.

## Features

### Report Types

1. **Campaign Performance**
   - Overall campaign metrics
   - Spend, ROAS, conversions, CTR breakdown
   - Campaign-by-campaign analysis

2. **Ad Creative Analysis**
   - Which creatives performed best
   - Hook type analysis (problem_solution, social_proof, transformation)
   - Video length and engagement patterns

3. **Audience Insights**
   - Demographics (age, gender)
   - Placement performance (Facebook Feed, Instagram Stories, etc.)
   - Device breakdown (mobile vs desktop)

4. **ROAS Breakdown**
   - Revenue attribution by channel
   - Attribution window analysis (1-day click, 7-day click)
   - Campaign-level ROAS comparison

5. **Weekly Summary**
   - Week-over-week comparison
   - Trend analysis
   - Performance changes

6. **Monthly Executive**
   - Executive summary for C-suite
   - Growth trends
   - Top campaigns
   - Strategic recommendations

### Output Formats

#### PDF Reports
- Professional layout using ReportLab
- Company branding (logo support)
- Executive summary section
- Key metrics with large numbers
- Data tables with formatting
- Insights with colored boxes
- Actionable recommendations
- Multi-page support

#### Excel Reports
- Multiple worksheets:
  - Executive Summary
  - Campaign Details
  - Insights
  - Recommendations
  - Raw Data (for pivot tables)
- Professional styling
- Color-coded cells
- Charts and visualizations
- Pivot-ready data structure

## Architecture

```
/services/ml-service/src/reports/
├── report_generator.py     # Core business logic
├── pdf_builder.py          # PDF generation (ReportLab)
├── excel_builder.py        # Excel generation (openpyxl)
├── templates/              # HTML templates (future use)
└── README.md              # This file
```

## API Endpoints

### Generate Report
```
POST /api/reports/generate
```

**Request:**
```json
{
  "report_type": "campaign_performance",
  "format": "pdf",
  "start_date": "2024-11-01",
  "end_date": "2024-11-30",
  "campaign_ids": ["camp-001", "camp-002"],
  "company_name": "Acme Corporation",
  "company_logo": "/path/to/logo.png"
}
```

**Response:**
```json
{
  "success": true,
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "report_type": "campaign_performance",
  "format": "pdf",
  "file_path": "/tmp/reports/550e8400-e29b-41d4-a716-446655440000.pdf",
  "download_url": "/api/reports/550e8400-e29b-41d4-a716-446655440000/download",
  "generated_at": "2024-12-05T14:30:00Z",
  "summary": {
    "campaigns_analyzed": 12,
    "date_range": {
      "start": "2024-11-01",
      "end": "2024-11-30"
    }
  }
}
```

### List Reports
```
GET /api/reports?limit=20
```

### Download Report
```
GET /api/reports/:id/download
```

### Delete Report
```
DELETE /api/reports/:id
```

### Get Templates
```
GET /api/reports/templates
```

## Usage Examples

### Python (Backend)

```python
from src.reports.report_generator import ReportGenerator, ReportType, ReportFormat
from src.reports.pdf_builder import generate_pdf_report
from datetime import datetime, timedelta

# Initialize generator
generator = ReportGenerator(db_pool=pool)

# Generate report
report_data = await generator.generate_report(
    report_type=ReportType.CAMPAIGN_PERFORMANCE,
    format=ReportFormat.PDF,
    start_date=datetime(2024, 11, 1),
    end_date=datetime(2024, 11, 30),
    company_name="Acme Corp"
)

# Build PDF
pdf_path = generate_pdf_report(
    report_content=report_data['content'],
    output_path="/tmp/report.pdf"
)
```

### TypeScript (Frontend)

```typescript
// Generate report
const response = await fetch('/api/reports/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    report_type: 'campaign_performance',
    format: 'pdf',
    start_date: '2024-11-01',
    end_date: '2024-11-30',
    company_name: 'Acme Corp'
  })
});

const data = await response.json();

// Download report
window.location.href = `/api/reports/${data.report_id}/download`;
```

### cURL

```bash
# Generate report
curl -X POST http://localhost:8000/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "campaign_performance",
    "format": "pdf",
    "start_date": "2024-11-01",
    "end_date": "2024-11-30",
    "company_name": "Acme Corp"
  }'

# Download report
curl -O http://localhost:8000/api/reports/{report_id}/download
```

## Data Sources

Reports pull data from:
- `campaigns` table - Campaign metadata and settings
- `campaign_outcomes` table - Performance metrics
- `ads` table - Ad creative details
- `clips` table - Video clip data
- Real-time calculations - Aggregations and metrics

## Insights & Recommendations

The report generator includes an AI-powered insights engine that:

1. **Analyzes Performance**
   - Identifies high-performing campaigns
   - Detects underperforming areas
   - Calculates trend changes

2. **Generates Insights**
   - Positive highlights (ROAS > 3.0x)
   - Warning flags (CTR declining)
   - Information points (new trends)

3. **Provides Recommendations**
   - Budget optimization suggestions
   - Creative testing ideas
   - Audience expansion opportunities
   - Priority ranking (High/Medium/Low)

## Professional Features

### Branding
- Company logo support (PNG, JPG)
- Custom company name
- Branded color schemes
- Professional typography

### Executive Summary
- One-page overview
- Key metrics highlighted
- Bottom-line conclusions
- Actionable next steps

### Charts & Visualizations
- Spend vs Revenue charts
- ROAS trend lines
- Campaign comparison bars
- Audience demographic breakdowns

### Data Export
- Raw data sheets for custom analysis
- Pivot-ready table structures
- All metrics exportable
- Formula-friendly formatting

## Performance

- **PDF Generation:** ~2-5 seconds for 50-page report
- **Excel Generation:** ~1-3 seconds for 5-worksheet workbook
- **Database Queries:** Optimized with indexes
- **File Size:** PDFs ~500KB-2MB, Excel ~200KB-1MB

## Dependencies

```
reportlab==4.0.7        # PDF generation
openpyxl==3.1.2         # Excel generation
python-dateutil==2.8.2  # Date parsing
```

## Testing

```bash
# Unit tests
pytest services/ml-service/tests/test_reports.py

# Integration tests
pytest services/ml-service/tests/test_report_integration.py

# Generate test report
python -m src.reports.test_generator
```

## Production Deployment

### Environment Variables
```bash
# Optional - custom report storage
REPORT_STORAGE_PATH=/var/reports

# Optional - report retention (days)
REPORT_RETENTION_DAYS=30
```

### Cron Job for Cleanup
```bash
# Clean up old reports daily at 2 AM
0 2 * * * find /tmp/reports -name "*.pdf" -mtime +30 -delete
0 2 * * * find /tmp/reports -name "*.xlsx" -mtime +30 -delete
```

### Security Considerations

1. **Access Control**
   - Reports contain sensitive business data
   - Implement authentication on download endpoints
   - Use signed URLs for time-limited access

2. **Data Privacy**
   - No PII in reports by default
   - Aggregate metrics only
   - Comply with data retention policies

3. **File Storage**
   - Store in secure location
   - Encrypt at rest (if cloud storage)
   - Auto-delete after retention period

## Roadmap

### Future Enhancements

- [ ] PowerPoint export format
- [ ] Scheduled report generation
- [ ] Email delivery integration
- [ ] White-label customization
- [ ] Interactive web reports
- [ ] Custom logo upload UI
- [ ] Report templates marketplace
- [ ] Multi-language support
- [ ] Automated commentary (GPT-4)
- [ ] Competitor benchmarking section

## Support

For issues or feature requests:
- File issue in project repository
- Contact development team
- See main documentation

---

**Built by Agent 18** - Professional reporting for elite marketers managing $5M+ in ad spend.
