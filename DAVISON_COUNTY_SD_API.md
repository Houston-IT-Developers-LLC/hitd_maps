# Davison County, South Dakota - Parcel Data API

**Status:** ✅ **FOUND - Working ArcGIS REST API**

---

## Quick Summary

| Attribute | Value |
|-----------|-------|
| **County** | Davison County, South Dakota |
| **Seat** | Mitchell (population ~20,000) |
| **County Population** | ~20,000 |
| **API Type** | ArcGIS REST MapServer |
| **Total Parcels** | 11,825 |
| **Provider** | District III GIS Services |
| **Coordinate System** | Web Mercator (EPSG:3857) |
| **Max Records/Query** | 2,000 |
| **Public Access** | ✅ Yes |

---

## API Endpoint

**MapServer URL:**
```
https://gis.districtiii.org/server/rest/services/DAVISON_COUNTY_WEB_LAYERS1/MapServer/4
```

**Service Root:**
```
https://gis.districtiii.org/server/rest/services/DAVISON_COUNTY_WEB_LAYERS1/MapServer
```

**Interactive Web Viewer:**
```
https://gis.districtiii.org/Davison/
```

---

## Service Details

- **Service Version:** ArcGIS 11.3
- **Max Record Count:** 2,000 records per query
- **Spatial Reference:** EPSG:3857 (Web Mercator)
- **Layer ID:** 4 (PARCEL layer)
- **Geometry Type:** Polygon

---

## Parcel Layer Schema

Key fields available in the parcel layer:

| Field Name | Type | Description |
|------------|------|-------------|
| `PARCEL_ID` | String | Unique parcel identifier |
| `OWNERNAME` | String | Property owner name |
| `SITE_ADDRESS` | String | Physical address of property |
| `MAILING_ADDRESS` | String | Owner mailing address |
| `PARCELLINK` | String | Link to detailed parcel info |
| `SHAPE_Area` | Double | Area in square meters (Web Mercator) |

---

## Download Instructions

### Method 1: Using Python Script

```bash
# Download all parcels (requires pagination for 11,825 records)
python3 data-pipeline/scripts/download_missing_states.py \
  --source davison_sd \
  --workers 4
```

### Method 2: Manual cURL (with pagination)

```bash
# Get parcel count
curl "https://gis.districtiii.org/server/rest/services/DAVISON_COUNTY_WEB_LAYERS1/MapServer/4/query?where=1%3D1&returnCountOnly=true&f=json"

# Download first batch (0-1999)
curl "https://gis.districtiii.org/server/rest/services/DAVISON_COUNTY_WEB_LAYERS1/MapServer/4/query?where=1%3D1&outFields=*&outSR=4326&f=geojson&resultOffset=0&resultRecordCount=2000" -o davison_sd_parcels_0.geojson

# Download second batch (2000-3999)
curl "https://gis.districtiii.org/server/rest/services/DAVISON_COUNTY_WEB_LAYERS1/MapServer/4/query?where=1%3D1&outFields=*&outSR=4326&f=geojson&resultOffset=2000&resultRecordCount=2000" -o davison_sd_parcels_2000.geojson

# Continue until all 11,825 parcels downloaded (6 batches total)
```

### Method 3: Direct Query URL (WGS84 output)

```
https://gis.districtiii.org/server/rest/services/DAVISON_COUNTY_WEB_LAYERS1/MapServer/4/query?where=1%3D1&outFields=*&outSR=4326&f=geojson
```

**Note:** Max 2,000 records per request. Use `resultOffset` parameter for pagination.

---

## Coverage

Davison County includes:
- **Mitchell** (county seat, pop. ~20K)
- **Mount Vernon** (pop. ~500)
- **Ethan** (pop. ~350)
- Rural agricultural parcels

Total: **11,825 parcels**

---

## Data Source Registry Entry

Add to `/home/exx/Documents/C/hitd_maps/data-pipeline/data/data_sources_registry.json`:

```json
"SD": {
  "name": "South Dakota",
  "counties": {
    "davison": {
      "name": "Davison County (Mitchell)",
      "population": 20000,
      "status": "source_found",
      "url": "https://gis.districtiii.org/Davison/",
      "api_url": "https://gis.districtiii.org/server/rest/services/DAVISON_COUNTY_WEB_LAYERS1/MapServer/4",
      "format": "ArcGIS REST MapServer",
      "coordinate_system": "Web Mercator (EPSG:3857)",
      "update_frequency": "unknown",
      "total_records": 11825,
      "our_status": "pending_download",
      "our_files": [],
      "discovered_date": "2026-01-27",
      "notes": "Mitchell area (pop 20K). Service provided by District III GIS. Max 2000 records per query requires pagination.",
      "assessor": "Davison County GIS via District III",
      "provider": "District III (districtiii.org)"
    }
  }
}
```

---

## Additional Layers Available

The DAVISON_COUNTY_WEB_LAYERS1 service includes additional useful layers:

| Layer ID | Name | Geometry | Description |
|----------|------|----------|-------------|
| 1 | MITCHELL CITY LIMITS | Polygon | City boundary |
| 2 | MT VERNON CITY LIMITS | Polygon | City boundary |
| 3 | ETHAN CITY LIMITS | Polygon | City boundary |
| 4 | **PARCEL** | Polygon | **Property parcels** |
| 5 | GOOD SALES | Polygon | Recent property sales |
| 14 | ZONING | Polygon | Zoning districts |
| 17 | ADDRESS POINT | Point | Address locations |
| 31 | ROADS | Polyline | Road centerlines |
| 37 | FLOOD DATA | Polygon | FEMA flood zones |
| 40 | TOWNSHIP | Polygon | Township boundaries |
| 41 | FIRE DISTRICTS | Polygon | Fire protection zones |

---

## Processing Pipeline

Once downloaded, process with standard pipeline:

```bash
# 1. Reproject to WGS84 (if needed - API can return WGS84 directly)
python3 data-pipeline/scripts/smart_reproject_parcels.py davison_sd_parcels.geojson

# 2. Convert to PMTiles
python3 data-pipeline/scripts/batch_convert_pmtiles.py davison_sd_parcels_wgs84.geojson --output parcels_sd_davison.pmtiles

# 3. Upload to R2
python3 data-pipeline/scripts/upload_to_r2_boto3.py parcels_sd_davison.pmtiles
```

---

## Contact Information

**GIS Provider:** District III
**Website:** https://www.districtiii.org/gis.html
**Service Coverage:** 25+ South Dakota counties
**Technology:** ArcGIS Server 11.3

**Davison County:**
- **Assessor Portal:** https://gis.districtiii.org/Davison/
- **Geocoder Service:** DAVISON_LOCATOR (GeocodeServer)

---

## Discovery Notes

- **Discovered:** 2026-01-27
- **Method:** Web search for District III services → Found updated HTTPS server (old ims.districtiii.org redirects to gis.districtiii.org)
- **Service name changed:** From "DAVISON" (old server) to "DAVISON_COUNTY_WEB_LAYERS1" (current server)
- **Server migration:** District III upgraded from ArcGIS 10.41 to 11.3, moved from HTTP to HTTPS
- **Data quality:** Service includes parcel IDs, owner names, addresses, and spatial data
- **Similar counties:** District III serves 25+ South Dakota counties with similar service structure

---

## Related Services

District III also provides GIS services for neighboring South Dakota counties:

- **Beadle County** (Huron) - Already have: `parcels_sd_beadle`
- **Hanson County** - Service available
- **Hutchinson County** - Service available
- **Bon Homme County** - Service available
- **Charles Mix County** - Service available
- **Aurora County** - Service available

All following similar MapServer structure at https://gis.districtiii.org/server/rest/services/
