# AI Prompt Templates for Parcel Data Tasks

Copy-paste these prompts to your local AI models (Deepseek R1, Llama 3.3, etc.)

---

## Prompt 1: Find Missing State Data

```
I'm building a US property parcel database for an outdoor recreation app. I need to find GIS parcel data for these missing states:

- Maine (ME)
- Rhode Island (RI)
- Vermont (VT)

Search for:
1. State GIS portal parcel datasets
2. ArcGIS REST service endpoints (FeatureServer or MapServer)
3. Open data portal downloads (GeoJSON, Shapefile)
4. Individual county GIS if no statewide exists

For each source found, provide:
- Full API URL for the query endpoint
- A curl command to test it
- What fields are available (owner name, address, acreage, etc.)
- Estimated record count
- Coordinate system (WGS84 or Web Mercator)

Focus on publicly accessible data that doesn't require authentication.
```

---

## Prompt 2: Validate Existing Endpoints

```
I have a list of ArcGIS parcel data endpoints. Please validate each one still works and document the schema.

Test these endpoints:
1. https://feature.tnris.org/arcgis/rest/services/Parcels/stratmap25_land_parcels_48/MapServer/0/query
2. https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcels_Public/FeatureServer/1/query
3. https://gisservicemt.gov/arcgis/rest/services/MSDI_Framework/Parcels/MapServer/0/query

For each endpoint, run:
```bash
curl -s "{URL}?where=1=1&returnCountOnly=true&f=json"
curl -s "{URL}?where=1=1&outFields=*&f=json&resultRecordCount=1"
```

Report:
- Is it accessible? (200 OK)
- Total record count
- Available fields (list them)
- Any changes from expected schema
- Server response time
```

---

## Prompt 3: Find Rich Data Sources

```
I have basic parcel boundary data but many states lack owner information and property addresses.

Find ArcGIS REST endpoints that include these fields:
- Owner name (OWNERNME1, owner_name, OWNER, etc.)
- Site address (SITEADRESS, site_addr, ADDRESS, etc.)
- Mailing address
- Acreage/lot size
- Assessed value
- Land use/zoning

Priority states needing enrichment:
- Virginia (currently only has parcel ID, locality, FIPS)
- Florida (need better owner data)
- Texas (TNRIS lacks owner names)

Search patterns:
- "{state} assessor parcel data GIS"
- "{state} tax parcel owner arcgis"
- "{county} property records FeatureServer"
```

---

## Prompt 4: Research County-Level Sources

```
I need to find ArcGIS parcel endpoints for individual counties. Many states don't have statewide data, so we collect county-by-county.

Find parcel data endpoints for the largest counties in these states:
- California (Los Angeles, San Diego, Orange, Riverside, San Bernardino)
- Texas (Harris, Dallas, Bexar, Tarrant, Travis)
- Florida (Miami-Dade, Broward, Palm Beach, Hillsborough, Orange)
- Illinois (Cook, DuPage, Lake, Will)

For each county found, provide in this format:
```python
"{STATE}_{COUNTY}": {
    "name": "{County Name}, {State}",
    "service_url": "{Full ArcGIS URL}/query",
    "out_fields": "*",
    "batch_size": 2000,
},
```

Test each endpoint to confirm it works and supports pagination.
```

---

## Prompt 5: Find Public Land Data

```
Beyond private parcels, I need public land boundaries for outdoor recreation:

Find GIS data sources for:
1. Wildlife Management Areas (WMAs) - state fish & wildlife agencies
2. State Parks and Recreation Areas
3. National Forest boundaries (USFS)
4. BLM land (Bureau of Land Management)
5. State trust lands
6. Conservation easements

Priority: States with good hunting opportunities
- Texas, Montana, Colorado, Wisconsin, Michigan, Pennsylvania, Georgia

For each dataset, provide:
- Agency/source name
- Download URL or API endpoint
- Data format (GeoJSON, Shapefile, GeoPackage)
- What attributes are included
```

---

## Prompt 6: Data Quality Audit

```
Review the field schemas from these parcel datasets and rate their data quality:

Virginia sample:
{
  "PARCELID": "45162",
  "LOCALITY": "Richmond City",
  "FIPS": "51760",
  "Shape__Area": 1234567,
  "Shape__Length": 456
}

Wisconsin sample:
{
  "PIN": "012-0123-0000",
  "OWNER_NAME": "SMITH JOHN",
  "SITE_ADDR": "123 MAIN ST",
  "ACRES": 2.5,
  "LAND_VALUE": 50000,
  "IMPR_VALUE": 150000
}

For each state, rate:
- Completeness (1-10): How many useful fields?
- Owner data (Y/N): Has owner name?
- Address data (Y/N): Has site address?
- Value data (Y/N): Has assessed value?
- Recommendations: What additional sources could enrich this?
```

---

## Prompt 7: API Discovery for Specific State

```
Find ALL available ArcGIS parcel data endpoints for [STATE NAME].

Search strategies:
1. State GIS clearinghouse/portal
2. Major county GIS websites
3. ArcGIS Hub searches
4. Open data portals

For [STATE NAME], find:
- Statewide dataset (if exists)
- Top 10 largest county datasets
- Any regional/multi-county datasets

Document each endpoint with:
- URL
- Owner/operator
- Approximate record count
- Key fields available
- Last update date (if visible)
- Any access restrictions

Output as a Python dict ready to add to export_county_parcels.py
```

---

## Prompt 8: Coordinate System Detection

```
I need to identify which parcel APIs return Web Mercator (EPSG:3857) vs WGS84 (EPSG:4326).

Test these sample coordinates from each API:
- If coordinates look like: -95.3698, 29.7604 → WGS84 ✓
- If coordinates look like: -10615325, 3473843 → Web Mercator (needs reprojection)

Test endpoint: {URL}?where=1=1&outFields=*&f=geojson&resultRecordCount=1

Check the first coordinate pair in the response geometry.

Report which states need reprojection before tile generation.
```

---

## Prompt 9: Broken Endpoint Alternatives

```
These parcel data endpoints have stopped working. Find alternatives:

Broken:
- [LIST ANY BROKEN URLs]

For each broken endpoint:
1. Search for the same agency's current GIS portal
2. Look for migrated/renamed services
3. Find alternative county/regional sources
4. Check if data moved to ArcGIS Hub

Common migration patterns:
- MapServer → FeatureServer
- arcgis/rest/services → services.arcgis.com (cloud migration)
- Old domain → new domain

Provide replacement URLs in the same format.
```

---

## Prompt 10: Batch Source Discovery

```
Generate a research plan for comprehensive parcel data coverage.

Current status:
- 48 states have some data
- Missing: ME, RI, VT
- Need enrichment: VA, FL (owner data)

Create a prioritized task list:
1. Find statewide sources for missing states
2. Identify 5 states with poorest data quality to improve
3. List top 20 counties by population that we should add
4. Find public land datasets to complement parcel data

For each task, include:
- Search queries to use
- Expected time to research
- Likelihood of finding good data (H/M/L)
```

---

## Usage Tips for Local Models

1. **Deepseek R1 671B**: Best for complex reasoning about data schemas and API patterns
2. **Llama 3.3 70B**: Good for search query generation and documentation
3. **Both**: Can validate curl commands and parse JSON responses

### Sample workflow:
```bash
# 1. Ask AI to generate search queries
# 2. Manually search and find candidate URLs
# 3. Ask AI to validate endpoints with curl
# 4. Ask AI to format as Python config
# 5. Add to export_county_parcels.py
# 6. Run export script
```

---

## Output Collection Template

When AI finds data, collect in this format:

```yaml
state: XX
source_type: statewide|county
county_name: (if county)
api_url: https://...
fields:
  - PARCEL_ID
  - OWNER_NAME
  - SITE_ADDR
record_count: ~X,XXX,XXX
coord_system: WGS84|WebMercator
tested: true|false
date_found: YYYY-MM-DD
notes: any issues or special handling
```
