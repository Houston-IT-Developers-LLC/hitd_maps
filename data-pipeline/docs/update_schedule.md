# Data Update Schedule

This document describes the process for keeping parcel data current.

## Update Frequencies by Source Type

| Source Type | Typical Frequency | Our Update Cadence |
|-------------|-------------------|-------------------|
| Statewide portals | Quarterly-Annual | Quarterly |
| County portals | Monthly-Annual | Quarterly |
| FOIA requests | On-demand | Annual |

## Quarterly Update Process

### 1. Check for Updates (Monthly)

Review source portals for new data releases.

```bash
# Check what we have loaded
./scripts/batch_process.sh status

# Compare against sources.json last_checked dates
cat data-pipeline/config/sources.json | jq '.states | to_entries[] | {state: .key, last_checked: .value.primary_source.last_checked}'
```

### 2. Download Updated Data

When a source has new data:

```bash
# Texas
./scripts/download_texas.sh ./downloads "<new_url_from_txgio>"

# Other states - download manually from their portals
# URLs documented in sources.json
```

### 3. Reload and Regenerate

```bash
# Full pipeline for updated states
./scripts/batch_process.sh full TX,WI,FL

# Verify counts match expectations
./scripts/batch_process.sh status
```

### 4. Deploy Updated Tiles

```bash
# Convert to PMTiles
pmtiles convert ./output/tiles/parcels_tx.mbtiles ./output/tiles/parcels_tx.pmtiles

# Upload to CDN
aws s3 cp ./output/tiles/ s3://your-bucket/tiles/ --recursive --include "*.pmtiles"

# Invalidate CDN cache
aws cloudfront create-invalidation --distribution-id XXXXX --paths "/tiles/*"
```

## Source Monitoring

### States with Notifications

Some state portals provide update notifications:

| State | Notification Method |
|-------|---------------------|
| Texas (TxGIO) | TNRIS newsletter, Twitter @TNABOREGIONAL |
| Wisconsin (SCO) | Parcel project page updates |
| Florida (FGDL) | Email list available |
| Minnesota | MN Geospatial Commons RSS |
| Indiana | IndianaMap newsletter |

### Manual Check Schedule

For states without notifications, check portals quarterly:

- **Q1:** First week of January
- **Q2:** First week of April
- **Q3:** First week of July
- **Q4:** First week of October

Update `last_checked` in sources.json after each check.

## Data Quality Validation

After each update, run validation queries:

```sql
-- Check record counts by state
SELECT
  state,
  COUNT(*) as parcels,
  COUNT(DISTINCT county) as counties,
  MAX(imported_at) as last_import
FROM parcels
GROUP BY state
ORDER BY state;

-- Check for geometry issues
SELECT state, COUNT(*) as invalid_geom
FROM parcels
WHERE NOT ST_IsValid(geom)
GROUP BY state
HAVING COUNT(*) > 0;

-- Check for missing required fields
SELECT
  state,
  ROUND(100.0 * COUNT(CASE WHEN owner_name IS NULL OR owner_name = '' THEN 1 END) / COUNT(*), 1) as pct_missing_owner,
  ROUND(100.0 * COUNT(CASE WHEN county IS NULL OR county = '' THEN 1 END) / COUNT(*), 1) as pct_missing_county
FROM parcels
GROUP BY state
ORDER BY pct_missing_owner DESC;

-- Compare to previous import
SELECT
  state,
  source,
  record_count,
  imported_at
FROM import_log
ORDER BY imported_at DESC
LIMIT 20;
```

### Expected Counts by State

| State | Expected Parcels | Tolerance |
|-------|------------------|-----------|
| TX | 28,000,000 | ±5% |
| WI | 3,500,000 | ±5% |
| FL | 10,000,000 | ±5% |
| PA | 5,000,000 | ±5% |
| OH | 6,000,000 | ±5% |

If counts differ by more than tolerance, investigate before deploying.

## Rollback Procedure

If an update introduces issues:

### 1. Keep Backups

```bash
# Before update, backup current tiles
cp parcels_tx.mbtiles parcels_tx.mbtiles.backup-$(date +%Y%m%d)
```

### 2. Restore from Backup

```bash
# Restore previous tiles
mv parcels_tx.mbtiles.backup-20260101 parcels_tx.mbtiles

# Re-upload to CDN
aws s3 cp parcels_tx.mbtiles s3://bucket/tiles/
aws cloudfront create-invalidation --distribution-id XXXXX --paths "/tiles/parcels_tx*"
```

### 3. Database Rollback

```sql
-- Check import log for previous good import
SELECT * FROM import_log
WHERE state = 'TX'
ORDER BY imported_at DESC;

-- Delete problematic import
DELETE FROM parcels
WHERE state = 'TX'
  AND source_date > '2026-01-01';

-- Re-import from backup if available
```

## Cost Tracking

Track data acquisition costs per state:

| State | Source | Cost | Last Update |
|-------|--------|------|-------------|
| TX | TxGIO | $0 | 2026-01-09 |
| WI | WI SCO | $0 | - |
| FL | FGDL | $0 | - |
| PA | PASDA | $0 | - |
| OH | OGRIP | $0 | - |
| MN | MN Geospatial | $0 | - |
| IN | IndianaMap | $0 | - |
| NC | NC OneMap | $0 | - |
| VA | VGIN | $0 | - |
| AR | GeoStor | $0 | - |

**Running Total:** $0

**vs. Commercial Aggregator:** $80,000+/year

## Automation (Future Enhancement)

GitHub Actions workflow for quarterly updates:

```yaml
# .github/workflows/quarterly-update.yml
name: Quarterly Parcel Update

on:
  schedule:
    - cron: '0 0 1 1,4,7,10 *'  # First of Jan, Apr, Jul, Oct
  workflow_dispatch:  # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check for source updates
        run: ./scripts/check_updates.sh

      - name: Download updated data
        run: ./scripts/download_updates.sh

      - name: Load to staging DB
        run: ./scripts/batch_process.sh load tier1

      - name: Validate data quality
        run: ./scripts/validate.sh

      - name: Generate tiles
        run: ./scripts/batch_process.sh tiles tier1

      - name: Deploy to CDN
        run: ./scripts/deploy_tiles.sh
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

      - name: Notify on completion
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {"text": "Parcel data update complete"}
```

This can be implemented in Phase 10 (Launch Preparation).

## Emergency Updates

For critical updates (e.g., major boundary changes):

1. Download new data immediately
2. Load to staging database
3. Validate against production
4. Deploy during low-traffic window
5. Monitor for issues

## Contact Points

| State | Agency | Contact |
|-------|--------|---------|
| TX | TNRIS | data@tnris.org |
| WI | SCO | sco@doa.wi.gov |
| FL | FGDL | geoplan@ufl.edu |
| MN | MN Geospatial | gisinfo.mngeo@state.mn.us |

---

*Last updated: 2026-01-10*
