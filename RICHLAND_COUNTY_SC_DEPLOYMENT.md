# Richland County, South Carolina - Parcel Data Deployment Report

**Date**: 2026-01-25  
**Target**: Richland County, SC (Columbia area)  
**Population**: ~416,000  
**Estimated Parcels**: ~168,000  
**Status**: ❌ **DEPLOYMENT BLOCKED - No Free Public Data Source Available**

---

## Executive Summary

After extensive research, **Richland County, South Carolina does NOT provide free, public access to parcel data** through standard channels (ArcGIS REST API, Open Data Portal, or downloadable files).

The county uses GeoServer/TileStache for their web mapping (richlandmaps.com) rather than Esri ArcGIS REST services, and does not maintain a public open data portal with downloadable datasets.

---

## Sources Investigated

### 1. Richland County GIS Portal
- **URL**: https://richlandmaps.com/
- **Technology**: GeoServer/TileStache (not ArcGIS REST)
- **Findings**: Web viewer only, no public API or downloads
- **Status**: ❌ No downloadable data

### 2. City of Columbia Open Data
- **URL**: https://coc-colacitygis.opendata.arcgis.com/
- **Findings**: Open data portal exists but does NOT include parcel datasets
- **Available Data**: Code violations, parks, fire stations, landmarks
- **Status**: ❌ No parcel data available

### 3. Richland County ArcGIS Hub
- **URL**: https://rcz.maps.arcgis.com/
- **Findings**: Private/authenticated ArcGIS Online organization portal
- **Status**: ❌ Requires authentication

### 4. SC Revenue and Fiscal Affairs Office
- **URL**: https://rfa.sc.gov/mapping
- **Findings**: State GIS authority, but no county parcel data available
- **Available Data**: Aerial imagery, boundaries, jurisdictional maps
- **Status**: ❌ No parcel downloads

### 5. SC State GIS Server
- **URL**: http://cowen.gis.sc.gov:6080/arcgis/rest/services
- **Findings**: Server not responding (connection refused)
- **Status**: ❌ Unavailable

### 6. Richland County Assessor
- **URL**: https://richlandcountysc.gov/Online-Services/Online-Data-Services
- **Findings**: Subscription service for deeds/probate records only (not GIS data)
- **Status**: ❌ No GIS/parcel data

---

## Commercial Options (Paid)

Several vendors offer Richland County parcel data for purchase:

| Provider | Records | Date | Price | Format |
|----------|---------|------|-------|--------|
| **ReportAll USA** | 168,559 | Q3 2024 | $250 | Shapefile, Excel, KML, CSV |
| **Regrid** | ~168,000 | Current | Unknown | Shapefile, KML (Requires Pro account) |
| **Dynamo Spatial** | 168,531 | Current | Unknown | Shapefile |
| **Mapping Solutions GIS** | Unknown | Current | Unknown | Various formats |

---

## Contact Information

### Richland County GIS
- **Website**: https://richlandmaps.com/
- **Email**: Not publicly listed
- **Phone**: 803-576-2400 (Main County)
- **Department**: Planning and Development Services

### City of Columbia GIS
- **Website**: https://gis.columbiasc.gov/
- **Email**: gis@columbiasc.gov
- **Phone**: 803-545-3300
- **Hours**: Monday-Friday, 8:30 AM - 5:00 PM

### SC Revenue and Fiscal Affairs
- **Website**: https://rfa.sc.gov/mapping
- **Email**: publicrelations@rfa.sc.gov
- **Phone**: 803-734-3793

---

## Alternative South Carolina Counties (With Open Data)

While Richland County lacks public parcel data, **other SC counties DO have ArcGIS Hub portals with free parcel downloads**:

### York County, SC ✅
- **Population**: ~282,000
- **URL**: https://opendata-yorkcosc.hub.arcgis.com/datasets/YorkCoSC::parcels
- **Format**: ArcGIS FeatureServer (downloadable)
- **Status**: **AVAILABLE FOR DEPLOYMENT**
- **Coverage Value**: Medium-high (Charlotte metro area spillover)

### Charleston County, SC ✅
- **Status**: Already have in our dataset
- **File**: `parcels_sc_charleston`

### Greenville County, SC ✅
- **Status**: Already have in our dataset
- **File**: `parcels_sc_greenville`

### Spartanburg County, SC ✅
- **Status**: Already have in our dataset
- **File**: `parcels_sc_spartanburg`

---

## Recommendations

### Short Term
1. **Deploy York County, SC** as alternative - Open data available now
2. **Contact Richland County GIS** directly via email/phone to request data access
3. **Monitor for open data portal** - City of Columbia portal exists but needs parcel data added

### Medium Term
1. **Budget for commercial purchase** if Richland County is priority ($250 from ReportAll USA)
2. **Check other SC counties** with population >100K for open data portals
3. **Revisit quarterly** - Many counties are launching open data portals

### Long Term
1. **Advocate for open data** - Contact county commissioners about public data access
2. **Partner with local GIS community** - University of SC, local developers
3. **Track SC statewide parcel initiative** - Some states are moving to statewide datasets

---

## South Carolina Coverage Status

### Current Coverage (3 counties)
- Charleston County ✅
- Greenville County ✅
- Spartanburg County ✅

### Available for Deployment
- York County (identified in this research)

### High-Priority Missing
- **Richland County** (Columbia - State capital, 416K pop) ❌ **NO FREE SOURCE**
- Horry County (Myrtle Beach, 370K pop)
- Berkeley County (Charleston metro, 244K pop)
- Anderson County (204K pop)
- Lexington County (Columbia metro, 293K pop)

### State Coverage
- **Current**: ~12% (3 of 46 counties)
- **With York County**: ~16% (4 of 46 counties)
- **With Richland (if obtained)**: ~21% (5 of 46 counties)

---

## Technical Notes

### Richland County GIS Stack
- **Mapping Platform**: GeoServer + GeoWebCache (TMS tiles)
- **Tile Service**: TileStache
- **Data Format**: Tiles only (not vector downloads)
- **Architecture**: Traditional WMS/WFS (not ArcGIS REST)

This explains why standard ArcGIS REST API queries don't work - they're using open-source GIS infrastructure.

### Data Request Strategy
If contacting county directly, request:
- **Format**: Shapefile or GeoJSON
- **Projection**: State Plane SC (EPSG:2273) or WGS84 (EPSG:4326)
- **Fields**: Parcel ID, Owner, Address, Acreage, Zoning (minimum)
- **Update Frequency**: Annual or quarterly refresh schedule

---

## Search References

This research included searches of:
- [Maps (GIS) | Richland County SC](https://www.richlandcountysc.gov/Property-Business/Mapping-and-Records/Geographic-Information-Systems)
- [City of Columbia GIS - South Carolina](https://coc-colacitygis.opendata.arcgis.com/)
- [Richland County GIS Homepage](https://rcz.maps.arcgis.com/)
- [Geography and Mapping | SC Revenue and Fiscal Affairs](https://rfa.sc.gov/mapping)
- [South Carolina Geographic Information Systems](http://gis.sc.gov/data.html)
- [York County SC Open Data Hub](https://opendata-yorkcosc.hub.arcgis.com/)
- [Richland County parcel data - Regrid](https://app.regrid.com/us/sc/richland)
- [ReportAll USA - Richland County SC](https://reportallusa.com/index.php/purchase-shapefiles/South%20Carolina/45079)

---

## Next Steps

**Immediate Action**: Deploy York County, SC parcels (free, available now)

**Follow-up**: Email gis@columbiasc.gov requesting parcel data access or open data portal timeline

