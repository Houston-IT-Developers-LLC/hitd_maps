# Integration Guide

How to integrate HITD Maps into your Flutter application.

## Table of Contents

1. [Installation](#installation)
2. [Basic Setup](#basic-setup)
3. [Configuration Options](#configuration-options)
4. [Adding Layers](#adding-layers)
5. [Handling User Interactions](#handling-user-interactions)
6. [Using Services](#using-services)
7. [Customization](#customization)
8. [Best Practices](#best-practices)

---

## Installation

### From GitHub (Recommended)

Add to your `pubspec.yaml`:

```yaml
dependencies:
  hitd_maps:
    git:
      url: https://github.com/Houston-IT-Developers/hitd_maps.git
      ref: main  # or specific version tag like v1.0.0
```

### From Local Path (Development)

```yaml
dependencies:
  hitd_maps:
    path: ../hitd_maps
```

### Install Dependencies

```bash
flutter pub get
```

---

## Basic Setup

### 1. Initialize Configuration

In your `main.dart`, initialize before `runApp()`:

```dart
import 'package:flutter/material.dart';
import 'package:hitd_maps/hitd_maps.dart';

void main() {
  // Option A: Custom configuration
  HitdMapConfig.initialize(
    pmtilesBaseUrl: 'https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels',
    basemapStyleUrl: 'assets/map/basemap_style.json',
    debugMode: true,  // Enable for development
  );

  // Option B: Use preset
  // HitdMapPresets.useGSpotOutdoors(debugMode: true);

  runApp(MyApp());
}
```

### 2. Add Basemap Style Asset

Create `assets/map/basemap_style.json` or use a URL. Example minimal style:

```json
{
  "version": 8,
  "name": "Basic",
  "sources": {
    "protomaps": {
      "type": "vector",
      "url": "pmtiles://https://your-basemap-url/basemap.pmtiles"
    }
  },
  "layers": [
    {
      "id": "background",
      "type": "background",
      "paint": {"background-color": "#f8f4f0"}
    }
  ]
}
```

Add to `pubspec.yaml`:

```yaml
flutter:
  assets:
    - assets/map/
```

### 3. Add the Map Widget

```dart
import 'package:hitd_maps/hitd_maps.dart';

class MapScreen extends StatefulWidget {
  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  HitdMapController? _controller;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: HitdMap(
        initialPosition: LatLng(30.2672, -97.7431),  // Austin, TX
        initialZoom: 12.0,
        layers: [
          HitdMapLayer.parcels(),
          HitdMapLayer.publicLands(),
        ],
        onMapCreated: (controller) {
          setState(() => _controller = controller);
        },
        onFeatureTap: _handleFeatureTap,
      ),
    );
  }

  void _handleFeatureTap(LatLng latLng, Map<String, dynamic>? properties) {
    if (properties != null) {
      final parcel = ParcelInfo.fromProperties(properties);
      _showParcelSheet(parcel);
    }
  }

  void _showParcelSheet(ParcelInfo parcel) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Container(
        padding: EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(parcel.ownerName ?? 'Unknown Owner',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 8),
            Text(parcel.address ?? 'No address'),
            SizedBox(height: 8),
            Row(
              children: [
                Chip(label: Text(parcel.formattedAcreage ?? 'N/A')),
                SizedBox(width: 8),
                Chip(label: Text(parcel.formattedMarketValue ?? 'N/A')),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## Configuration Options

### HitdMapConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pmtilesBaseUrl` | String | Required | Base URL for your tile CDN |
| `basemapStyleUrl` | String | Required | MapLibre style JSON URL/asset |
| `usePmtilesProtocol` | bool | `true` | Use `pmtiles://` protocol |
| `defaultZoom` | double | `14.0` | Default map zoom level |
| `minZoom` | double | `4.0` | Minimum allowed zoom |
| `maxZoom` | double | `18.0` | Maximum allowed zoom |
| `debugMode` | bool | `false` | Enable debug logging |
| `cacheDurationMinutes` | int | `30` | Cache duration for API calls |
| `openMeteoBaseUrl` | String | Open-Meteo URL | Weather API base URL |

### Example: Production vs Development

```dart
if (kDebugMode) {
  HitdMapConfig.initialize(
    pmtilesBaseUrl: 'http://localhost:8080/tiles',
    basemapStyleUrl: 'https://demotiles.maplibre.org/style.json',
    debugMode: true,
  );
} else {
  HitdMapPresets.useGSpotOutdoors();
}
```

---

## Adding Layers

### Built-in Layer Types

```dart
// Property boundaries (state-specific)
HitdMapLayer.parcels()

// All public lands (nationwide)
HitdMapLayer.publicLands()

// BLM lands
HitdMapLayer.blmLands()

// National Forest
HitdMapLayer.nationalForest()

// Wetlands (state-specific)
HitdMapLayer.wetlands()

// Wildlife Management Areas (state-specific)
HitdMapLayer.wma()
```

### Customizing Layer Appearance

```dart
HitdMapLayer.parcels(
  fillColor: Colors.red.withOpacity(0.3),
  lineColor: Colors.red,
  fillOpacity: 0.2,
  visible: true,
)

HitdMapLayer.publicLands(
  fillColor: Color(0xFF4CAF50),
  fillOpacity: 0.25,
  visible: false,  // Hidden by default
)
```

### Custom Layers

```dart
HitdMapLayer.custom(
  id: 'hunting-units',
  displayName: 'Hunting Units',
  sourceLayer: 'units',
  pmtilesFilename: 'hunting_units_tx.pmtiles',
  isStateSpecific: true,
  fillColor: Colors.orange,
  fillOpacity: 0.2,
  minZoom: 8,
  maxZoom: 16,
)
```

### Dynamic Layer Management

```dart
// Add layer after map created
await _controller.addLayer(HitdMapLayer.wetlands());

// Remove layer
await _controller.removeLayer('wetlands');

// Toggle visibility
await _controller.toggleLayer('public-lands');

// Set visibility explicitly
await _controller.setLayerVisibility('parcels', false);

// Check if visible
bool isVisible = _controller.isLayerVisible('parcels');
```

---

## Handling User Interactions

### Feature Taps

```dart
HitdMap(
  onFeatureTap: (LatLng latLng, Map<String, dynamic>? properties) {
    if (properties == null) {
      // Tapped on empty area
      return;
    }

    // Check which layer was tapped (by properties present)
    if (properties.containsKey('owner_name') || properties.containsKey('OWNER')) {
      // Parcel tapped
      final parcel = ParcelInfo.fromProperties(properties);
      _showParcelDetails(parcel);
    } else if (properties.containsKey('Unit_Nm') || properties.containsKey('Mang_Name')) {
      // Public land tapped
      final land = PublicLandInfo.fromProperties(properties);
      _showPublicLandDetails(land);
    }
  },
)
```

### Map Taps (Any Location)

```dart
HitdMap(
  onTap: (LatLng latLng) {
    print('Tapped at: ${latLng.latitude}, ${latLng.longitude}');

    // Example: Drop a pin
    _controller?.addMarker(latLng, iconImage: 'pin');
  },
)
```

### Camera Events

```dart
HitdMap(
  onCameraIdle: (CameraPosition position) {
    print('Zoom: ${position.zoom}');
    print('Center: ${position.target}');

    // Example: Load data for visible area
    _loadAreaData(position.target);
  },
)
```

---

## Using Services

### Solunar Calculator

```dart
import 'package:hitd_maps/hitd_maps.dart';

final solunar = SolunarService();

// Get today's data
final today = solunar.getSolunarDay(
  30.2672,  // latitude
  -97.7431, // longitude
  DateTime.now(),
);

print('Day Rating: ${today.dayRating}/100');
print('Moon Phase: ${today.moonPhase.phase.displayName}');
print('Moon Phase Emoji: ${today.moonPhase.phase.emoji}');

// Get current instant rating
final currentRating = solunar.getCurrentRating(30.2672, -97.7431);

// Get next period
final nextPeriod = solunar.getNextPeriod(30.2672, -97.7431);
if (nextPeriod != null) {
  print('Next: ${nextPeriod.description}');
  print('Starts: ${nextPeriod.start}');
  print('Type: ${nextPeriod.type.displayName}');
}

// Get 7-day forecast
final forecast = solunar.getForecast(30.2672, -97.7431, days: 7);
for (final day in forecast) {
  print('${day.date}: Rating ${day.dayRating}');
}
```

### Wind Service

```dart
import 'package:hitd_maps/hitd_maps.dart';
import 'package:get/get.dart';

// Register service (if using GetX)
final wind = Get.put(WindService());

// Or instantiate directly
final wind = WindService();

// Get current wind
final current = await wind.getCurrentWind(30.2672, -97.7431);
print('Wind: ${current.speed} mph from ${current.cardinalDirection}');
print('Gusts: ${current.gusts} mph');

// Get hourly forecast
final forecast = await wind.getHourlyForecast(30.2672, -97.7431, hours: 24);

// Get hunting quality
final quality = wind.getHuntingQuality(current.speed);
print('Hunting conditions: ${quality.label}');

// Calculate scent cone direction
final scentDir = wind.getScentConeDirection(current.direction);
print('Scent travels: ${GeoUtils.degreesToCardinal(scentDir)}');

// Find best hunting hours
final bestHours = wind.getBestHuntingHours(forecast, limit: 5);
```

---

## Customization

### Adding Overlays

```dart
Stack(
  children: [
    HitdMap(...),

    // Wind overlay (top right)
    Obx(() => MapWindOverlay(
      currentWind: windService.currentWind.value,
      alignment: Alignment.topRight,
      padding: EdgeInsets.all(16),
      onTap: () => _showWindDetails(),
    )),

    // Solunar overlay (top left)
    MapSolunarOverlay(
      rating: solunarService.getCurrentRating(lat, lng),
      moonPhase: solunarService.getMoonPhase(DateTime.now()),
      activePeriod: solunarService.getCurrentPeriod(lat, lng),
      alignment: Alignment.topLeft,
      onTap: () => _showSolunarDetails(),
    ),
  ],
)
```

### Custom Colors

Override default colors:

```dart
// In your app's theme or constants
class AppMapColors {
  static const parcelFill = Color(0x33FF0000);
  static const parcelOutline = Color(0xFFCC0000);
  static const publicLands = Color(0xFF228B22);
}

// Use in layers
HitdMapLayer.parcels(
  fillColor: AppMapColors.parcelFill,
  lineColor: AppMapColors.parcelOutline,
)
```

### State Switching

```dart
// Switch to California data
await _controller.switchState('ca');

// Get current state
print(_controller.currentStateCode);  // 'ca'

// Get state name
print(HitdMapController.getStateName('ca'));  // 'California'

// List all available states
print(HitdMapController.availableStates);
```

---

## Best Practices

### 1. Initialize Early

```dart
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  HitdMapConfig.initialize(...);  // Before runApp
  runApp(MyApp());
}
```

### 2. Store Controller Reference

```dart
class _MapScreenState extends State<MapScreen> {
  HitdMapController? _controller;

  @override
  Widget build(BuildContext context) {
    return HitdMap(
      onMapCreated: (controller) {
        _controller = controller;
        _loadInitialData();
      },
    );
  }

  void _loadInitialData() {
    // Now safe to use controller
    _controller?.switchState(userPreferredState);
  }
}
```

### 3. Handle Null Safety

```dart
void _onFeatureTap(LatLng latLng, Map<String, dynamic>? properties) {
  if (properties == null) return;

  final parcel = ParcelInfo.fromProperties(properties);

  // Use null-aware operators
  final display = parcel.ownerName ?? 'Unknown Owner';
  final value = parcel.formattedMarketValue ?? 'Value not available';
}
```

### 4. Dispose Resources

```dart
@override
void dispose() {
  // Controller handles its own cleanup
  // But dispose any local resources
  _searchController.dispose();
  super.dispose();
}
```

### 5. Layer Visibility by Zoom

```dart
HitdMap(
  onCameraIdle: (position) {
    // Hide detailed layers when zoomed out
    if (position.zoom < 10) {
      _controller?.setLayerVisibility('parcels', false);
    } else {
      _controller?.setLayerVisibility('parcels', true);
    }
  },
)
```

### 6. Error Handling

```dart
try {
  await windService.getCurrentWind(lat, lng);
} catch (e) {
  // Handle gracefully
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text('Could not load wind data')),
  );
}
```

---

## Next Steps

- [Data Pipeline Documentation](DATA_PIPELINE.md) - How data is processed
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
- [API Reference](API_REFERENCE.md) - Full API documentation
