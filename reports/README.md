# Validation Reports Directory

This directory stores pre-flight validation reports.

## Files Generated

Reports are automatically generated with timestamp in filename:

- `pre-flight-YYYYMMDD_HHMMSS.txt` - Terminal output
- `pre-flight-YYYYMMDD_HHMMSS.json` - Machine-readable JSON
- `pre-flight-YYYYMMDD_HHMMSS.md` - Markdown report
- `pre-flight-YYYYMMDD_HHMMSS.pdf` - PDF report (optional)

## Usage

Reports are automatically generated when running:

```bash
./scripts/pre-flight.sh
```

## Retention

Keep reports for:
- Last 7 days of development
- All production deployments
- All investor demos

## Example Files

```
reports/
├── pre-flight-20251205_143022.txt
├── pre-flight-20251205_143022.json
├── pre-flight-20251205_143022.md
└── pre-flight-20251205_143022.pdf
```

## View Latest Report

```bash
ls -lt reports/ | head -5
cat reports/pre-flight-*.txt | tail -100
```
