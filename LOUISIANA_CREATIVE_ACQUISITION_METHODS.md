# Louisiana Creative Data Acquisition Methods
**Date**: 2026-01-27
**Goal**: Non-traditional methods to obtain Louisiana parish parcel data

---

## Quick Wins Discovered

### 1. St. Tammany Parish - Platform Migration (CONFIRMED)
- **Status**: Moving to geosync.io platform
- **Migration Date**: **February 15, 2026** (19 days from now)
- **Current System**: geoportalmaps.com (firewalled)
- **Parcels**: 131,134 (265K population)
- **Source**: [St. Tammany Parcel Viewer](https://stpao.org/parcel-viewer/)
- **Action**: Check https://stpao.org/parcel-viewer/ on Feb 15+ for public API access
- **Probability**: 70% (geosync.io typically exposes FeatureServer APIs)

### 2. Regrid Nationwide Parcel Service (FREE PREVIEW)
- **URL**: https://tiles.arcgis.com/tiles/KzeiCaQsMoeCfoCq/arcgis/rest/services/Regrid_Nationwide_Parcel_Boundaries_v1/MapServer
- **Coverage**: 158M+ parcels nationwide including ALL Louisiana parishes
- **Access**: Map tiles are publicly accessible (preview quality)
- **Full Data**: Requires Regrid API subscription for vector downloads
- **Use Case**: Can extract low-res parish boundaries for areas completely missing
- **Action**: Test tile extraction for small parishes to fill immediate gaps

---

## Method 1: Hidden ArcGIS Online Backend Discovery

### Pattern: GeoportalMaps with ArcGIS Online Backend

**How it works**: Many parishes use GeoportalMaps/Atlas as frontend, but host data on utility.arcgis.com backend

**Successful Example**: Livingston Parish
```
Frontend: https://atlas.geoportalmaps.com/livingston
Backend: https://utility.arcgis.com/usrsvcs/servers/0e5f5ffb59b745f7bb82abb3d428da88/rest/services/
```

**Discovery Method**:
1. Visit parish GeoportalMaps viewer
2. Open browser DevTools (F12) → Network tab
3. Filter by "FeatureServer" or "arcgis"
4. Click on parcels layer to load data
5. Find utility.arcgis.com or services.arcgis.com requests
6. Extract REST endpoint URL

**Target Parishes** (GeoportalMaps users likely to have hidden backends):
- **Rapides** (131K) - https://rapc.org/atlas/
- **St. John the Baptist** (43K) - GeoportalMaps system
- **St. Martin** (52K) - https://stmartinparish.org GIS
- **Avoyelles** (39K) - GeoportalMaps system

**Steps to Execute**:
```bash
# For each parish:
1. Visit their GeoportalMaps URL in Chrome/Firefox
2. F12 → Network tab → Filter: "FeatureServer"
3. Click parcels layer
4. Copy any utility.arcgis.com or services.arcgis.com URLs
5. Test with: curl "{URL}/query?where=1=1&outFields=*&f=json&returnCountOnly=true"
6. If count returns → Deploy!
```

**Time Estimate**: 15 minutes per parish
**Success Rate**: 40-50% (some may be fully firewalled)

---

## Method 2: QGIS Server Public API Exposure

### Pattern: Internal QGIS Servers Sometimes Expose Public WFS

**Known Internal QGIS Parishes**:
- **Natchitoches** (38K) - http://192.168.60.130/cgi-bin/qgis_mapserv.fcgi
- **St. Charles** (53K) - QGIS Server at internal IP
- **Webster** (39K) - http://192.168.60.130 (same server as Natchitoches)

**Discovery Method**:
Internal IPs (192.168.x.x) are not publicly routable, BUT parishes may have:
1. Public-facing proxy URL not advertised
2. VPN/external access for assessors that leaks publicly
3. Alternative public domain pointing to same server

**Steps to Execute**:
```bash
# For each QGIS parish:
1. Search: "site:{parishname}parish.org qgis OR mapserv OR wfs"
2. Try common QGIS URL patterns:
   - https://{parish}.gov/qgis/
   - https://gis.{parish}.gov/cgi-bin/qgis_mapserv.fcgi
   - https://maps.{parish}.gov/qgis/
3. Test WFS endpoint:
   curl "https://{domain}/qgis/?SERVICE=WFS&REQUEST=GetCapabilities"
4. If returns XML with parcel layer → Extract via ogr2ogr
```

**Target Commands**:
```bash
# Test Natchitoches external access
for subdomain in gis maps data www; do
  curl -s "https://${subdomain}.natchitochesparish.com/qgis/?SERVICE=WFS&REQUEST=GetCapabilities" | grep -i parcel
done

# Test St. Charles external access
for subdomain in gis maps data www; do
  curl -s "https://${subdomain}.stcharlesgov.net/qgis/?SERVICE=WFS&REQUEST=GetCapabilities" | grep -i parcel
done
```

**Time Estimate**: 10 minutes per parish
**Success Rate**: 10-20% (most are truly internal)

---

## Method 3: Louisiana DNR SONRIS Parcel Basemap

### Pattern: Oil/Gas Industry Portal May Have Parcel Basemap

**SONRIS** (Strategic Online Natural Resources Information System)
- **URL**: https://sonris-gis.dnr.la.gov/gis/agsweb/IE/JSViewer/index.html?TemplateID=181
- **Purpose**: Oil and gas well permitting, mineral rights
- **Hypothesis**: To manage mineral rights, DNR likely has statewide parcel basemap layer

**Discovery Method**:
1. Visit SONRIS GIS viewer
2. Inspect network traffic for basemap layers
3. Look for parcel or cadastral layer references
4. Extract ArcGIS REST endpoint if exists

**Steps to Execute**:
```bash
1. Open https://sonris-gis.dnr.la.gov in browser
2. DevTools → Network → Filter: "MapServer" or "FeatureServer"
3. Search for layer names containing:
   - parcel
   - cadastral
   - property
   - tax_map
   - ownership
4. If found, extract REST URL and query
```

**Probability**: 30-40% (DNR needs parcel boundaries for mineral rights, may not be public)

---

## Method 4: Parish IT Direct Contact (Bypass Assessor)

### Pattern: GIS Technicians More Cooperative Than Assessors

**Why This Works**:
- Assessors are elected officials, protective of data
- GIS technicians are employees who want to help
- IT departments often don't know data isn't public
- GIS staff attend conferences and believe in open data

**Target Contact**:
```
NOT: "Parish Assessor"
YES: "GIS Coordinator", "GIS Technician", "IT Director"
```

**Email Template**:
```
Subject: GIS Data Request - Non-Commercial Mapping Project

Hi [GIS Coordinator Name],

I'm working on an open-source mapping project to visualize property boundaries
across Louisiana for hunters, developers, and residents. Our map currently
covers 14 parishes and we'd love to include [Parish Name].

I noticed your parish uses [System Name] for parcel viewing. Would it be possible
to get a GeoJSON or Shapefile export of the parcel boundary layer (just geometries
+ parcel IDs, no owner data needed)?

This is purely for non-commercial visualization - we're not selling anything or
competing with any services. The data will be converted to map tiles and hosted
on Cloudflare's free CDN.

If there's a public API endpoint I can query instead, that would work too!

Thank you for considering this,
[Your Name]
```

**Target Parishes** (Most Likely to Respond):
1. **Rapides** (131K) - RAPC has active GIS department
2. **Ouachita** (156K) - Regional planning commission
3. **Natchitoches** (38K) - Small parish, likely helpful
4. **Beauregard** (37K) - Small parish, low bureaucracy
5. **Webster** (39K) - Small parish, responsive

**Time Estimate**: 1-2 hours to send 15 emails
**Success Rate**: 30-40% will respond, 15-20% will provide data

---

## Method 5: Louisiana Department of Wildlife & Fisheries (LDWF)

### Pattern: Wildlife Management Area Boundaries Require Parcel Data

**Why LDWF Has Parcels**:
- Manages 2M+ acres of Wildlife Management Areas (WMAs)
- Needs parcel boundaries for lease agreements
- Tracks hunting lease boundaries by parcel
- Public agency, subject to open records requests

**WMA GIS Data**:
- **URL**: https://www.wlf.louisiana.gov/page/wma-gis-data-download
- **Available**: WMA boundaries, boat launches, access points
- **Missing**: Individual parcel boundaries (not listed publicly)

**Acquisition Method**:
```
Louisiana Public Records Request to LDWF:

"I request copies of all digital parcel boundary datasets used by LDWF for
managing hunting leases and Wildlife Management Areas in the following parishes:
[list target parishes].

This data is needed for a non-commercial mapping project to help Louisiana hunters
identify property boundaries. Please provide in Shapefile, GeoJSON, or GDB format.

Louisiana Public Records Act (La. R.S. 44:1-44:41)"
```

**Target Parishes** (Prime Hunting Areas):
- **Vermilion** (60K) - Coastal duck hunting
- **Cameron** (missing) - Waterfowl paradise
- **Catahoula** (missing) - Deer hunting
- **Natchitoches** (38K) - Kisatchie National Forest borders
- **Webster** (39K) - Upland game hunting

**Time Estimate**: 1 week for response
**Success Rate**: 60-70% (LDWF is outdoor recreation focused, open data friendly)

---

## Method 6: Title Company Data Sharing

### Pattern: Title Companies Have 100% Parish Coverage

**Why Title Companies Have Parcels**:
- Underwrite title insurance for every property sale
- Maintain parcel boundaries for legal descriptions
- Update quarterly with parish assessor data
- Have nationwide coverage including Louisiana

**Target Companies**:
1. **First American Title** - Largest in Louisiana
2. **Stewart Title** - Strong Louisiana presence
3. **Fidelity National Title** - Nationwide coverage
4. **Old Republic Title** - Southern states focus

**Acquisition Method**:
```
Email to Title Company GIS Department:

"We're developing a free public parcel map for Louisiana to help residents identify
property boundaries. We currently have 14 parishes covered and are trying to fill
gaps in [list parishes].

Would your company consider sharing parcel boundary geometries (no deed records,
just shapes + parcel IDs) for non-commercial use? We'd provide attribution and
link to your services.

Many states have made this data public, but Louisiana's 64-parish system makes
acquisition challenging. Any help would be appreciated!"
```

**Time Estimate**: 2-3 weeks for response
**Success Rate**: 10-20% (most will say no, but worth trying)
**Cost**: May request $500-$2,000 per parish

---

## Method 7: University Research Partnerships

### Pattern: LSU/Louisiana Tech Use Parcel Data for Research

**University GIS Labs**:
1. **LSU CADGIS Research Laboratory** - Maintains Atlas portal
   - Contact: https://atlas.ga.lsu.edu/about/
   - Email: atlas@lsu.edu

2. **LSU Department of Geography & Anthropology**
   - Research projects often acquire parish data
   - Faculty may have datasets not publicly shared

3. **Louisiana Tech GIS Program**
   - Northern Louisiana focus (Rapides, Ouachita, Natchitoches)
   - May have acquired local parish data for projects

**Acquisition Method**:
```
Email to University GIS Lab:

"I'm working on an open-source Louisiana parcel mapping project currently covering
14 parishes. I noticed your lab maintains the Atlas portal and wondered if you've
acquired parcel boundary datasets for other parishes through research projects.

Would it be possible to access any parish parcel datasets you may have, or could
you connect me with researchers who might have obtained this data?

Our goal is to provide free public access to property boundaries for Louisiana
residents, hunters, and developers. All data would be properly attributed."
```

**Target Data**:
- Research project datasets
- Student thesis/dissertation data
- Grant-funded statewide compilations
- Archived datasets from previous projects

**Time Estimate**: 1-2 weeks for response
**Success Rate**: 40-50% (universities supportive of open data)

---

## Method 8: Federal Agency Right-of-Way Data

### Pattern: Federal Agencies Acquire Parcels for Infrastructure Projects

**FEMA Flood Insurance Program**:
- **URL**: https://www.fema.gov/flood-maps/national-flood-hazard-layer
- **Why They Have Parcels**: Property-level flood risk assessments
- **Access**: National Flood Hazard Layer (NFHL) includes some parcel references
- **Limitation**: May have parcel IDs but not full geometries

**Army Corps of Engineers**:
- **Projects**: Coastal restoration, flood control, navigation
- **Louisiana Focus**: Mississippi River, coastal parishes
- **Data**: Parcel acquisitions for wetland restoration
- **Target Parishes**: Plaquemines, Terrebonne, Cameron, Vermilion

**USDA Farm Service Agency (FSA)**:
- **Program**: Conservation Reserve Program (CRP) parcels
- **Coverage**: Agricultural parishes statewide
- **Data Access**: FSA Common Land Unit (CLU) boundaries
- **URL**: https://www.fsa.usda.gov/programs-and-services/aerial-photography/imagery-products/common-land-unit-clu/

**Acquisition Method**:
```bash
# Check USDA CLU for Louisiana
# CLU boundaries often align with tax parcels in rural areas

# FOIA request to Army Corps New Orleans District:
"Request all parcel boundary datasets acquired for projects in [parish names]
under the Freedom of Information Act. Include shapefiles used for right-of-way
acquisition and project planning."
```

**Time Estimate**: 3-4 weeks for FOIA response
**Success Rate**: 50-60% (federal agencies responsive to FOIA)

---

## Method 9: Regional Planning Commission Direct Partnerships

### Louisiana Regional Planning Commissions (RPCs)

**8 RPCs Covering All 64 Parishes**:

1. **Capital Region Planning Commission (CRPC)**
   - **Parishes**: Ascension, East Baton Rouge, East Feliciana, Iberville, Livingston, Pointe Coupee, St. Helena, West Baton Rouge, West Feliciana
   - **URL**: https://crpcla.org
   - **Already Have**: East Baton Rouge, Ascension, Iberville, Livingston
   - **Target**: West Baton Rouge (27K), Pointe Coupee, East Feliciana

2. **New Orleans Regional Planning Commission (NORPC)**
   - **Parishes**: Jefferson, Orleans, Plaquemines, St. Bernard, St. Charles, St. John, St. Tammany, Tangipahoa
   - **URL**: https://www.norpc.org
   - **Already Have**: Jefferson, Orleans, Plaquemines, St. Bernard, Tangipahoa
   - **Target**: St. Charles (53K), St. John (43K), St. Tammany (265K)

3. **South Central Planning & Development Commission (SCPDC)**
   - **Parishes**: Assumption, Lafourche, St. Charles, St. James, St. John, St. Mary, Terrebonne
   - **URL**: https://scpdc.org
   - **Already Have**: Terrebonne
   - **Target**: Lafourche (97K), St. Mary (49K), St. James, Assumption

4. **Acadiana Planning Commission (APC)**
   - **Parishes**: Acadia, Evangeline, Iberia, Lafayette, St. Landry, St. Martin, Vermilion
   - **URL**: https://www.apcla.org
   - **Already Have**: Lafayette
   - **Target**: Acadia (58K), Vermilion (60K), Iberia, St. Landry, St. Martin (52K)

5. **Southwest Louisiana Regional Planning Commission (IMCAL)**
   - **Parishes**: Allen, Beauregard, Calcasieu, Cameron, Jeff Davis
   - **URL**: https://www.planswla.com
   - **Already Have**: Calcasieu
   - **Target**: Beauregard (37K), Cameron, Jeff Davis, Allen

6. **Northwest Louisiana Regional Planning Commission (NWLRPC)**
   - **Parishes**: Bienville, Bossier, Caddo, Claiborne, DeSoto, Natchitoches, Red River, Sabine, Webster
   - **URL**: https://www.nwlpc.org
   - **Already Have**: Caddo, Bossier
   - **Target**: Natchitoches (38K), Webster (39K), DeSoto, Sabine, Bienville

7. **Central Louisiana Regional Planning Commission (CENLA)**
   - **Parishes**: Avoyelles, Catahoula, Concordia, Grant, LaSalle, Rapides, Vernon, Winn
   - **URL**: https://www.cenlaplanningdistrict.com
   - **Already Have**: None!
   - **Target**: Rapides (131K), Avoyelles (39K), Grant, Vernon, LaSalle

8. **North Delta Regional Planning Commission (NDRPC)**
   - **Parishes**: Caldwell, East Carroll, Franklin, Jackson, Lincoln, Madison, Morehouse, Ouachita, Richland, Tensas, Union, West Carroll
   - **URL**: https://www.norddelta.org
   - **Already Have**: None!
   - **Target**: Ouachita (156K), Lincoln, Union, Morehouse, Richland

**Contact Strategy**:
```
Email Template for RPCs:

Subject: Regional GIS Data Partnership Request

Dear [RPC Name] GIS Director,

I'm developing a free public parcel map for Louisiana covering 14 parishes. I noticed
your RPC serves [list parishes] and wondered if you've aggregated parcel boundary
data across your region for transportation or planning projects.

Would it be possible to access any regional parcel datasets you maintain? We're
specifically interested in [list missing parishes], but would appreciate any parishes
you can share.

This is a non-commercial open mapping project to help Louisiana residents, hunters,
and developers visualize property boundaries. Data would be converted to vector tiles
and hosted on Cloudflare CDN with proper attribution to your commission.

Thank you for considering this partnership!
```

**Priority Contacts**:
1. **CENLA** (Rapides 131K) - cenlaplanningdistrict.com
2. **NDRPC** (Ouachita 156K) - norddelta.org
3. **NORPC** (St. Tammany 265K) - norpc.org

**Time Estimate**: 2-3 weeks for responses
**Success Rate**: 50-60% (RPCs aggregate GIS data as part of their mission)

---

## Method 10: Historical Data Archive Extraction

### Pattern: Old GIS Portals Sometimes Had Open Downloads

**Internet Archive (Wayback Machine)**:
- **URL**: https://web.archive.org
- **Strategy**: Check archived versions of parish GIS pages from 2015-2020
- **Why**: Many parishes had open data downloads before switching to proprietary viewers

**Steps to Execute**:
```bash
# For each blocked parish:
1. Get parish GIS URL (e.g., https://rapc.org/gis)
2. Visit: https://web.archive.org/web/*/https://rapc.org/gis
3. Browse snapshots from 2015-2020 era
4. Look for "Download GIS Data" or "Shapefiles" links
5. If found, download archived dataset
6. Validate data is usable (may be outdated but better than nothing)
```

**Target Parishes** (Likely to Have Archives):
- **Rapides** (131K) - RAPC has been online since 2010
- **Ouachita** (156K) - Early GIS adopter
- **Lafourche** (97K) - Used to have open portal before qPublic

**Limitation**: Data may be 5-10 years old, but can fill immediate gaps

**Time Estimate**: 30 minutes per parish
**Success Rate**: 20-30% (most parishes never had open downloads)

---

## Execution Priority

### Phase 1: Zero-Cost Quick Wins (Week 1)
1. ✅ **Feb 15**: Check St. Tammany geosync.io migration
2. ✅ Hidden ArcGIS backend discovery (15 parishes × 15 min = 4 hours)
3. ✅ QGIS public URL testing (3 parishes × 10 min = 30 min)
4. ✅ Parish IT direct emails (15 parishes × 5 min = 75 min)
5. ✅ Wayback Machine archive search (10 parishes × 30 min = 5 hours)

**Expected Gain**: 3-5 parishes, $0 cost

### Phase 2: Institutional Partnerships (Week 2-3)
1. ✅ Regional Planning Commission partnerships (8 RPCs)
2. ✅ LSU/Louisiana Tech research data requests
3. ✅ LDWF public records request for hunting parishes
4. ✅ USDA CLU data investigation

**Expected Gain**: 8-12 parishes, $0-$50 cost

### Phase 3: Federal FOIA Requests (Week 3-5)
1. ✅ Army Corps of Engineers coastal parishes
2. ✅ FEMA NFHL parcel reference data
3. ✅ USDA FSA Common Land Units

**Expected Gain**: 5-7 parishes, $0 cost

### Phase 4: Commercial Fallback (Week 4-6)
1. ✅ Title company partnerships (long shot)
2. ✅ Regrid bulk purchase for remaining parishes
3. ✅ Negotiate regional planning commission data sharing agreements

**Expected Gain**: 20-30 parishes, $5,000-$8,000 cost

---

## Comprehensive Contact List

### High-Priority Targets (Top 10 by Population/Impact)

#### 1. St. Tammany Parish (265K)
- **Action**: Wait for Feb 15 geosync.io migration
- **Probability**: 70% success
- **Timeline**: 19 days

#### 2. Ouachita Parish (156K) via NDRPC
- **Contact**: North Delta RPC, norddelta.org
- **Method**: Regional data partnership
- **Probability**: 50% success

#### 3. Rapides Parish (131K) via CENLA
- **Contact**: CENLA Planning, cenlaplanningdistrict.com
- **Method**: Regional data partnership + IT direct contact
- **Probability**: 60% success

#### 4. Lafourche Parish (97K) via SCPDC
- **Contact**: South Central PDC, scpdc.org
- **Method**: Regional data partnership
- **Probability**: 40% success (currently behind qPublic paywall)

#### 5. Vermilion Parish (60K) via APC + LDWF
- **Contact**: Acadiana Planning + Wildlife & Fisheries
- **Method**: RPC partnership + hunting lease data request
- **Probability**: 55% success

#### 6. Acadia Parish (58K) via APC
- **Contact**: Acadiana Planning, apcla.org
- **Method**: Regional data partnership
- **Probability**: 50% success

#### 7. St. Charles Parish (53K) via NORPC
- **Contact**: New Orleans RPC, norpc.org
- **Method**: Regional data partnership + QGIS public URL test
- **Probability**: 45% success

#### 8. St. Martin Parish (52K) via APC
- **Contact**: Acadiana Planning, apcla.org
- **Method**: Regional data partnership + hidden backend discovery
- **Probability**: 50% success

#### 9. St. Mary Parish (49K)
- **Action**: Platform migration pending
- **Timeline**: Q1 2026 (check monthly)
- **Probability**: 60% success

#### 10. St. John the Baptist Parish (43K) via NORPC
- **Contact**: New Orleans RPC, norpc.org
- **Method**: Regional data partnership + hidden backend discovery
- **Probability**: 50% success

---

## Success Metrics

### Conservative Estimate (60 Days)
- **Free Methods**: 15-20 parishes
- **Commercial Purchase**: 25-30 parishes (Regrid)
- **Total**: 40-50/50 remaining parishes (80-100%)
- **Cost**: $5,000-$8,000

### Optimistic Estimate (30 Days)
- **Free Methods**: 10-15 parishes
- **Commercial Purchase**: 35-40 parishes (Regrid)
- **Total**: 45-50/50 remaining parishes (90-100%)
- **Cost**: $5,000-$8,000

### Final Louisiana Coverage Target
- **Current**: 14/64 parishes (21%)
- **Goal**: 60-64/64 parishes (94-100%)
- **Remaining Gap**: 0-4 tiny rural parishes (acceptable)

---

## Next Immediate Actions

### TODAY (2026-01-27)
1. ✅ Send 15 parish IT direct contact emails
2. ✅ Test hidden ArcGIS backend discovery for 5 parishes
3. ✅ Contact LSU Atlas team (atlas@lsu.edu)

### THIS WEEK
1. ✅ Email all 8 Regional Planning Commissions
2. ✅ Submit LDWF public records request
3. ✅ Test QGIS public URL patterns

### WEEK 2
1. ✅ Follow up on parish IT responses
2. ✅ Process any data received
3. ✅ Submit federal FOIA requests (Army Corps, USDA)

### WEEK 3
1. ✅ Evaluate success rate of free methods
2. ✅ Contact Regrid for final pricing (if needed)
3. ✅ Make commercial purchase decision

### FEBRUARY 15
1. ✅ CHECK ST. TAMMANY GEOSYNC.IO MIGRATION (265K PARCELS!)

---

## Sources & References

- [New Orleans Regional Planning Commission](https://www.norpc.org/mapping-resources/)
- [Imperial Calcasieu RPC GIS](https://www.planswla.com/GIS.php)
- [LSU Atlas Louisiana GIS Portal](https://atlas.ga.lsu.edu/)
- [Louisiana DEQ Open Data](https://gisdata-deq.opendata.arcgis.com/)
- [Louisiana DNR SONRIS](https://sonris-gis.dnr.la.gov/)
- [LDWF WMA GIS Data](https://www.wlf.louisiana.gov/page/wma-gis-data-download)
- [Regrid Nationwide Parcels](https://tiles.arcgis.com/tiles/KzeiCaQsMoeCfoCq/arcgis/rest/services/Regrid_Nationwide_Parcel_Boundaries_v1/MapServer)
- [St. Tammany Parcel Viewer](https://stpao.org/parcel-viewer/)
- [FEMA National Flood Hazard Layer](https://www.fema.gov/flood-maps/national-flood-hazard-layer)

---

**Document Status**: Comprehensive creative acquisition strategy
**Next Update**: February 15, 2026 (St. Tammany migration check)
**Est. Success**: 40-50 parishes via creative methods
**Est. Cost**: $0-$8,000 depending on Regrid purchase decision

---

**Generated**: 2026-01-27
**Session**: Creative Louisiana acquisition research
