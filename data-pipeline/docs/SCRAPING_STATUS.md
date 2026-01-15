# Parcel Scraping Status - Handoff Document

> **Last Updated**: January 13, 2026 @ 12:45 AM CST
> **Handoff To**: Server with more RAM
> **Current Machine**: MacBook (limited RAM)

## Current Running Scrapers (As of Handoff)

```bash
# Check what's still running
ps aux | grep export_county_parcels | grep -v grep
```

### Active Jobs at Handoff:
| Config | State | Status |
|--------|-------|--------|
| TX_STATEWIDE | Texas | Running - needs 32GB+ RAM |
| CA_LOS_ANGELES | California | Running |
| CA_SAN_DIEGO | California | Running |
| OH_FRANKLIN | Ohio | Running |
| PA_ALLEGHENY | Pennsylvania | Running |
| PA_STATEWIDE | Pennsylvania | Running |
| MI_WAYNE | Michigan | Running |
| WI_STATEWIDE | Wisconsin | Running |
| NV_CLARK | Nevada | Running |
| WA_KING | Washington | Running |

---

## State Completion Status (46/50 States Have Data)

### ✅ COMPLETE (100%) - 17 States
No action needed - ready for MapLibre:

| State | Size | PMTiles |
|-------|------|---------|
| AK | 258MB | ✅ |
| CA | 19.4GB | ✅ |
| CO | 5.2GB | ✅ |
| CT | 2.8GB | ✅ |
| DE | 391MB | ✅ |
| HI | 424MB | ✅ |
| IA | 2.2GB | ✅ |
| MA | 4.4GB | ✅ |
| ND | 881MB | ✅ |
| NH | 871MB | ✅ |
| NV | 2.5GB | ✅ |
| SC | 2.8GB | ✅ |
| TN | 3.2GB | ✅ |
| UT | 1.3GB | ✅ |
| WV | 1.9GB | ✅ |

### 🔄 IN PROGRESS - Need More Scraping

| State | Current | Expected | % | Priority Configs to Run |
|-------|---------|----------|---|------------------------|
| **TX** | 4.2GB | 22GB | 19% | `TX_STATEWIDE`, `TX_STATEWIDE_RECENT` |
| **PA** | 422MB | 4.5GB | 9% | `PA_STATEWIDE`, `PA_PASDA_STATEWIDE` |
| **NY** | 3.2GB | 7GB | 46% | `NY_STATEWIDE_V2` |
| **FL** | 2.9GB | 8GB | 36% | `FL_STATEWIDE` (may need rate limiting) |
| **GA** | 1.1GB | 3.5GB | 33% | `GA_FULTON`, `GA_COBB`, `GA_DEKALB` |
| **MI** | 1.8GB | 3.5GB | 51% | `MI_WAYNE`, `MI_OAKLAND`, `MI_MACOMB` |
| **OH** | 2.8GB | 4.5GB | 62% | `OH_STATEWIDE`, `OH_CUYAHOGA`, `OH_FRANKLIN` |
| **IL** | 740MB | 4GB | 18% | `IL_COOK`, `IL_DUPAGE`, `IL_LAKE` |
| **WI** | 1.2GB | 2.4GB | 48% | `WI_STATEWIDE` |
| **MN** | 2.0GB | 2.2GB | 92% | Almost done! |
| **NM** | 761MB | 0.8GB | 93% | Almost done! |
| **AZ** | 2.0GB | 2.5GB | 81% | `AZ_MARICOPA`, `AZ_PIMA` |

### ❌ FAILED/MISSING - Need Attention

| State | Issue | Recommended Action |
|-------|-------|-------------------|
| **AR** | API not responding | Find alternative endpoint - try county-level |
| **OK** | DNS errors | Check if endpoint URL changed |
| **ME** | SSL certificate errors | Run with `--insecure` or update certifi |
| **VT** | API errors | Find alternative source |
| **RI** | No config exists | Research RI GIS portal, add config |
| **FL** | 403 Forbidden on some counties | Add rate limiting, try `FL_STATEWIDE` |
| **DC** | Empty | Small area - may need manual config |
| **IN** | 0% | Run `IN_STATEWIDE` |
| **MD** | 0% | Run `MD_STATEWIDE` |
| **NC** | 0% in geojson folder | Run `NC_STATEWIDE` |
| **NJ** | 0% in geojson folder | Run `NJ_STATEWIDE` |
| **VA** | 0% in geojson folder | Run `VA_STATEWIDE` |
| **WA** | 0% in geojson folder | Run `WA_STATEWIDE` |
| **MT** | 0% in geojson folder | Run `MT_STATEWIDE` |

---

## Priority Commands for Server

### Step 1: Pull Latest Code
```bash
cd /home/exx/Documents/C/hitd_maps
git pull origin main
```

### Step 2: Install Dependencies
```bash
# Python
pip install pyproj pmtiles requests tqdm

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y tippecanoe awscli jq

# Verify
tippecanoe --version
python3 --version
```

### Step 3: Run High-Priority Scrapers (Parallel)
```bash
cd data-pipeline

# Texas - MOST IMPORTANT (28M parcels, needs 32GB+ RAM)
python3 scripts/export_county_parcels.py TX_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py TX_STATEWIDE_RECENT -o output/geojson &

# New York (9M parcels)
python3 scripts/export_county_parcels.py NY_STATEWIDE_V2 -o output/geojson &

# Pennsylvania
python3 scripts/export_county_parcels.py PA_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py PA_PASDA_STATEWIDE -o output/geojson &

# Florida
python3 scripts/export_county_parcels.py FL_STATEWIDE -o output/geojson &

# Missing States
python3 scripts/export_county_parcels.py IN_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py MD_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py NC_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py NJ_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py VA_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py WA_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py MT_STATEWIDE -o output/geojson &
```

### Step 4: Run Medium-Priority Scrapers
```bash
# Ohio
python3 scripts/export_county_parcels.py OH_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py OH_CUYAHOGA -o output/geojson &
python3 scripts/export_county_parcels.py OH_FRANKLIN -o output/geojson &

# Georgia
python3 scripts/export_county_parcels.py GA_FULTON -o output/geojson &
python3 scripts/export_county_parcels.py GA_COBB -o output/geojson &
python3 scripts/export_county_parcels.py GA_DEKALB -o output/geojson &

# Michigan
python3 scripts/export_county_parcels.py MI_WAYNE -o output/geojson &
python3 scripts/export_county_parcels.py MI_OAKLAND -o output/geojson &

# Illinois
python3 scripts/export_county_parcels.py IL_COOK -o output/geojson &
```

### Step 5: Monitor Progress
```bash
# Count running scrapers
ps aux | grep export_county_parcels | grep -v grep | wc -l

# List all running
ps aux | grep export_county_parcels | grep -v grep | \
  sed 's/.*export_county_parcels.py //' | sed 's/ -o.*//'

# Check memory usage
ps aux | grep export_county_parcels | grep -v grep | \
  awk '{print $12, "| Mem:", int($6/1024)"MB"}'

# Check output folder sizes
du -sh output/geojson/*/
```

### Step 6: Generate PMTiles (After Scraping Complete)
```bash
# For each state with new data
python3 scripts/convert_to_pmtiles.py output/geojson/tx output/tiles/parcels_tx.pmtiles
python3 scripts/convert_to_pmtiles.py output/geojson/ny output/tiles/parcels_ny.pmtiles
# etc...

# Or bulk convert
for state in tx ny pa fl ga mi oh il; do
  python3 scripts/convert_to_pmtiles.py output/geojson/$state output/tiles/parcels_$state.pmtiles
done
```

### Step 7: Upload to Cloudflare R2
```bash
# Set credentials
export AWS_ACCESS_KEY_ID=YOUR_R2_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=YOUR_R2_SECRET_KEY

# Upload all PMTiles
./scripts/bulk_upload_r2.sh

# Or single file
aws s3 cp output/tiles/parcels_tx.pmtiles \
  s3://gspot-tiles/parcels/parcels_tx.pmtiles \
  --endpoint-url https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com
```

---

## Cloudflare R2 Details

| Setting | Value |
|---------|-------|
| Bucket | `gspot-tiles` |
| Account ID | `551bf8d24bb6069fbaa10e863a672fd5` |
| Public URL | `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev` |
| Endpoint | `https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com` |

---

## RAM Requirements

| Task | Recommended RAM |
|------|-----------------|
| Single county (<500K parcels) | 4GB |
| Medium state (1-5M parcels) | 8GB |
| Large state (5-15M parcels) | 16GB |
| Texas (28M parcels) | 32GB+ |
| Multiple parallel scrapers | 64GB+ |

---

## Key Files

| File | Purpose |
|------|---------|
| `scripts/export_county_parcels.py` | Main scraper with 200+ configs |
| `scripts/reproject_geojson.py` | Convert EPSG:3857 → WGS84 |
| `scripts/convert_to_pmtiles.py` | GeoJSON → PMTiles |
| `scripts/bulk_upload_r2.sh` | Upload to Cloudflare R2 |
| `docs/TECHNICAL_SPEC.md` | Full documentation |
| `docs/DATA_FRESHNESS.md` | Update tracking |

---

## After Completion Checklist

- [ ] All 50 states scraped
- [ ] Coordinates reprojected to WGS84
- [ ] PMTiles generated for each state
- [ ] Uploaded to Cloudflare R2
- [ ] Tested in MapLibre preview
- [ ] Updated DATA_FRESHNESS.md with completion dates
