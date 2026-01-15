# GSpot Parcel Data - AI Assistant Guide

> **For**: Deepseek R1 671B, Llama 3.3 70B, or other local LLMs
> **Purpose**: Help improve, expand, and maintain US property parcel data
> **Last Updated**: January 2026

---

## Project Overview

GSpot Outdoors is building a comprehensive US property parcel database for outdoor recreation (hunting, fishing, camping). The app shows property boundaries so users know where public vs private land is.

### Current Status
- **48 states** have scraped parcel data (~85GB GeoJSON)
- **7 states** converted to PMTiles and live on CDN
- **3 states missing**: Maine (ME), Rhode Island (RI), Vermont (VT)
- **~150M parcels** total estimated

### Tech Stack
- **Data Format**: GeoJSON → MBTiles → PMTiles
- **Hosting**: Cloudflare R2 (CDN)
- **Visualization**: MapLibre GL (Flutter + Web)
- **Tools**: tippecanoe, pyproj, Python scripts

---

## Data Sources

### Primary Source Types

1. **ArcGIS REST Services** (Most Common)
   - URL Pattern: `https://{domain}/arcgis/rest/services/{path}/MapServer/0/query` or `FeatureServer/0/query`
   - Supports pagination via `resultOffset` and `resultRecordCount`
   - Returns GeoJSON with `f=geojson` parameter

2. **State GIS Portals**
   - Often have statewide parcel datasets
   - Examples: TNRIS (Texas), VGIN (Virginia), NYS ITS (New York)

3. **County GIS Websites**
   - For states without statewide data
   - Each county may have different schema/fields

### Known Working Statewide APIs

| State | API URL | Notes |
|-------|---------|-------|
| TX | `https://feature.tnris.org/arcgis/rest/services/Parcels/stratmap25_land_parcels_48/MapServer/0/query` | 28M parcels, rich data |
| NY | `https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcels_Public/FeatureServer/1/query` | 9M parcels |
| MT | `https://gisservicemt.gov/arcgis/rest/services/MSDI_Framework/Parcels/MapServer/0/query` | Full state |
| VA | `https://vgin.vdem.virginia.gov/arcgis/rest/services/VA_Base_Layers/VA_Parcels/MapServer/0/query` | Limited fields |
| WI | Via county APIs combined | Good owner data |

---

## Tasks for AI Assistants

### 1. Find Missing State Data (HIGH PRIORITY)

**States needing data sources:**
- Maine (ME)
- Rhode Island (RI)
- Vermont (VT)

**Search strategies:**
```
"{state name} GIS parcel data"
"{state name} property parcels ArcGIS"
"{state name} tax parcels open data"
site:arcgis.com "{state name}" parcels
```

**What to look for:**
- ArcGIS REST endpoints (FeatureServer or MapServer)
- GeoJSON download links
- Shapefile downloads (can convert)
- Open data portals

### 2. Find Better Data Sources (MEDIUM PRIORITY)

Some states have limited fields. Find APIs with richer data:

**Priority fields to find:**
- `owner_name` / `OWNERNME1` - Property owner
- `site_address` / `SITEADRESS` - Physical address
- `acreage` / `ACRES` - Lot size
- `land_use` / `LANDUSE` - Zoning/use type
- `assessed_value` - Property value

**States needing enrichment:**
- Virginia (VA) - Only has 7 fields, no owner/address
- Many states only have parcel boundaries

### 3. Find Updated Data Sources

Data gets stale. Look for:
- 2025/2026 parcel updates
- Better maintained endpoints
- More reliable servers

### 4. Add County-Level Sources

For states without statewide APIs, find individual county sources:

**Template to fill out:**
```python
"{STATE}_{COUNTY}": {
    "name": "{County Name}, {State}",
    "service_url": "{ArcGIS REST URL}/query",
    "out_fields": "*",
    "batch_size": 2000,  # Adjust based on server limits
}
```

---

## How to Validate a Data Source

### Step 1: Check if endpoint exists
```bash
curl -s "{URL}?f=json" | head -100
```

### Step 2: Check field schema
```bash
curl -s "{URL}?where=1=1&outFields=*&f=json&resultRecordCount=1"
```

### Step 3: Check total record count
```bash
curl -s "{URL}?where=1=1&returnCountOnly=true&f=json"
```

### Step 4: Test pagination
```bash
curl -s "{URL}?where=1=1&outFields=*&f=geojson&resultOffset=0&resultRecordCount=10"
```

### What makes a good source:
- ✅ Returns GeoJSON (or can convert)
- ✅ Supports pagination (resultOffset)
- ✅ Has owner/address fields
- ✅ Server is stable/fast
- ✅ Data is recent (2024-2026)
- ❌ Avoid: Rate-limited, requires auth, slow servers

---

## Output Format

When you find a new data source, provide:

```markdown
## {State} - {County/Statewide}

**API URL**: `https://...`

**Test command**:
```bash
curl -s "{URL}?where=1=1&outFields=*&f=geojson&resultRecordCount=1"
```

**Fields available**:
- PARCEL_ID: Parcel identifier
- OWNER_NAME: Property owner
- SITE_ADDR: Property address
- ACRES: Lot size
- (list all relevant fields)

**Total records**: ~X,XXX,XXX

**Coordinate system**: EPSG:4326 (WGS84) / EPSG:3857 (Web Mercator)

**Notes**: Any issues, rate limits, quirks
```

---

## Existing Configuration

The main export script is at:
```
data-pipeline/scripts/export_county_parcels.py
```

It contains ~200 county/state configurations. Add new sources to the `COUNTY_CONFIGS` dict.

### Current state coverage by config count:
```
TX: 14 configs (statewide + counties)
PA: 14 configs
GA: 14 configs
TN: 12 configs
CA: 10 configs
CO: 9 configs
VA: 8 configs
MI: 8 configs
FL: 8 configs
...
```

---

## Coordinate Systems

**Important**: Some APIs return Web Mercator (EPSG:3857) instead of WGS84 (EPSG:4326).

**How to detect:**
- WGS84: Coordinates like `-95.3, 29.7` (reasonable lng/lat)
- Web Mercator: Coordinates like `-10610000, 3480000` (large numbers)

**If Web Mercator**, add to reproject list. Our pipeline handles this automatically.

---

## Priority Research Tasks

### Immediate (Missing States)
1. **Maine** - Search for MaineGIS, Maine DOT, county GIS
2. **Rhode Island** - Search RIGIS, Providence GIS
3. **Vermont** - Search VCGI, Vermont GIS

### High Value (Major Counties)
1. **Los Angeles County, CA** - Largest US county
2. **Cook County, IL** (Chicago area)
3. **Maricopa County, AZ** (Phoenix area)
4. **San Diego County, CA**

### Data Quality Improvements
1. Find Texas owner name data (current TNRIS lacks it)
2. Find Virginia property addresses
3. Find Florida owner information

---

## Search Query Templates

```
# For statewide data
"{state} statewide parcel GIS"
"{state} open data portal parcels"
"{state} GIS clearinghouse property"

# For county data
"{county} county {state} GIS parcels"
"{county} county assessor parcel map"
"{county} county property data ArcGIS"

# For ArcGIS specifically
site:arcgis.com "{state}" parcels FeatureServer
site:arcgis.com "{county}" parcels
"{state} arcgis rest services parcels"
```

---

## Example New Source Entry

Here's what a complete new source looks like:

```python
# Add to COUNTY_CONFIGS in export_county_parcels.py

"RI_STATEWIDE": {
    "name": "Rhode Island Statewide Parcels",
    "service_url": "https://rigis-edc.opendata.arcgis.com/datasets/parcels/FeatureServer/0/query",
    "out_fields": "*",
    "batch_size": 2000,
    "notes": "Found via RIGIS Open Data Portal"
},
```

---

## Data Enrichment Ideas

Beyond basic parcel data, useful additions:

1. **Wildlife Management Areas (WMAs)**
   - State fish & wildlife agencies
   - Public hunting land boundaries

2. **National Forest Boundaries**
   - USFS data

3. **BLM Land**
   - Bureau of Land Management parcels

4. **State Parks**
   - State recreation areas

5. **Conservation Easements**
   - Land trust data

---

## Contact/Resources

- **ArcGIS Hub**: https://hub.arcgis.com/ - Search for parcel datasets
- **Data.gov**: https://data.gov/ - Federal open data
- **State GIS Portals**: Search "{state} GIS" for official portals

---

## Success Metrics

A good data improvement session should:
- [ ] Find at least 1 new statewide source
- [ ] Validate 5+ existing endpoints still work
- [ ] Document field schemas for new sources
- [ ] Identify 3+ counties with rich owner data
- [ ] Report any broken/moved endpoints

---

*This guide helps local AI models contribute to the GSpot parcel database without external API costs. All data processing happens locally.*
