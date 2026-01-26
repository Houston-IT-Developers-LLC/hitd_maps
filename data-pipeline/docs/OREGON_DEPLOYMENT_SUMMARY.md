# Oregon Counties Deployment Summary
**Date:** 2026-01-25
**Status:** Partial Deployment Complete

## Objective
Deploy parcel data for top 5 missing Oregon counties by population to improve coverage from 5% (2 counties) to significant Portland metro and major city coverage.

## Priority Counties Target
1. **Clackamas** (421K pop) - Portland metro
2. **Lane** (382K pop) - Eugene
3. **Marion** (345K pop) - Salem
4. **Jackson** (223K pop) - Medford
5. **Deschutes** (198K pop) - Bend

---

## ✅ Completed Deployments

### Lane County (Eugene)
- **Status:** ✅ DEPLOYED
- **Population:** 382,000
- **Features:** 158,979 parcels
- **Source:** Lane County GIS
- **API:** `https://lcmaps.lanecounty.org/arcgis/rest/services/PlanMaps/AddressParcel/MapServer/1`
- **File:** `parcels_or_lane.pmtiles`
- **Size:** 127.9 MB
- **R2 URL:** `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_or_lane.pmtiles`
- **Download Time:** 71 seconds
- **Processing:** GeoJSON → PMTiles (tippecanoe)
- **Zoom Levels:** 8-15
- **Projection:** WGS84 (EPSG:4326)

---

## 🔍 Data Sources Found (Manual Download Required)

### Clackamas County (Portland Metro)
- **Population:** 421,000
- **Challenge:** Oregon Dept of Forestry MapServer is display-only (no query/download support)
- **Alternative Sources:**
  1. **Oregon Metro RLIS** (Recommended)
     - Covers Clackamas, Multnomah, Washington counties
     - Portal: https://rlisdiscovery.oregonmetro.gov/datasets/9d3c396ffad44649bc7451465aa300f0
     - Format: Download via portal (Shapefile/GeoPackage)
     - Updated: Quarterly
     - **Action:** Manual download from portal → convert to GeoJSON → PMTiles

  2. **Clackamas County GIS Data Portal**
     - URL: https://www.clackamas.us/gis/data-portal
     - Format: Shapefile downloads
     - Contact: gisquestions@clackamas.us

### Marion County (Salem)
- **Population:** 345,000
- **Sources Found:**
  1. **Marion County Open Data Portal**
     - URL: https://gis-marioncounty.opendata.arcgis.com/
     - **Note:** Parcels available for instant download WITHOUT ownership info
     - For parcels WITH ownership: Email GIS@co.marion.or.us
     - Format: Shapefile/GeoJSON
     - **Action:** Download from portal OR request ownership data via email

  2. **Oregon Dept of Forestry** (Display only)
     - Layer 23: https://gis.odf.oregon.gov/ags1/rest/services/WebMercator/TaxlotsDisplay/MapServer/23
     - Not suitable for bulk download

### Jackson County (Medford)
- **Population:** 223,000
- **Sources Found:**
  1. **Jackson County Open GIS**
     - URL: https://gis.jacksoncountyor.gov/datasets/tax-lots/about
     - Hub: https://hub.arcgis.com/datasets/JCGIS::tax-lots/about
     - Format: Tax lot polygons with ownership/account info
     - Update Frequency: Weekly
     - **Action:** Download from ArcGIS Hub page

  2. **Oregon Dept of Forestry** (Display only)
     - Layer 14: Not suitable for download

### Deschutes County (Bend)
- **Population:** 198,000
- **Sources Found:**
  1. **Deschutes County Data Portal**
     - URL: https://data.deschutes.org/datasets/deschutes::taxlots/about
     - Hub: https://hub.arcgis.com/maps/901cdd4a5ca24cc3b72cc8e3e0f11f02
     - Formats: Shapefile, File Geodatabase, KML, CSV, GeoJSON
     - API: GeoServices available
     - **Action:** Download from data portal

  2. **Deschutes County GIS Services**
     - URL: https://www.deschutes.org/it/page/gis-data-services
     - Developer Resources: https://www.deschutes.org/it/page/developer-resources

---

## 📊 Coverage Status

### Before Deployment
- **Oregon Coverage:** 5% (2 counties)
- **Files:** parcels_or_lane, parcels_or_multnomah_v2

### After Lane County Deployment
- **Oregon Coverage:** 8% (3 counties)
- **Files:** +parcels_or_lane (159K parcels)
- **Total Files:** 237 parcel datasets nationwide

### Potential After Full Deployment
- **Coverage:** ~30% if all 5 priority counties deployed
- **Additional Parcels:** Est. 400K-500K features
- **Coverage Area:** Portland metro, Salem, Eugene, Medford, Bend

---

## 🛠️ Processing Pipeline Used

### Lane County Workflow
```bash
# 1. Download from ArcGIS REST API (MapServer)
python3 scripts/download_oregon_counties.py --county Lane --workers 4

# 2. Data already in WGS84, no reprojection needed
# Source: https://lcmaps.lanecounty.org/.../MapServer/1 (outSR=4326)

# 3. Convert to PMTiles
tippecanoe -o data/pmtiles/parcels_or_lane.pmtiles \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  --force \
  --maximum-zoom=14 \
  --minimum-zoom=8 \
  --layer=parcels \
  --name="Lane County Oregon Parcels" \
  --attribution="Lane County" \
  data/downloads/parcels_or_lane.geojson

# 4. Upload to R2
python3 -c "import boto3; ..." # Upload via boto3

# 5. Add to valid_parcels.json
# Already present in file

# 6. Regenerate coverage report
python3 scripts/generate_coverage_report.py
```

---

## 📋 Next Steps for Remaining Counties

### Recommended Approach

#### 1. Download via Open Data Portals (Manual)
Each county has different download mechanisms. Visit portals and download:
- **Clackamas:** Oregon Metro RLIS → Taxlots (Public) dataset
- **Marion:** gis-marioncounty.opendata.arcgis.com → Parcels dataset
- **Jackson:** gis.jacksoncountyor.gov → Tax Lots dataset
- **Deschutes:** data.deschutes.org → Taxlots dataset

#### 2. Convert Downloads to GeoJSON
```bash
# If Shapefile
ogr2ogr -f GeoJSON -t_srs EPSG:4326 output.geojson input.shp

# If GeoPackage
ogr2ogr -f GeoJSON -t_srs EPSG:4326 output.geojson input.gpkg

# If already GeoJSON, just ensure WGS84
ogr2ogr -f GeoJSON -t_srs EPSG:4326 output_wgs84.geojson input.geojson
```

#### 3. Convert to PMTiles
```bash
tippecanoe -o data/pmtiles/parcels_or_[county].pmtiles \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  --force \
  --maximum-zoom=14 \
  --minimum-zoom=8 \
  --layer=parcels \
  --name="[County] County Oregon Parcels" \
  --attribution="[County] County" \
  output_wgs84.geojson
```

#### 4. Upload to R2
```bash
python3 scripts/upload_to_r2_boto3.py \
  data/pmtiles/parcels_or_[county].pmtiles \
  parcels/parcels_or_[county].pmtiles
```

#### 5. Update Tracking
```bash
# Add to valid_parcels.json
echo '  "parcels_or_[county]",' >> data/valid_parcels.json

# Regenerate coverage
python3 scripts/generate_coverage_report.py
```

---

## 🔐 API Endpoints Discovered

### Working REST APIs (Downloadable)
| County | API URL | Type | Features | Notes |
|--------|---------|------|----------|-------|
| Lane | `https://lcmaps.lanecounty.org/arcgis/rest/services/PlanMaps/AddressParcel/MapServer/1` | MapServer | 158,979 | ✅ Deployed |

### Display-Only APIs (Not Downloadable)
| County | API URL | Type | Notes |
|--------|---------|------|-------|
| All OR | `https://gis.odf.oregon.gov/ags1/rest/services/WebMercator/TaxlotsDisplay/MapServer` | MapServer | Statewide display service, query disabled |
| Clackamas | Above + `/2` | MapServer Layer | Use Oregon Metro RLIS instead |
| Marion | Above + `/23` | MapServer Layer | Use county portal instead |
| Jackson | Above + `/14` | MapServer Layer | Use county portal instead |
| Deschutes | Above + `/8` | MapServer Layer | Use county portal instead |

### Download Portals (Manual)
- **Oregon Metro RLIS:** https://rlisdiscovery.oregonmetro.gov/
- **Marion County:** https://gis-marioncounty.opendata.arcgis.com/
- **Jackson County:** https://gis.jacksoncountyor.gov/
- **Deschutes County:** https://data.deschutes.org/

---

## 📈 Impact

### Population Coverage Added
- **Lane County:** 382,000 residents now have parcel data access

### Potential Full Deployment Impact
If all 5 counties deployed:
- **Total Population:** 1.57M residents
- **Percentage of Oregon:** ~37% of state population (4.2M)
- **Key Cities:** Portland metro (Clackamas), Salem (Marion), Eugene (Lane), Medford (Jackson), Bend (Deschutes)

---

## 💡 Lessons Learned

### What Worked
1. **Lane County REST API** - Direct MapServer query with pagination
2. **Parallel downloads** - 4-8 workers for efficient batch processing
3. **Tippecanoe** - Excellent PMTiles conversion with auto-simplification
4. **R2 Upload** - Fast, cheap storage with global CDN

### Challenges Encountered
1. **Oregon Dept of Forestry** - Statewide MapServer is display-only, no query support
2. **Oregon Metro RLIS** - Download API doesn't support programmatic access (returns error)
3. **County Portals** - Each county uses different download mechanisms
4. **No FeatureServers** - Most counties use MapServers or manual downloads only

### Recommendations
1. **Prioritize counties with REST APIs** for automated downloads
2. **Manual downloads** required for counties with portal-only access
3. **Oregon Metro RLIS** is best source for Portland metro (Clackamas, Multnomah, Washington)
4. **Email county GIS departments** for bulk download access when portals don't work

---

## 🎯 Deployment Script Created

**File:** `/home/exx/Documents/C/hitd_maps/data-pipeline/scripts/download_oregon_counties.py`

**Features:**
- Parallel download with configurable workers
- Automatic pagination for large datasets
- Progress tracking with ETA
- Retry logic for failed requests
- GeoJSON output with metadata
- County filtering (`--county` flag)
- List available services (`--list` flag)

**Usage:**
```bash
# List available counties
python3 scripts/download_oregon_counties.py --list

# Download specific county
python3 scripts/download_oregon_counties.py --county Lane --workers 4

# Download all configured counties
python3 scripts/download_oregon_counties.py --workers 8
```

**Currently Configured:**
- Lane County (✅ Working)
- Clackamas, Marion, Jackson, Deschutes (❌ Display-only APIs)

---

## 📁 Files Created

### Data Files
- `/home/exx/Documents/C/hitd_maps/data-pipeline/data/downloads/parcels_or_lane.geojson` (382 MB)
- `/home/exx/Documents/C/hitd_maps/data-pipeline/data/pmtiles/parcels_or_lane.pmtiles` (128 MB)

### Scripts
- `/home/exx/Documents/C/hitd_maps/data-pipeline/scripts/download_oregon_counties.py`

### Documentation
- This file: `OREGON_DEPLOYMENT_SUMMARY.md`

---

## 🔗 Resources

### Oregon GIS Portals
- [Oregon GEOHub](https://geohub.oregon.gov/pages/parcel-viewer) - Statewide parcel viewer
- [Oregon Metro RLIS](https://rlisdiscovery.oregonmetro.gov/) - Portland metro regional data
- [Oregon Spatial Data Library](https://spatialdata.oregonexplorer.info/) - Statewide GIS portal

### County GIS Contacts
- **Lane County:** GIS webpage at https://www.lanecounty.org/government/county_departments/information_services/maps___g_i_s
- **Clackamas County:** gisquestions@clackamas.us
- **Marion County:** GIS@co.marion.or.us
- **Jackson County:** gis@jacksoncountyor.gov
- **Deschutes County:** https://www.deschutes.org/it/page/gis-data-services

### Technical Documentation
- [Lane County REST API](https://lcmaps.lanecounty.org/arcgis/rest/services/PlanMaps/AddressParcel/MapServer/1)
- [Oregon Dept of Forestry Taxlots](https://gis.odf.oregon.gov/ags1/rest/services/WebMercator/TaxlotsDisplay/MapServer)
- [PMTiles Spec](https://github.com/protomaps/PMTiles)
- [Tippecanoe Documentation](https://github.com/felt/tippecanoe)

---

**Generated:** 2026-01-25
**Next Action:** Manual downloads for Clackamas, Marion, Jackson, Deschutes counties from respective portals
