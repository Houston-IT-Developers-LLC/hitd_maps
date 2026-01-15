# Changelog

All notable changes to hitd_maps will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- DATA_REGISTRY.md - Complete tracking of all data sources
- Autonomous agent integration documentation

### Changed
- Nothing yet

### Fixed
- Nothing yet

---

## [1.0.0] - 2026-01-13

### Added
- **Core Map Widget**
  - `HitdMap` - Main MapLibre GL widget with PMTiles support
  - `HitdMapController` - Camera control, layer management, annotations
  - `HitdMapConfig` - Global configuration for tile URLs

- **Layer System**
  - `HitdMapLayer.parcels()` - Property boundaries
  - `HitdMapLayer.publicLands()` - PAD-US federal/state lands
  - `HitdMapLayer.blmLands()` - BLM lands specifically
  - `HitdMapLayer.nationalForest()` - National forest boundaries
  - `HitdMapLayer.wetlands()` - NWI wetlands data
  - `HitdMapLayer.wma()` - Wildlife management areas
  - `HitdMapLayer.custom()` - Custom vector tile layers

- **Services**
  - `SolunarService` - Moon-based hunting/fishing predictions
  - `WindService` - Real-time wind data from Open-Meteo API

- **Models**
  - `ParcelInfo` - Property data model with owner, address, acreage
  - `PublicLandInfo` - Public land data with designation, access level
  - `SolunarDay` - Daily solunar predictions with major/minor periods
  - `WindData` - Wind speed, direction, gusts

- **Widgets**
  - `MapWindOverlay` - Wind direction/speed indicator
  - `MapSolunarOverlay` - Solunar rating and moon phase display

- **Offline Support**
  - `OfflineManager` - Download and manage offline tile regions
  - `OfflineRegionWidget` - UI for offline region selection

- **Proprietary Features** (Premium)
  - `HuntingPressureService` - Hunting pressure analysis
  - `LandownerContactsService` - Property owner lookup
  - `LeaseMarketplaceService` - Hunting lease listings

- **Documentation**
  - DATA_PIPELINE.md - Complete data processing guide
  - INTEGRATION_GUIDE.md - How to integrate into apps
  - TROUBLESHOOTING.md - Common issues and solutions
  - DATA_REGISTRY.md - All data sources with status

### Data Sources Integrated
- Texas TNRIS StratMap (28M parcels)
- New York NYS ITS (9M parcels)
- Montana MSDI (statewide)
- Florida DEP (statewide)
- Ohio SOS (statewide)
- PAD-US 4.0 (nationwide public lands)
- Open-Meteo API (weather/wind)
- 200+ county-specific APIs

---

## Data Updates Log

### 2026-01-15
- Added DATA_REGISTRY.md with complete source tracking
- Documented Harris County coordinate issue and fix

### 2026-01-13
- **Major Scraping Run**: 72GB across 46 states
- 154 PMTiles files uploaded to R2
- Server: 512GB RAM, 48 cores, ~6 hours runtime
- States with full coverage: TX, NY, MT, FL, OH, CA, CO, CT, DE, HI, IA, MA, ND, NH, NV, SC, TN, UT, WV

### 2026-01-10
- Initial R2 bucket setup
- First TX statewide export
- PAD-US 4.0 nationwide download

### 2026-01-09
- Repository created
- Core architecture designed

---

## Version Compatibility

| hitd_maps | Flutter | Dart | MapLibre GL |
|-----------|---------|------|-------------|
| 1.0.x | >=3.0.0 | >=2.18.0 | ^0.18.0 |

---

## Migration Guide

### From Google Maps to hitd_maps

```dart
// Before (Google Maps)
GoogleMap(
  initialCameraPosition: CameraPosition(
    target: LatLng(30.0, -97.0),
    zoom: 12,
  ),
)

// After (hitd_maps)
HitdMap(
  initialPosition: LatLng(30.0, -97.0),
  initialZoom: 12.0,
  layers: [HitdMapLayer.parcels()],
)
```

### From Mapbox to hitd_maps

```dart
// Before (Mapbox)
MapboxMap(
  styleString: MapboxStyles.SATELLITE,
  initialCameraPosition: CameraPosition(
    target: LatLng(30.0, -97.0),
    zoom: 12,
  ),
)

// After (hitd_maps)
HitdMap(
  initialPosition: LatLng(30.0, -97.0),
  initialZoom: 12.0,
  layers: [HitdMapLayer.parcels()],
)
```
