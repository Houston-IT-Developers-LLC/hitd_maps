# Parcel Data Documentation

## Overview

This document describes the parcel data collection process, sources, and documentation for the GSpot Outdoors application.

## Data Collection Summary

- **Collection Date**: January 13-15, 2026
- **Collection Method**: ArcGIS REST API scraping
- **Output Format**: PMTiles (converted from GeoJSON via tippecanoe)
- **Storage Location**: Cloudflare R2 (gspot-tiles bucket)
- **Total States Covered**: 47+ states

## Data Sources

All parcel data was collected from publicly available ArcGIS REST API endpoints operated by:
- State GIS departments
- County assessor/property offices
- Regional planning organizations (COGs, MPOs)
- Open data portals

## Update Schedule

| Data Type | Update Frequency | Next Update Estimate |
|-----------|------------------|----------------------|
| Parcel boundaries | Quarterly | April 2026 |
| Property ownership | Quarterly | April 2026 |
| Statewide datasets | Annually | January 2027 |

## R2 Storage Structure

```
s3://gspot-tiles/
├── parcels/
│   ├── parcels_{state}_{county}.pmtiles
│   ├── parcels_{state}_statewide.pmtiles
│   └── ...
└── wgs84/
    └── (reprojected files if needed)
```

## File Naming Convention

- `parcels_{state}_{county}.pmtiles` - County-level data
- `parcels_{state}_statewide.pmtiles` - Statewide consolidated data
- `_v2` suffix - Alternative or newer data source for same area

## Data Fields

Common fields included in parcel data:

| Field | Description |
|-------|-------------|
| `objectid` | Unique identifier |
| `parno` / `pin` | Parcel number |
| `ownname` | Owner name |
| `siteadd` | Property address |
| `landval` | Land value |
| `improvval` | Improvement value |
| `parval` | Total parcel value |
| `gisacres` | Parcel acreage |
| `parusecode` | Land use code |

Note: Field names vary by jurisdiction. Not all fields are available in all datasets.

## Processing Pipeline

1. **Scraping**: Python script (`export_county_parcels.py`) queries ArcGIS REST APIs
2. **GeoJSON Export**: Features exported as GeoJSON with all attributes
3. **Reprojection**: If needed, `ogr2ogr` converts to WGS84 (EPSG:4326)
4. **PMTiles Conversion**: `tippecanoe` creates vector tiles at zoom levels 0-14
5. **R2 Upload**: boto3 uploads to Cloudflare R2 bucket
6. **Cleanup**: Local GeoJSON files deleted after successful upload

## Known Data Issues

### Coordinate Systems
- Some sources export in State Plane coordinates (NAD83)
- Pipeline automatically reprojects to WGS84 when needed

### Incomplete Extracts
- Some jurisdictions have pagination limits (max 1000-2000 features per request)
- Script handles pagination automatically via `resultOffset`

### Data Quality
- Property values may be outdated (assessor data has lag)
- Some parcels may lack geometry (centroid-only)
- Rural areas may have incomplete coverage

## API Sources by State

See `COUNTY_CONFIGS` in `export_county_parcels.py` for complete list of API endpoints.

Major data sources include:
- State-level: MA, CT, NJ, NC, FL, TX, CA, NY, OH, PA
- County-level: Harris County TX, Los Angeles CA, Cook IL, etc.
- Regional: INCOG (Oklahoma), various MPOs

## Usage in Application

The PMTiles files are served via Cloudflare R2 and rendered using:
- MapLibre GL JS (web)
- MapLibre Flutter SDK (mobile)

Layer configuration in `map_style.json`:
```json
{
  "id": "parcels",
  "type": "fill",
  "source": "parcels",
  "source-layer": "parcels",
  "paint": {
    "fill-color": "#e0e0e0",
    "fill-opacity": 0.5,
    "fill-outline-color": "#666"
  }
}
```

## Manifest File

The `PARCEL_DATA_MANIFEST.json` file tracks all uploaded datasets with:
- Extraction timestamp
- Feature count
- File sizes (GeoJSON and PMTiles)
- R2 keys
- Update schedule

## Contact

For questions about the data collection process or to report issues:
- Repository: https://github.com/gspot-outdoors/my-gspot-outdoors-flutter
- Data Pipeline: `data-pipeline/` directory

## License

Parcel data sourced from government agencies is generally in the public domain.
Individual jurisdictions may have specific terms of use.
Always verify licensing before commercial use.

---
Generated: 2026-01-15
Pipeline Version: 1.0
