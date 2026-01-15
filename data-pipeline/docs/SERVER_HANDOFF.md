# Server Handoff - 512GB RAM Server

> **Date**: January 13, 2026 (Updated 1:15 AM CST)
> **From**: MacBook (limited RAM)
> **To**: 512GB RAM Server
> **Status**: All scrapers stopped, ready for server takeover
> **Total Data Collected**: ~72GB across 46 states

---

## PROMPT FOR CLAUDE VSC ON SERVER

Copy and paste this to Claude on your server:

```
I'm continuing a parcel data scraping project. Please read the handoff document at:
data-pipeline/docs/SERVER_HANDOFF.md

This server has 512GB RAM. I need you to:

1. Read the current scraping status
2. Launch parallel scrapers for ALL incomplete states
3. With 512GB RAM, run as many as possible simultaneously
4. After scraping completes, generate PMTiles and upload to Cloudflare R2

Start by reading the handoff docs and then run the high-priority scrapers.
```

---

## CURRENT STATE COMPLETION

### Current Data Sizes (as of handoff)
```
CA: 9.7GB  |  OH: 7.6GB  |  CO: 5.2GB  |  NJ: 4.9GB  |  VA: 4.7GB
MA: 4.4GB  |  WA: 3.5GB  |  NY: 3.2GB  |  FL: 2.9GB  |  IN: 2.8GB
CT: 2.8GB  |  UT: 2.6GB  |  MD: 2.3GB  |  NC: 2.2GB  |  IA: 2.2GB
TX: 2.1GB  |  MN: 2.0GB  |  WV: 1.9GB  |  TN: 1.6GB  |  SC: 1.4GB
NV: 1.3GB  |  WI: 1.1GB  |  MI: 1.1GB  |  AZ: 1.0GB  |  MT: 955MB
ND: 881MB  |  NH: 871MB  |  NM: 761MB  |  KY: 623MB  |  GA: 587MB
MO: 440MB  |  HI: 424MB  |  DE: 391MB  |  IL: 370MB  |  NE: 276MB
KS: 240MB  |  LA: 234MB  |  OR: 231MB  |  PA: 202MB  |  SD: 177MB
WY: 145MB  |  MS: 122MB  |  ID: 89MB   |  AL: 76MB   |  AK: 258MB
```

### Complete (17 states) - NO ACTION NEEDED
```
AK, CA, CO, CT, DE, HI, IA, MA, ND, NH, NV, SC, TN, UT, WV
```

### Partially Complete - NEED MORE SCRAPING
| State | Current | Target | % | Config to Run |
|-------|---------|--------|---|---------------|
| TX | 4.2GB | 22GB | 19% | TX_STATEWIDE, TX_STATEWIDE_RECENT |
| NY | 3.2GB | 7GB | 46% | NY_STATEWIDE_V2 |
| FL | 2.9GB | 8GB | 36% | FL_STATEWIDE |
| PA | 422MB | 4.5GB | 9% | PA_STATEWIDE, PA_PASDA_STATEWIDE |
| OH | 2.8GB | 4.5GB | 62% | OH_STATEWIDE |
| GA | 1.1GB | 3.5GB | 33% | GA_FULTON, GA_COBB, GA_DEKALB |
| MI | 1.8GB | 3.5GB | 51% | MI_WAYNE, MI_OAKLAND |
| IL | 740MB | 4GB | 18% | IL_COOK, IL_DUPAGE |
| WI | 1.2GB | 2.4GB | 48% | WI_STATEWIDE |
| AZ | 2.0GB | 2.5GB | 81% | AZ_MARICOPA |
| MN | 2.0GB | 2.2GB | 92% | Almost done |
| NM | 761MB | 0.8GB | 93% | Almost done |
| KY | 1.3GB | 1.8GB | 69% | KY_JEFFERSON |
| OR | 462MB | 1.5GB | 30% | OR_MULTNOMAH |
| LA | 466MB | 1.8GB | 25% | LA_ORLEANS, LA_JEFFERSON |
| MO | 882MB | 2.4GB | 36% | MO_JACKSON, MO_ST_CHARLES |
| AL | 286MB | 2GB | 14% | AL_JEFFERSON, AL_MOBILE |
| MS | 392MB | 1.2GB | 32% | MS_STATEWIDE |
| KS | 484MB | 1.2GB | 39% | KS_SEDGWICK |
| NE | 550MB | 0.8GB | 67% | NE_STATEWIDE |
| SD | 213MB | 0.4GB | 52% | SD_MINNEHAHA |
| WY | 183MB | 0.3GB | 60% | WY_STATEWIDE |
| ID | 89MB | 0.6GB | 15% | ID_STATEWIDE |

### Missing/Empty - NEED FULL SCRAPING
| State | Issue | Config to Try |
|-------|-------|---------------|
| IN | Not started | IN_STATEWIDE |
| MD | Not started | MD_STATEWIDE |
| NC | Not started | NC_STATEWIDE |
| NJ | Not started | NJ_STATEWIDE |
| VA | Not started | VA_STATEWIDE |
| WA | Not started | WA_STATEWIDE |
| MT | Not started | MT_STATEWIDE |
| AR | API issues | AR_STATEWIDE (retry) |
| OK | DNS errors | OK_OKLAHOMA, OK_TULSA |
| ME | SSL errors | ME_STATEWIDE (with --insecure) |
| VT | API errors | VT_STATEWIDE (retry) |
| RI | No config | Need to research/add |
| DC | Empty | Small area, low priority |

---

## COMMANDS FOR 512GB SERVER

### Step 1: Setup
```bash
cd /home/exx/Documents/C/hitd_maps
git pull origin main

# Install dependencies
pip install pyproj pmtiles requests tqdm
sudo apt-get install -y tippecanoe awscli jq
```

### Step 2: Run ALL Scrapers in Parallel (512GB can handle this)
```bash
cd data-pipeline

# === HIGH PRIORITY (Big States) ===
python3 scripts/export_county_parcels.py TX_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py TX_STATEWIDE_RECENT -o output/geojson &
python3 scripts/export_county_parcels.py NY_STATEWIDE_V2 -o output/geojson &
python3 scripts/export_county_parcels.py FL_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py PA_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py PA_PASDA_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py OH_STATEWIDE -o output/geojson &

# === MISSING STATES ===
python3 scripts/export_county_parcels.py IN_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py MD_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py NC_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py NJ_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py VA_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py WA_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py MT_STATEWIDE -o output/geojson &

# === PARTIAL STATES ===
python3 scripts/export_county_parcels.py GA_FULTON -o output/geojson &
python3 scripts/export_county_parcels.py GA_COBB -o output/geojson &
python3 scripts/export_county_parcels.py GA_DEKALB -o output/geojson &
python3 scripts/export_county_parcels.py MI_WAYNE -o output/geojson &
python3 scripts/export_county_parcels.py MI_OAKLAND -o output/geojson &
python3 scripts/export_county_parcels.py IL_COOK -o output/geojson &
python3 scripts/export_county_parcels.py IL_DUPAGE -o output/geojson &
python3 scripts/export_county_parcels.py WI_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py AZ_MARICOPA -o output/geojson &
python3 scripts/export_county_parcels.py KY_JEFFERSON -o output/geojson &
python3 scripts/export_county_parcels.py OR_MULTNOMAH -o output/geojson &
python3 scripts/export_county_parcels.py LA_ORLEANS -o output/geojson &
python3 scripts/export_county_parcels.py LA_JEFFERSON -o output/geojson &
python3 scripts/export_county_parcels.py MO_JACKSON -o output/geojson &
python3 scripts/export_county_parcels.py AL_JEFFERSON -o output/geojson &
python3 scripts/export_county_parcels.py MS_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py KS_SEDGWICK -o output/geojson &
python3 scripts/export_county_parcels.py NE_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py ID_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py WY_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py SD_MINNEHAHA -o output/geojson &

# === RETRY FAILED ===
python3 scripts/export_county_parcels.py AR_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py OK_OKLAHOMA -o output/geojson &
python3 scripts/export_county_parcels.py OK_TULSA -o output/geojson &
python3 scripts/export_county_parcels.py ME_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py VT_STATEWIDE -o output/geojson &

echo "Launched $(ps aux | grep export_county_parcels | grep -v grep | wc -l) scrapers"
```

### Step 3: Monitor Progress
```bash
# Count running
ps aux | grep export_county_parcels | grep -v grep | wc -l

# List all with memory
ps aux | grep export_county_parcels | grep -v grep | awk '{print $12, "| Mem:", int($6/1024)"MB"}'

# Watch folder sizes
watch -n 60 'du -sh output/geojson/*/ | sort -hr | head -20'

# Check total RAM usage
free -h
```

### Step 4: After Scraping Complete - Generate PMTiles
```bash
# Generate tiles for all states
for state in tx ny fl pa oh ga mi il wi az mn nm ky or la mo al ms ks ne id wy sd in md nc nj va wa mt ar ok me vt; do
  if [ -d "output/geojson/$state" ]; then
    echo "Processing $state..."
    python3 scripts/convert_to_pmtiles.py output/geojson/$state output/tiles/parcels_$state.pmtiles
  fi
done
```

### Step 5: Upload to Cloudflare R2
```bash
# Set credentials (get from Cloudflare dashboard)
export AWS_ACCESS_KEY_ID=YOUR_R2_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=YOUR_R2_SECRET_KEY

# Bulk upload
./scripts/bulk_upload_r2.sh

# Verify
aws s3 ls s3://gspot-tiles/parcels/ \
  --endpoint-url https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com
```

---

## CLOUDFLARE R2 DETAILS

### Credentials (Already in bulk_upload_r2.sh)
```bash
export AWS_ACCESS_KEY_ID="ecd653afe3300fdc045b9980df0dbb14"
export AWS_SECRET_ACCESS_KEY="c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
```

### Bucket Info
| Setting | Value |
|---------|-------|
| Bucket | `gspot-tiles` |
| Account ID | `551bf8d24bb6069fbaa10e863a672fd5` |
| Public URL | `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev` |
| Endpoint | `https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com` |
| File Pattern | `parcels/parcels_{state}.pmtiles` |

### Upload Commands

```bash
# Option 1: Use the bulk upload script (credentials already embedded)
./scripts/bulk_upload_r2.sh

# Option 2: Manual upload single file
export AWS_ACCESS_KEY_ID="ecd653afe3300fdc045b9980df0dbb14"
export AWS_SECRET_ACCESS_KEY="c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

aws s3 cp output/tiles/parcels_tx.pmtiles \
  s3://gspot-tiles/parcels/parcels_tx.pmtiles \
  --endpoint-url https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com

# Option 3: Upload all PMTiles
for file in output/tiles/*.pmtiles; do
  filename=$(basename "$file")
  echo "Uploading $filename..."
  aws s3 cp "$file" "s3://gspot-tiles/parcels/$filename" \
    --endpoint-url https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com
done

# Option 4: Upload all GeoJSON files
for file in output/geojson/*/*.geojson; do
  filename=$(basename "$file")
  echo "Uploading $filename..."
  aws s3 cp "$file" "s3://gspot-tiles/parcels/$filename" \
    --endpoint-url https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com \
    --no-progress
done
```

### Verify Uploads
```bash
# List all uploaded files
aws s3 ls s3://gspot-tiles/parcels/ \
  --endpoint-url https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com

# Check public URL works
curl -I https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_tx.pmtiles
```

### Access in MapLibre (Flutter/Web)
```dart
// PMTiles URL
final pmtilesUrl = 'https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_tx.pmtiles';
```

---

## EXPECTED COMPLETION

With 512GB RAM running ~35 parallel scrapers:
- **Texas (28M parcels)**: ~2-4 hours
- **New York (9M parcels)**: ~1-2 hours
- **Other states**: ~30min - 1hr each
- **Total estimated**: ~4-6 hours for all states

---

## AFTER COMPLETION CHECKLIST

- [ ] All 50 states have GeoJSON data
- [ ] PMTiles generated for each state
- [ ] Uploaded to Cloudflare R2
- [ ] Verify in MapLibre preview: `open preview/index.html`
- [ ] Update DATA_FRESHNESS.md with completion dates
- [ ] Commit and push results

---

## KEY FILES

| File | Purpose |
|------|---------|
| `scripts/export_county_parcels.py` | Main scraper (200+ configs) |
| `scripts/convert_to_pmtiles.py` | GeoJSON → PMTiles |
| `scripts/bulk_upload_r2.sh` | Upload to R2 |
| `docs/TECHNICAL_SPEC.md` | Full documentation |
