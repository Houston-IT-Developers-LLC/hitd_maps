# Additional Data Sources & Features

**Date:** 2026-01-13

This document covers NEW data sources and features beyond the existing enrichment pipeline (PAD-US, NWI, NHD, NLCD, SSURGO, FEMA, Federal Lands, State WMAs).

---

## NEW Data Sources to Add

### 1. USDA CropScape / Cropland Data Layer (CDL)

**Why it matters:** Hunters need to know where corn, soybeans, wheat fields are - deer, dove, waterfowl congregate near food sources.

| Attribute | Value |
|-----------|-------|
| **Provider** | USDA NASS |
| **URL** | https://nassgeodata.gmu.edu/CropScape |
| **Direct Download** | https://www.nass.usda.gov/Research_and_Science/Cropland/Release/ |
| **Format** | GeoTIFF (raster) |
| **Resolution** | 30m (standard), 10m (2024+) |
| **Coverage** | CONUS + Hawaii |
| **Update** | Annual |
| **Cost** | FREE (public domain) |

**Download URLs (2024):**
```
# National 30m (1.6 GB)
https://www.nass.usda.gov/Research_and_Science/Cropland/Release/datasets/2024_30m_cdls.zip

# State-specific available too
https://nassgeodata.gmu.edu/CropScape/
```

**Key Crop Codes for Hunting:**
| Code | Crop | Hunting Relevance |
|------|------|-------------------|
| 1 | Corn | **Excellent** - Deer, waterfowl, dove |
| 5 | Soybeans | **Excellent** - Deer, dove |
| 24 | Winter Wheat | Good - Dove, deer browse |
| 26 | Oats | Good - Deer, dove |
| 36 | Alfalfa | Good - Deer feeding |
| 61 | Fallow/Idle | Good - Dove, quail cover |
| 176 | Grassland/Pasture | Good - Quail, deer bedding |

**Processing Pipeline:**
```bash
# Download national CDL
wget https://www.nass.usda.gov/Research_and_Science/Cropland/Release/datasets/2024_30m_cdls.zip

# Convert raster to vector polygons (simplified for map display)
gdal_polygonize.py 2024_30m_cdls.tif -f GeoJSON crops_raw.geojson

# Filter to hunting-relevant crops only and simplify
ogr2ogr -f GeoJSON crops_hunting.geojson crops_raw.geojson \
  -where "DN IN (1, 5, 24, 26, 36, 61, 176)" \
  -simplify 0.0001

# Generate PMTiles
tippecanoe -o crops.pmtiles -Z6 -z14 \
  --drop-densest-as-needed crops_hunting.geojson
```

**Alternative: Serve as Raster Tiles (faster):**
```bash
# Create COG (Cloud Optimized GeoTIFF)
gdal_translate -of COG -co COMPRESS=LZW 2024_30m_cdls.tif crops_cog.tif

# Or create terrain-RGB style tiles with rio-mbtiles
rio mbtiles crops_cog.tif -o crops.mbtiles --zoom 6 14

# Convert to PMTiles
pmtiles convert crops.mbtiles crops.pmtiles
```

---

### 2. NIFC Wildfire Perimeters

**Why it matters:** Recent burn areas regrow quickly = food sources for deer. Hunters seek 1-5 year old burns.

| Attribute | Value |
|-----------|-------|
| **Provider** | National Interagency Fire Center |
| **URL** | https://data-nifc.opendata.arcgis.com/ |
| **Format** | Shapefile, GeoJSON, API |
| **Coverage** | National |
| **Update** | Real-time (current fires), Annual (historical) |
| **Cost** | FREE (public domain) |

**Data Endpoints:**
```
# Historical fire perimeters (all years)
https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/InterAgencyFirePerimeterHistory_All_Years_View/FeatureServer/0

# Current fires (real-time)
https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters_Current/FeatureServer/0

# 2024 fires only
https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_-_2024_Wildfire_Perimeters/FeatureServer/0
```

**Download Script:**
```python
#!/usr/bin/env python3
"""download_wildfire.py - Download NIFC wildfire perimeters"""

import requests
import json

BASE_URL = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services"
HISTORICAL = f"{BASE_URL}/InterAgencyFirePerimeterHistory_All_Years_View/FeatureServer/0"

def download_fires(start_year=2019, state_abbr=None):
    """Download fire perimeters from start_year to present"""

    where_clause = f"FireYear >= {start_year}"
    if state_abbr:
        where_clause += f" AND StateName = '{state_abbr}'"

    params = {
        'where': where_clause,
        'outFields': 'FireYear,IncidentName,GISAcres,CreateDate,StateName',
        'f': 'geojson',
        'resultOffset': 0,
        'resultRecordCount': 2000
    }

    features = []
    while True:
        resp = requests.get(f"{HISTORICAL}/query", params=params)
        data = resp.json()
        features.extend(data.get('features', []))

        if len(data.get('features', [])) < 2000:
            break
        params['resultOffset'] += 2000

    return {'type': 'FeatureCollection', 'features': features}

if __name__ == '__main__':
    # Download last 5 years of fires
    fires = download_fires(start_year=2021)
    with open('wildfire_perimeters.geojson', 'w') as f:
        json.dump(fires, f)
    print(f"Downloaded {len(fires['features'])} fire perimeters")
```

**Useful Fire Attributes:**
| Field | Description |
|-------|-------------|
| `FireYear` | Year fire occurred |
| `IncidentName` | Name of fire |
| `GISAcres` | Size in acres |
| `FireType` | Wildfire, Prescribed, etc. |
| `CreateDate` | When mapped |

---

### 3. MTBS Burn Severity

**Why it matters:** Severity affects regrowth - moderate severity burns grow back faster with browse.

| Attribute | Value |
|-----------|-------|
| **Provider** | Monitoring Trends in Burn Severity |
| **URL** | https://www.mtbs.gov/direct-download |
| **Format** | GeoTIFF (severity), Shapefile (perimeters) |
| **Coverage** | National |
| **Update** | Annual |
| **Cost** | FREE |

**Severity Classes:**
| Value | Class | Hunting Relevance |
|-------|-------|-------------------|
| 1 | Unburned | - |
| 2 | Low | Good browse in 1-2 years |
| 3 | Moderate | **Excellent** browse in 2-4 years |
| 4 | High | Slower recovery, 3-5 years |

**Download:**
```bash
# Perimeters shapefile
wget https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/MTBS_Fire/data/composite_data/burned_area_extent_shapefile/mtbs_perims_DD.zip

# Burn severity mosaics by state
# Check https://www.mtbs.gov/direct-download for specific years
```

---

### 4. USFS Motor Vehicle Use Maps (MVUM) - Roads & Trails

**Why it matters:** Know which roads are open, seasonal closures, and OHV-allowed trails.

| Attribute | Value |
|-----------|-------|
| **Provider** | USDA Forest Service |
| **URL** | https://data.fs.usda.gov/geodata/edw/datasets.php |
| **Format** | File Geodatabase, Shapefile |
| **Coverage** | All National Forests |
| **Update** | Annual |
| **Cost** | FREE |

**Datasets:**
| Dataset | Size (GDB) | Size (SHP) |
|---------|------------|------------|
| National Forest System Roads | 195 MB | 337 MB |
| Motor Vehicle Use Map: Roads | 113 MB | 214 MB |
| Motor Vehicle Use Map: Trails | 26 MB | 53 MB |

**Download URLs:**
```
# MVUM Roads
https://data.fs.usda.gov/geodata/edw/edw_resources/fc/S_USA.MVUM_Roads.gdb.zip
https://data.fs.usda.gov/geodata/edw/edw_resources/shp/S_USA.MVUM_Roads.shp.zip

# MVUM Trails
https://data.fs.usda.gov/geodata/edw/edw_resources/fc/S_USA.MVUM_Trails.gdb.zip
https://data.fs.usda.gov/geodata/edw/edw_resources/shp/S_USA.MVUM_Trails.shp.zip

# Full Road Network
https://data.fs.usda.gov/geodata/edw/edw_resources/fc/S_USA.RoadCore_FS.gdb.zip
```

**Key Fields for MVUM Roads:**
| Field | Description |
|-------|-------------|
| `SEASONAL` | Seasonal restrictions (dates) |
| `OPERATIONALMAINTENANCELEVEL` | 1-5 scale |
| `PASSENGERVEHICLE` | Allowed? Y/N |
| `HIGHCLEARANCEVEHICLE` | Allowed? Y/N |
| `FOURWHEELDRIVE` | Allowed? Y/N |
| `ATV` | Allowed? Y/N |
| `MOTORCYCLE` | Allowed? Y/N |

---

### 5. FCC Cell Coverage Maps

**Why it matters:** Safety - know where you'll have signal in remote areas.

| Attribute | Value |
|-----------|-------|
| **Provider** | Federal Communications Commission |
| **URL** | https://www.fcc.gov/BroadbandData |
| **Legacy URL** | https://www.fcc.gov/form-477-mobile-voice-and-broadband-coverage-areas |
| **Format** | Shapefile, GeoJSON |
| **Coverage** | National |
| **Update** | Biannual |
| **Cost** | FREE |

**Download:**
```
# Form 477 data (older but simpler)
https://www.fcc.gov/form-477-mobile-voice-and-broadband-coverage-areas

# Download by carrier or all combined
# Files are several GB total
```

**Processing:**
```bash
# Merge all carriers into single "any coverage" layer
ogr2ogr -f GeoJSON cell_coverage_all.geojson \
  -sql "SELECT ST_Union(geometry) as geometry, 'any' as carrier FROM coverage" \
  att_coverage.geojson verizon_coverage.geojson tmobile_coverage.geojson

# Simplify for smaller tiles
ogr2ogr -f GeoJSON cell_coverage_simple.geojson cell_coverage_all.geojson -simplify 0.001

# Create PMTiles
tippecanoe -o cell_coverage.pmtiles -Z4 -z12 \
  --drop-densest-as-needed cell_coverage_simple.geojson
```

---

### 6. USGS 3DEP Elevation (DEM)

**Why it matters:** Terrain analysis for saddles, benches, funnels, travel corridors.

| Attribute | Value |
|-----------|-------|
| **Provider** | USGS 3D Elevation Program |
| **URL** | https://apps.nationalmap.gov/downloader/ |
| **API** | https://tnmaccess.nationalmap.gov/api/v1/products |
| **Format** | GeoTIFF |
| **Resolution** | 1m, 10m, 30m |
| **Coverage** | National |
| **Cost** | FREE |

**Download via API:**
```python
import requests

# Query for 10m DEM tiles in an area
params = {
    'datasets': '10m DEM',
    'bbox': '-97.5,30.0,-97.0,30.5',  # Austin area
    'prodFormats': 'GeoTIFF'
}
resp = requests.get('https://tnmaccess.nationalmap.gov/api/v1/products', params=params)
products = resp.json()['items']

for product in products:
    print(product['downloadURL'])
```

**Terrain Analysis (Python/GDAL):**
```python
from osgeo import gdal
import numpy as np

# Load DEM
dem = gdal.Open('dem_10m.tif')
elevation = dem.ReadAsArray()

# Calculate slope
x_grad, y_grad = np.gradient(elevation, 10)  # 10m cell size
slope = np.degrees(np.arctan(np.sqrt(x_grad**2 + y_grad**2)))

# Find saddles (local minima on ridgelines)
# Find benches (low slope areas on hillsides)
# Find funnels (converging terrain)
```

**Terrain RGB Tiles for MapLibre:**
```bash
# Convert DEM to terrain-rgb tiles
rio rgbify -b -10000 -i 0.1 dem.tif terrain_rgb.tif
rio mbtiles terrain_rgb.tif -o terrain.mbtiles --zoom 6 14
pmtiles convert terrain.mbtiles terrain.pmtiles
```

---

### 7. State Game Management Units (GMUs)

**Why it matters:** Core hunting data - know which unit you're in for regulations.

| Attribute | Value |
|-----------|-------|
| **Provider** | State Wildlife Agencies |
| **Coverage** | State-by-state |
| **Update** | Annual |
| **Cost** | FREE |

**State GMU Data Sources:**

| State | URL | Format |
|-------|-----|--------|
| **Colorado** | https://geodata.colorado.gov/datasets/CPW::cpw-gmu-boundary-big-game | GeoJSON, SHP |
| **Montana** | https://gis.mt.gov/Home/data | SHP |
| **Wyoming** | https://wgfd.wyo.gov/Hunt/Where-to-Hunt/Hunt-Area-Maps | KML |
| **Texas** | https://tpwd.texas.gov/gis/data | SHP |
| **Arizona** | https://azgfd.maps.arcgis.com/ | ArcGIS FS |
| **New Mexico** | https://gis.wildlife.state.nm.us/ | SHP |
| **Idaho** | https://idfg.idaho.gov/ifwis/maps | SHP |
| **Utah** | https://gis.utah.gov/data/boundaries/wilderness/ | SHP |
| **Oregon** | https://nrimp.dfw.state.or.us/DataClearinghouse/ | SHP |
| **Washington** | https://wdfw.wa.gov/hunting/regulations | KML |
| **Wisconsin** | https://dnrmaps.wi.gov/H5/?viewer=HUNT_trout | ArcGIS |
| **Michigan** | https://gis-midnr.opendata.arcgis.com/ | GeoJSON |
| **Minnesota** | https://gisdata.mn.gov/ | SHP |
| **Pennsylvania** | https://www.pgc.pa.gov/InformationResources/Maps | SHP |

**Scraping Script Pattern:**
```python
#!/usr/bin/env python3
"""download_gmu.py - Download GMU boundaries from state wildlife agencies"""

STATE_GMU_SOURCES = {
    'CO': {
        'url': 'https://opendata.arcgis.com/api/v3/datasets/40a7e7eafc914a519ce54afe66bbe0ec_0/downloads/data?format=geojson&spatialRefId=4326',
        'format': 'geojson'
    },
    'MT': {
        'url': 'https://ftp.geoinfo.msl.mt.gov/Data/Spatial/NonMSDI/Shapefiles/MontanaFWP_HuntingDistricts.zip',
        'format': 'shapefile'
    },
    # Add more states...
}

def download_gmu(state_abbr):
    source = STATE_GMU_SOURCES.get(state_abbr)
    if not source:
        print(f"No GMU source configured for {state_abbr}")
        return

    # Download and process based on format
    # ...
```

---

### 8. Walk-In Hunting Access Programs

**Why it matters:** FREE hunting access on private land - major feature differentiator.

| Program | States |
|---------|--------|
| WIHA (Walk-In Hunting Areas) | Kansas |
| PLOTS (Private Land Open To Sportsmen) | North Dakota |
| Walk-In Areas | South Dakota, Nebraska |
| Block Management | Montana |
| Open Fields and Waters | Nebraska |
| Hunter Access | Colorado, Oklahoma |

**Data Sources:**

| State | URL |
|-------|-----|
| **Kansas WIHA** | https://ksoutdoors.com/Hunting/Where-to-Hunt-in-Kansas |
| **ND PLOTS** | https://gf.nd.gov/hunting/plots |
| **SD Walk-In** | https://apps.sd.gov/gf56fishhunt/ |
| **Montana Block** | https://myfwp.mt.gov/fwpPub/landOwnerSignup |
| **Nebraska** | https://outdoornebraska.gov/publicaccessatlas/ |
| **Colorado** | https://cpw.state.co.us/hunting-access |

**Note:** These programs change annually as landowners enroll/unenroll. Data should be refreshed before each hunting season.

---

## ALGORITHMS TO BUILD

### 1. Solunar Calculator

**No API needed - calculate client-side in Flutter.**

```dart
// lib/utils/solunar_calculator.dart

import 'package:astronomy/astronomy.dart';

class SolunarCalculator {
  /// Calculate major and minor feeding periods
  static SolunarData calculate(double lat, double lon, DateTime date) {
    final observer = Observer(lat, lon, 0);
    final time = AstroTime(date);

    // Moon transit (directly overhead) = Major period #1
    final moonTransit = SearchHourAngle(Body.Moon, observer, 0, time, 1);

    // Moon anti-transit (underfoot) = Major period #2
    final moonAntiTransit = SearchHourAngle(Body.Moon, observer, 12, time, 1);

    // Moonrise = Minor period #1
    final moonRise = SearchRiseSet(Body.Moon, observer, Direction.Rise, time, 1);

    // Moonset = Minor period #2
    final moonSet = SearchRiseSet(Body.Moon, observer, Direction.Set, time, 1);

    // Moon phase for rating
    final phase = MoonPhase(time);

    // Sun times for overlap bonus
    final sunrise = SearchRiseSet(Body.Sun, observer, Direction.Rise, time, 1);
    final sunset = SearchRiseSet(Body.Sun, observer, Direction.Set, time, 1);

    return SolunarData(
      majorPeriods: [
        SolunarPeriod(
          start: moonTransit.time.toDateTime().subtract(Duration(hours: 1)),
          end: moonTransit.time.toDateTime().add(Duration(hours: 1)),
          type: PeriodType.major,
        ),
        SolunarPeriod(
          start: moonAntiTransit.time.toDateTime().subtract(Duration(hours: 1)),
          end: moonAntiTransit.time.toDateTime().add(Duration(hours: 1)),
          type: PeriodType.major,
        ),
      ],
      minorPeriods: [
        SolunarPeriod(
          start: moonRise.time.toDateTime().subtract(Duration(minutes: 30)),
          end: moonRise.time.toDateTime().add(Duration(minutes: 30)),
          type: PeriodType.minor,
        ),
        SolunarPeriod(
          start: moonSet.time.toDateTime().subtract(Duration(minutes: 30)),
          end: moonSet.time.toDateTime().add(Duration(minutes: 30)),
          type: PeriodType.minor,
        ),
      ],
      moonPhase: phase.phase, // 0-360 degrees
      rating: _calculateRating(phase.phase, moonTransit, sunrise, sunset),
    );
  }

  static int _calculateRating(double phase, SearchResult transit,
      SearchResult sunrise, SearchResult sunset) {
    int rating = 3; // Base rating

    // New moon (0°) or full moon (180°) = best days
    if (phase < 10 || phase > 350 || (phase > 170 && phase < 190)) {
      rating += 2;
    }

    // Major period overlaps with sunrise/sunset = bonus
    final transitHour = transit.time.toDateTime().hour;
    final sunriseHour = sunrise.time.toDateTime().hour;
    final sunsetHour = sunset.time.toDateTime().hour;

    if ((transitHour - sunriseHour).abs() <= 1 ||
        (transitHour - sunsetHour).abs() <= 1) {
      rating += 1;
    }

    return rating.clamp(1, 5);
  }
}

class SolunarData {
  final List<SolunarPeriod> majorPeriods;
  final List<SolunarPeriod> minorPeriods;
  final double moonPhase;
  final int rating; // 1-5 stars

  SolunarData({
    required this.majorPeriods,
    required this.minorPeriods,
    required this.moonPhase,
    required this.rating,
  });
}

class SolunarPeriod {
  final DateTime start;
  final DateTime end;
  final PeriodType type;

  SolunarPeriod({required this.start, required this.end, required this.type});
}

enum PeriodType { major, minor }
```

**Flutter Package:** `astronomy: ^0.2.0` (dart native, no API)

---

### 2. Deer Movement Score Calculator

**Combine weather + moon + time for activity prediction.**

```dart
// lib/utils/deer_activity_calculator.dart

class DeerActivityCalculator {
  /// Calculate deer activity score (0-100) based on conditions
  static Future<DeerActivity> calculate({
    required double lat,
    required double lon,
    required DateTime dateTime,
  }) async {
    // Get weather from Open-Meteo (FREE, no API key)
    final weather = await _fetchWeather(lat, lon, dateTime);
    final solunar = SolunarCalculator.calculate(lat, lon, dateTime);

    double score = 50; // Base score

    // BAROMETRIC PRESSURE (biggest factor)
    // Rising pressure = increased activity
    if (weather.pressureTrend > 0) {
      score += (weather.pressureTrend * 10).clamp(0, 20);
    } else if (weather.pressureTrend < -2) {
      // Rapidly falling = deer bed down
      score -= 15;
    }

    // TEMPERATURE
    // Cold front approaching = feeding frenzy
    if (weather.tempChange24h < -10) {
      score += 15; // Major cold front
    } else if (weather.tempChange24h < -5) {
      score += 8;  // Moderate cooling
    }
    // Ideal temps: 40-55°F
    if (weather.temp >= 40 && weather.temp <= 55) {
      score += 10;
    } else if (weather.temp > 70) {
      score -= 10; // Too hot
    }

    // WIND
    // Light wind (5-15 mph) = ideal
    if (weather.windSpeed >= 5 && weather.windSpeed <= 15) {
      score += 5;
    } else if (weather.windSpeed > 20) {
      score -= (weather.windSpeed - 20) * 2; // Penalty for high wind
    }

    // TIME OF DAY
    final hour = dateTime.hour;
    if (hour >= 5 && hour <= 9) {
      score += 15; // Dawn
    } else if (hour >= 16 && hour <= 19) {
      score += 15; // Dusk
    } else if (hour >= 10 && hour <= 15) {
      score -= 15; // Midday
    }

    // MOON PHASE
    // New moon and full moon = increased activity
    final moonPhase = solunar.moonPhase;
    if (moonPhase < 10 || moonPhase > 350) {
      score += 10; // New moon
    } else if (moonPhase > 170 && moonPhase < 190) {
      score += 8; // Full moon
    }

    // SOLUNAR PERIODS
    // Check if current time is in major/minor period
    for (final period in solunar.majorPeriods) {
      if (dateTime.isAfter(period.start) && dateTime.isBefore(period.end)) {
        score += 15;
        break;
      }
    }
    for (final period in solunar.minorPeriods) {
      if (dateTime.isAfter(period.start) && dateTime.isBefore(period.end)) {
        score += 8;
        break;
      }
    }

    // PRECIPITATION
    if (weather.precipitation > 0 && weather.precipitation < 0.1) {
      score += 5; // Light rain/drizzle = good movement
    } else if (weather.precipitation > 0.3) {
      score -= 10; // Heavy rain = bedded down
    }

    return DeerActivity(
      score: score.clamp(0, 100).round(),
      factors: _buildFactors(weather, solunar),
      recommendation: _getRecommendation(score),
    );
  }

  static Future<WeatherData> _fetchWeather(double lat, double lon, DateTime dt) async {
    // Open-Meteo FREE API - no key needed!
    final url = Uri.parse(
      'https://api.open-meteo.com/v1/forecast'
      '?latitude=$lat&longitude=$lon'
      '&hourly=temperature_2m,windspeed_10m,winddirection_10m,'
      'precipitation,surface_pressure'
      '&past_days=1&forecast_days=1'
      '&temperature_unit=fahrenheit'
    );

    final response = await http.get(url);
    final data = json.decode(response.body);

    // Parse current conditions and calculate trends
    // ...
    return WeatherData(/* ... */);
  }

  static String _getRecommendation(double score) {
    if (score >= 80) return 'Excellent - Get in the stand!';
    if (score >= 65) return 'Good - Worth hunting';
    if (score >= 50) return 'Average - Might see some movement';
    if (score >= 35) return 'Below average - Consider waiting';
    return 'Poor - Deer likely bedded';
  }
}
```

---

### 3. Wind Overlay Integration

**Open-Meteo wind data displayed on map.**

```dart
// lib/services/wind_service.dart

class WindService {
  static const _baseUrl = 'https://api.open-meteo.com/v1/forecast';

  /// Get wind forecast for location
  static Future<List<WindData>> getWindForecast(double lat, double lon) async {
    final url = Uri.parse(
      '$_baseUrl?latitude=$lat&longitude=$lon'
      '&hourly=windspeed_10m,winddirection_10m,windgusts_10m'
      '&forecast_days=3'
      '&windspeed_unit=mph'
    );

    final response = await http.get(url);
    final data = json.decode(response.body);

    final times = data['hourly']['time'] as List;
    final speeds = data['hourly']['windspeed_10m'] as List;
    final directions = data['hourly']['winddirection_10m'] as List;
    final gusts = data['hourly']['windgusts_10m'] as List;

    return List.generate(times.length, (i) => WindData(
      time: DateTime.parse(times[i]),
      speed: speeds[i]?.toDouble() ?? 0,
      direction: directions[i]?.toDouble() ?? 0,
      gusts: gusts[i]?.toDouble() ?? 0,
    ));
  }

  /// Calculate if stand is good for current wind
  static StandWindRating rateStandForWind({
    required double standLat,
    required double standLon,
    required double approachBearing, // Direction you approach from
    required double windDirection,   // Wind coming FROM this direction
  }) {
    // Wind should blow your scent AWAY from where deer approach
    // Calculate the scent cone (typically 30° spread)

    final scentDirection = (windDirection + 180) % 360; // Where scent goes
    final angleDiff = (scentDirection - approachBearing).abs();
    final normalizedDiff = angleDiff > 180 ? 360 - angleDiff : angleDiff;

    if (normalizedDiff > 90) {
      return StandWindRating.excellent; // Scent blowing opposite of approach
    } else if (normalizedDiff > 60) {
      return StandWindRating.good;
    } else if (normalizedDiff > 30) {
      return StandWindRating.marginal;
    } else {
      return StandWindRating.poor; // Scent blowing toward approach
    }
  }
}
```

---

### 4. Terrain Analysis Tools

**Pre-process terrain on server, serve as vector tiles.**

```python
#!/usr/bin/env python3
"""terrain_analysis.py - Find hunting-relevant terrain features"""

import numpy as np
from osgeo import gdal
from scipy import ndimage
import geopandas as gpd
from shapely.geometry import Point, LineString

def find_saddles(dem_path, output_path):
    """Find saddles (low points between ridges) - travel corridors"""
    dem = gdal.Open(dem_path)
    elevation = dem.ReadAsArray().astype(float)
    transform = dem.GetGeoTransform()

    # Calculate terrain position index
    mean_filter = ndimage.uniform_filter(elevation, size=50)
    tpi = elevation - mean_filter

    # Saddles are local minima along ridgelines (TPI near 0, on ridge)
    ridgeline = tpi > np.percentile(tpi, 85)
    local_min = ndimage.minimum_filter(elevation, size=5) == elevation

    saddles = ridgeline & local_min & (np.abs(tpi) < 10)

    # Convert to points
    points = []
    rows, cols = np.where(saddles)
    for r, c in zip(rows, cols):
        x = transform[0] + c * transform[1]
        y = transform[3] + r * transform[5]
        points.append(Point(x, y))

    gdf = gpd.GeoDataFrame(geometry=points, crs='EPSG:4326')
    gdf.to_file(output_path, driver='GeoJSON')
    return len(points)


def find_benches(dem_path, output_path, min_slope=5, max_slope=15):
    """Find benches (flat areas on hillsides) - feeding/bedding areas"""
    dem = gdal.Open(dem_path)
    elevation = dem.ReadAsArray().astype(float)

    # Calculate slope
    dy, dx = np.gradient(elevation, 10)  # Assumes 10m resolution
    slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))

    # Benches: low slope areas surrounded by steeper terrain
    low_slope = (slope >= min_slope) & (slope <= max_slope)

    # Must be on a hillside (surrounding area has higher average slope)
    surrounding_slope = ndimage.uniform_filter(slope, size=20)
    on_hillside = surrounding_slope > 20

    benches = low_slope & on_hillside

    # Vectorize and simplify
    # ... convert to polygons, filter by size, export


def find_funnels(dem_path, output_path):
    """Find terrain funnels - pinch points where deer travel"""
    dem = gdal.Open(dem_path)
    elevation = dem.ReadAsArray().astype(float)

    # Calculate terrain ruggedness index
    tri = ndimage.generic_filter(elevation, lambda x: np.max(x) - np.min(x), size=5)

    # Funnels are narrow corridors of low ruggedness between high ruggedness
    low_rugged = tri < np.percentile(tri, 30)

    # Find narrow corridors using morphological operations
    from scipy.ndimage import binary_erosion, binary_dilation

    # Erode then dilate to find pinch points
    eroded = binary_erosion(low_rugged, iterations=3)
    pinch_points = eroded & ~binary_erosion(low_rugged, iterations=4)

    # ... convert to points/lines and export
```

---

## PRIORITY IMPLEMENTATION ORDER

| Priority | Feature | Data Source | Effort | Status |
|----------|---------|-------------|--------|--------|
| 1 | Parcel boundaries | Your scraper | - | ✅ In progress |
| 2 | Public lands | PAD-US | - | ✅ Script exists |
| 3 | Wetlands | NWI | - | ✅ Script exists |
| 4 | Water features | NHD | - | ✅ Script exists |
| 5 | **Wind overlay** | Open-Meteo API | 2-3 days | ⬜ TODO |
| 6 | **Solunar calculator** | Astronomy lib | 1-2 days | ⬜ TODO |
| 7 | **Crop fields** | USDA CropScape | 1 week | ⬜ TODO |
| 8 | **Wildfire history** | NIFC | 1 week | ⬜ TODO |
| 9 | **USFS roads/trails** | MVUM data | 1 week | ⬜ TODO |
| 10 | **Deer activity score** | Algorithm | 1 week | ⬜ TODO |
| 11 | **GMU boundaries** | State agencies | 2-3 weeks | ⬜ TODO |
| 12 | **Terrain analysis** | USGS 3DEP | 2-3 weeks | ⬜ TODO |
| 13 | Cell coverage | FCC | 1 week | ⬜ TODO |
| 14 | Walk-in hunting | State programs | 2 weeks | ⬜ TODO |

---

## GROUP-SPECIFIC FEATURES

These are your **killer differentiators** - no other app does these well:

### 1. Drive Coordinator Mode
- Assign pushers/standers positions on map
- Signal drive start (all members notified)
- Real-time position tracking during drive
- Automatic "drive complete" detection

### 2. Shared Stand Recommendations
- Based on today's wind, recommend which club stand to hunt
- Show ALL group stands, not just your own
- "Best stand for SE wind" algorithm

### 3. Group Harvest Log
- Log deer with auto-captured: GPS, weather, moon phase, wind
- Visible to entire hunting club
- Build historical intelligence: "This stand produces in NW winds"

### 4. Member Down Alert
- Emergency button broadcasts GPS to all group members
- Auto-calls 911 with coordinates (optional)
- "I need help" vs "Medical emergency" options

### 5. Guest Access
- Generate temp codes for visiting hunters
- Limited time access (1 day, 1 weekend, 1 season)
- Restricted to specific areas if needed

---

## API COSTS SUMMARY

| Service | Cost | Rate Limits |
|---------|------|-------------|
| Open-Meteo (weather/wind) | **FREE** | 10,000 requests/day |
| USGS National Map | **FREE** | None |
| NIFC Wildfires | **FREE** | None |
| USDA CropScape | **FREE** | None |
| State GMU data | **FREE** | Varies |
| FCC Coverage | **FREE** | None |
| Astronomy calculations | **FREE** | Client-side |

**Total API costs: $0**

All data is either:
- Downloaded once and converted to PMTiles (served from your R2)
- Calculated client-side (solunar, deer activity)
- Called from free APIs (Open-Meteo weather)
