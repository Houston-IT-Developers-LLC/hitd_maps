# Priority County Acquisition Plan
**For 14 Partial States - Target: 50-70% Coverage**

**Date**: 2026-01-27
**Strategy**: Focus on top 20-25 counties by population in each state

---

## Summary

**Goal**: Add ~150-200 county files to jump from current partial coverage to 50-70% in all 14 states

**Estimated Impact**:
- Illinois: 10% → 65%
- Michigan: 12% → 60%
- Georgia: 5% → 50%
- Missouri: 10% → 60%
- Louisiana: 17% → 70%
- Others: 5-10% → 40-60%

**Method**: Use existing `agent/source_finder.py` and `download_missing_states.py` tools

---

## Priority 1: Large States (High Population)

### Illinois (102 counties) - Current: 10% → Target: 65%
**Add these 15 counties** (~5.5M more people, 60% of state):

| County | Population | City | Priority |
|--------|-----------|------|----------|
| DuPage | 930K | Naperville | ✅ Already have |
| Kane | 540K | Aurora | ✅ Already have |
| Will | 690K | Joliet | ✅ Already have |
| Lake | 700K | Waukegan | ✅ Already have |
| Cook | 5.2M | Chicago | ✅ Already have |
| Madison | 260K | Alton | 🔴 NEED |
| St. Clair | 260K | Belleville | ✅ Already have |
| Champaign | 210K | Champaign | 🔴 NEED |
| Sangamon | 200K | Springfield | 🔴 NEED |
| Rock Island | 145K | Rock Island | 🔴 NEED |
| Peoria | 180K | Peoria | ✅ Already have |
| Winnebago | 285K | Rockford | ✅ Already have |
| Tazewell | 132K | Pekin | 🔴 NEED |
| McLean | 170K | Bloomington | 🔴 NEED |
| Kankakee | 110K | Kankakee | 🔴 NEED |

**Still need**: 8 counties

---

### Michigan (83 counties) - Current: 12% → Target: 60%
**Add these 15 counties** (~4M more people):

| County | Population | City | Priority |
|--------|-----------|------|----------|
| Wayne | 1.8M | Detroit | ✅ Already have |
| Oakland | 1.3M | Pontiac | ✅ Already have |
| Macomb | 880K | Mt. Clemens | ✅ Already have |
| Kent | 660K | Grand Rapids | ✅ Already have |
| Genesee | 405K | Flint | 🔴 NEED |
| Washtenaw | 370K | Ann Arbor | 🔴 NEED |
| Ottawa | 300K | Holland | ✅ Already have |
| Ingham | 290K | Lansing | 🔴 NEED |
| Kalamazoo | 265K | Kalamazoo | 🔴 NEED |
| Saginaw | 190K | Saginaw | 🔴 NEED |
| St. Clair | 160K | Port Huron | 🔴 NEED |
| Muskegon | 175K | Muskegon | ✅ Already have |
| Jackson | 160K | Jackson | 🔴 NEED |
| Berrien | 155K | Benton Harbor | 🔴 NEED |
| Calhoun | 135K | Battle Creek | 🔴 NEED |

**Still need**: 9 counties

---

### Georgia (159 counties!) - Current: 5% → Target: 50%
**Add these 20 counties** (~5M more people):

| County | Population | City | Priority |
|--------|-----------|------|----------|
| Fulton | 1.1M | Atlanta | ✅ Already have |
| Gwinnett | 950K | Lawrenceville | ✅ Already have |
| Cobb | 760K | Marietta | ✅ Already have |
| DeKalb | 760K | Decatur | ✅ Already have |
| Chatham | 295K | Savannah | ✅ Already have |
| Clayton | 295K | Jonesboro | 🔴 NEED |
| Cherokee | 265K | Canton | 🔴 NEED |
| Forsyth | 250K | Cumming | ✅ Already have |
| Henry | 245K | McDonough | 🔴 NEED |
| Richmond | 200K | Augusta | ✅ Already have |
| Columbia | 155K | Evans | 🔴 NEED |
| Hall | 210K | Gainesville | 🔴 NEED |
| Muscogee | 195K | Columbus | 🔴 NEED |
| Bibb | 153K | Macon | 🔴 NEED |
| Houston | 160K | Warner Robins | 🔴 NEED |
| Bartow | 108K | Cartersville | 🔴 NEED |
| Paulding | 168K | Dallas | 🔴 NEED |
| Clarke | 128K | Athens | 🔴 NEED |
| Coweta | 148K | Newnan | 🔴 NEED |
| Fayette | 118K | Fayetteville | 🔴 NEED |

**Still need**: 14 counties

---

### Missouri (115 counties) - Current: 10% → Target: 60%
**Add these 15 counties** (~2.5M more people):

| County | Population | City | Priority |
|--------|-----------|------|----------|
| St. Louis City | 300K | St. Louis | ✅ Already have |
| St. Louis County | 1.0M | Clayton | ✅ Already have |
| Jackson | 715K | Kansas City | ✅ Already have |
| St. Charles | 410K | St. Charles | ✅ Already have |
| Greene | 295K | Springfield | ✅ Already have |
| Clay | 250K | Liberty | ✅ Already have |
| Jefferson | 228K | Hillsboro | 🔴 NEED |
| Boone | 180K | Columbia | ✅ Already have |
| Franklin | 105K | Union | 🔴 NEED |
| Cass | 107K | Harrisonville | 🔴 NEED |
| Christian | 89K | Ozark | ✅ Already have |
| Jasper | 120K | Joplin | 🔴 NEED |
| Platte | 105K | Platte City | 🔴 NEED |
| Cape Girardeau | 80K | Cape Girardeau | 🔴 NEED |
| Buchanan | 88K | St. Joseph | 🔴 NEED |

**Still need**: 7 counties

---

## Priority 2: Medium States

### Louisiana (64 parishes) - Current: 17% → Target: 70%
**Add these 12 parishes** (~1.5M more people):

| Parish | Population | City | Priority |
|--------|-----------|------|----------|
| East Baton Rouge | 455K | Baton Rouge | ✅ Already have |
| Jefferson | 435K | Metairie | ✅ Already have |
| Orleans | 385K | New Orleans | ✅ Already have |
| St. Tammany | 264K | Mandeville | 🔴 NEED |
| Lafayette | 245K | Lafayette | ✅ Already have |
| Caddo | 238K | Shreveport | ✅ Already have |
| Calcasieu | 208K | Lake Charles | ✅ Already have |
| Bossier | 130K | Bossier City | 🔴 NEED |
| Rapides | 130K | Alexandria | 🔴 NEED |
| Terrebonne | 110K | Houma | ✅ Already have |
| Lafourche | 97K | Thibodaux | 🔴 NEED |
| Ouachita | 150K | Monroe | 🔴 NEED |
| Ascension | 125K | Gonzales | 🔴 NEED |
| St. Bernard | 48K | Chalmette | 🔴 NEED |

**Still need**: 7 parishes

---

### Alabama (67 counties) - Current: 5% → Target: 40%
**Add these 15 counties** (~2M more people):

| County | Population | City | Priority |
|--------|-----------|------|----------|
| Jefferson | 660K | Birmingham | ✅ Already have |
| Mobile | 415K | Mobile | ✅ Already have |
| Madison | 395K | Huntsville | ✅ Already have |
| Montgomery | 227K | Montgomery | ✅ Already have |
| Shelby | 225K | Alabaster | 🔴 NEED |
| Baldwin | 230K | Bay Minette | 🔴 NEED |
| Tuscaloosa | 210K | Tuscaloosa | 🔴 NEED |
| Lee | 175K | Auburn | 🔴 NEED |
| Morgan | 120K | Decatur | 🔴 NEED |
| Calhoun | 114K | Anniston | 🔴 NEED |
| Houston | 107K | Dothan | 🔴 NEED |
| Etowah | 102K | Gadsden | 🔴 NEED |
| Limestone | 103K | Athens | 🔴 NEED |
| St. Clair | 91K | Pell City | 🔴 NEED |
| Lauderdale | 93K | Florence | 🔴 NEED |

**Still need**: 11 counties

---

### Kentucky (120 counties) - Current: 5% → Target: 40%
**Add these 15 counties** (~1.5M more people):

| County | Population | City | Priority |
|--------|-----------|------|----------|
| Jefferson | 770K | Louisville | ✅ Already have |
| Fayette | 322K | Lexington | ✅ Already have |
| Kenton | 170K | Covington | ✅ Already have |
| Boone | 135K | Burlington | ✅ Already have |
| Warren | 135K | Bowling Green | ✅ Already have |
| Hardin | 110K | Elizabethtown | 🔴 NEED |
| Daviess | 103K | Owensboro | ✅ Already have |
| Campbell | 93K | Newport | 🔴 NEED |
| Madison | 93K | Richmond | 🔴 NEED |
| McCracken | 67K | Paducah | 🔴 NEED |
| Christian | 72K | Hopkinsville | 🔴 NEED |
| Oldham | 68K | La Grange | 🔴 NEED |
| Laurel | 63K | London | 🔴 NEED |
| Pike | 58K | Pikeville | 🔴 NEED |
| Bullitt | 83K | Shepherdsville | 🔴 NEED |

**Still need**: 9 counties

---

## Priority 3: Smaller States

### South Carolina (46 counties) - Current: 10% → Target: 50%
**Add 10 counties** (~1.5M more people)

| County | Population | City | Status |
|--------|-----------|------|--------|
| Greenville | 525K | Greenville | ✅ Already have |
| Charleston | 408K | Charleston | ✅ Already have |
| York | 280K | Rock Hill | ✅ Already have |
| Spartanburg | 330K | Spartanburg | ✅ Already have |
| Lexington | 295K | Lexington | ✅ Already have |
| Horry | 351K | Myrtle Beach | 🔴 NEED |
| Richland | 415K | Columbia | 🔴 NEED |
| Anderson | 203K | Anderson | 🔴 NEED |
| Beaufort | 192K | Beaufort | 🔴 NEED |
| Berkeley | 230K | Moncks Corner | 🔴 NEED |

**Still need**: 5 counties

---

### Mississippi (82 counties) - Current: 7% → Target: 40%
**Add 10 counties**

| County | Population | City | Status |
|--------|-----------|------|--------|
| Hinds | 220K | Jackson | ✅ Already have |
| Harrison | 208K | Gulfport | ✅ Already have |
| DeSoto | 185K | Southaven | ✅ Already have |
| Rankin | 157K | Brandon | ✅ Already have |
| Madison | 110K | Madison | 🔴 NEED |
| Lee | 85K | Tupelo | 🔴 NEED |
| Jackson | 143K | Pascagoula | 🔴 NEED |
| Lauderdale | 73K | Meridian | 🔴 NEED |
| Forrest | 78K | Hattiesburg | 🔴 NEED |
| Lowndes | 58K | Columbus | 🔴 NEED |

**Still need**: 6 counties

---

### Oklahoma (77 counties) - Current: 5% → Target: 40%
**Add 10 counties**

| County | Population | City | Status |
|--------|-----------|------|--------|
| Oklahoma | 795K | Oklahoma City | ✅ Already have |
| Tulsa | 670K | Tulsa | ✅ Already have |
| Cleveland | 295K | Norman | ✅ Already have |
| Comanche | 121K | Lawton | ✅ Already have |
| Canadian | 154K | El Reno | 🔴 NEED |
| Rogers | 95K | Claremore | 🔴 NEED |
| Wagoner | 80K | Wagoner | 🔴 NEED |
| Creek | 72K | Sapulpa | 🔴 NEED |
| Pottawatomie | 73K | Shawnee | 🔴 NEED |
| Washington | 52K | Bartlesville | 🔴 NEED |

**Still need**: 6 counties

---

### Oregon (36 counties) - Current: 5% → Target: 40%
**Add 8 counties**

| County | Population | City | Status |
|--------|-----------|------|--------|
| Multnomah | 820K | Portland | ✅ Already have |
| Washington | 615K | Hillsboro | 🔴 NEED |
| Clackamas | 425K | Oregon City | 🔴 NEED |
| Lane | 382K | Eugene | ✅ Already have |
| Marion | 350K | Salem | 🔴 NEED |
| Deschutes | 200K | Bend | 🔴 NEED |
| Jackson | 224K | Medford | 🔴 NEED |
| Linn | 130K | Albany | 🔴 NEED |
| Yamhill | 108K | McMinnville | 🔴 NEED |
| Douglas | 110K | Roseburg | 🔴 NEED |

**Still need**: 8 counties

---

### South Dakota (66 counties) - Current: 10% → Target: 40%
**Add 8 counties**

| County | Population | City | Status |
|--------|-----------|------|--------|
| Minnehaha | 200K | Sioux Falls | ✅ Already have |
| Pennington | 115K | Rapid City | ✅ Already have |
| Lincoln | 65K | Canton | ✅ Already have |
| Brown | 38K | Aberdeen | 🔴 NEED |
| Codington | 28K | Watertown | ✅ Already have |
| Brookings | 35K | Brookings | 🔴 NEED |
| Yankton | 23K | Yankton | 🔴 NEED |
| Lawrence | 27K | Deadwood | 🔴 NEED |
| Davison | 20K | Mitchell | 🔴 NEED |
| Hughes | 18K | Pierre | 🔴 NEED |

**Still need**: 6 counties

---

### Nebraska (93 counties) - Current: 2% → Target: 30%
**Add 10 counties**

| County | Population | City | Status |
|--------|-----------|------|--------|
| Douglas | 585K | Omaha | ✅ Already have |
| Lancaster | 322K | Lincoln | ✅ Already have |
| Sarpy | 190K | Bellevue | 🔴 NEED |
| Hall | 63K | Grand Island | 🔴 NEED |
| Buffalo | 51K | Kearney | 🔴 NEED |
| Dodge | 37K | Fremont | 🔴 NEED |
| Madison | 36K | Norfolk | 🔴 NEED |
| Scotts Bluff | 36K | Scottsbluff | 🔴 NEED |
| Lincoln | 35K | North Platte | 🔴 NEED |
| Dakota | 21K | Dakota City | 🔴 NEED |

**Still need**: 8 counties

---

### Kansas (105 counties) - Current: 1% → Target: 30%
**Add 10 counties**

| County | Population | City | Status |
|--------|-----------|------|--------|
| Johnson | 610K | Olathe | 🔴 NEED |
| Sedgwick | 523K | Wichita | ✅ Already have |
| Shawnee | 177K | Topeka | 🔴 NEED |
| Wyandotte | 165K | Kansas City | 🔴 NEED |
| Douglas | 123K | Lawrence | ✅ Already have |
| Leavenworth | 82K | Leavenworth | 🔴 NEED |
| Riley | 74K | Manhattan | 🔴 NEED |
| Reno | 63K | Hutchinson | 🔴 NEED |
| Butler | 68K | El Dorado | 🔴 NEED |
| Saline | 54K | Salina | 🔴 NEED |

**Still need**: 8 counties

---

## Implementation Summary

### Total Counties to Add: ~150

**By Priority**:
- Priority 1 (Large states): 65 counties (IL, MI, GA, MO, LA)
- Priority 2 (Medium states): 41 counties (AL, KY, SC, MS)
- Priority 3 (Smaller states): 44 counties (OK, OR, SD, NE, KS)

### Tools to Use

1. **agent/source_finder.py** - Find ArcGIS REST endpoints
2. **scripts/download_missing_states.py** - Download from endpoints
3. **scripts/smart_reproject_parcels.py** - Convert to WGS84
4. **scripts/batch_convert_pmtiles.py** - Convert to PMTiles
5. **scripts/upload_to_r2_boto3.py** - Upload to R2

### Estimated Timeline

- **Week 1-2**: Priority 1 states (65 counties) → IL, MI, GA, MO to 50-65%
- **Week 3**: Priority 2 states (41 counties) → AL, KY, SC, MS to 40-50%
- **Week 4**: Priority 3 states (44 counties) → OK, OR, SD, NE, KS to 30-40%

### Expected Results

After completing this plan:
- **37 states at 100%** (unchanged)
- **14 states at 40-70%** (up from 1-17%)
- **Overall coverage**: ~85-90% of US population
- **Total files**: ~385 PMTiles (up from 234)

---

## Next Steps

1. ✅ Generate this priority list
2. Run `agent/source_finder.py` for each needed county
3. Batch download using parallel workers
4. Process and upload
5. Update valid_parcels.json and coverage_status.json

**Ready to start!**
