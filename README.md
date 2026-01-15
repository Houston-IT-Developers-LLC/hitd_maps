# HITD Maps

A comprehensive Flutter mapping toolkit for outdoor/hunting applications by Houston IT Developers LLC.

## Features

- **MapLibre GL Integration** - Vector tile map rendering with PMTiles support
- **Parcel Data** - Property boundary visualization with owner information
- **Public Lands** - Federal and state land boundaries (PAD-US)
- **Solunar Calculator** - Hunting/fishing activity predictions based on moon position
- **Wind Overlay** - Real-time wind data with scent cone visualization
- **Layer Management** - Easy toggle between multiple data layers

## Installation

Add to your `pubspec.yaml`:

```yaml
dependencies:
  hitd_maps:
    git:
      url: https://github.com/RORHITD/hitd_maps.git
      ref: main
```

## Quick Start

### 1. Initialize the configuration

```dart
import 'package:hitd_maps/hitd_maps.dart';

void main() {
  // Configure your tile server
  HitdMapConfig.initialize(
    pmtilesBaseUrl: 'https://your-cdn.com/tiles',
    basemapStyleUrl: 'assets/map/basemap_style.json',
  );

  runApp(MyApp());
}
```

Or use a preset:

```dart
HitdMapPresets.useGSpotOutdoors();
```

### 2. Add the map widget

```dart
HitdMap(
  initialPosition: LatLng(30.2672, -97.7431),
  initialZoom: 12.0,
  layers: [
    HitdMapLayer.parcels(),
    HitdMapLayer.publicLands(),
  ],
  onMapCreated: (controller) {
    // Store controller for later use
    _mapController = controller;
  },
  onFeatureTap: (latLng, properties) {
    if (properties != null) {
      final parcel = ParcelInfo.fromProperties(properties);
      _showParcelDetails(parcel);
    }
  },
)
```

### 3. Use the services

```dart
// Solunar calculator
final solunar = SolunarService();
final today = solunar.getSolunarDay(30.2672, -97.7431, DateTime.now());
print('Day Rating: ${today.dayRating}');
print('Moon Phase: ${today.moonPhase.phase.displayName}');

// Wind service
final wind = WindService();
await wind.getCurrentWind(30.2672, -97.7431);
print('Wind: ${wind.currentWind.value?.speed} mph from ${wind.currentWind.value?.cardinalDirection}');
```

## Available Layers

| Layer | Description | State-Specific |
|-------|-------------|----------------|
| `HitdMapLayer.parcels()` | Property boundaries | Yes |
| `HitdMapLayer.publicLands()` | All public lands (PAD-US) | No |
| `HitdMapLayer.blmLands()` | BLM lands | No |
| `HitdMapLayer.nationalForest()` | National Forest | No |
| `HitdMapLayer.wetlands()` | NWI wetlands | Yes |
| `HitdMapLayer.wma()` | Wildlife Management Areas | Yes |
| `HitdMapLayer.custom(...)` | Custom vector tile layer | Configurable |

## Controller Methods

```dart
// Camera control
await controller.moveCamera(LatLng(30.0, -97.0), zoom: 14);
await controller.moveToBounds(bounds);
await controller.zoomIn();
await controller.zoomOut();

// Layer management
await controller.addLayer(HitdMapLayer.wetlands());
await controller.setLayerVisibility('parcels', false);
await controller.toggleLayer('public-lands');

// State switching (for state-specific data)
await controller.switchState('ca');

// Feature queries
final features = await controller.queryFeaturesAtPoint(screenPoint);

// Annotations
final marker = await controller.addMarker(position, iconImage: 'pin');
await controller.addLine(points, lineColor: '#FF0000');
await controller.addPolygon(boundary, fillColor: '#00FF00', fillOpacity: 0.3);
```

## Widgets

### Wind Overlay

```dart
Stack(
  children: [
    HitdMap(...),
    MapWindOverlay(
      currentWind: windService.currentWind.value,
      onTap: () => _showWindDetails(),
    ),
  ],
)
```

### Solunar Overlay

```dart
Stack(
  children: [
    HitdMap(...),
    MapSolunarOverlay(
      rating: solunarService.getCurrentRating(lat, lng),
      moonPhase: solunarService.getMoonPhase(DateTime.now()),
      activePeriod: solunarService.getCurrentPeriod(lat, lng),
      onTap: () => _showSolunarDetails(),
    ),
  ],
)
```

## Data Pipeline

This package is designed to work with PMTiles generated from:
- County assessor parcel data
- PAD-US public lands data
- State wildlife management areas
- National Wetlands Inventory
- Other GIS data sources

See the [data-pipeline](https://github.com/RORHITD/hitd_maps/tree/main/data-pipeline) directory for scripts to download and process this data.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Houston IT Developers LLC
- Website: [houstonitdev.com](https://houstonitdev.com)
- GitHub: [@RORHITD](https://github.com/RORHITD/hitd_maps)
