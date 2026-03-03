/// Configuration for HITD Maps package
///
/// Use [HitdMapConfig] to configure the map package with your
/// tile server URLs, API keys, and default settings.
library;

import 'package:flutter/foundation.dart';

/// Global configuration for the HITD Maps package.
///
/// Call [HitdMapConfig.initialize] before using any map features:
///
/// ```dart
/// void main() {
///   HitdMapConfig.initialize(
///     pmtilesBaseUrl: 'https://your-cdn.com/tiles',
///     basemapStyleUrl: 'https://your-cdn.com/style.json',
///   );
///   runApp(MyApp());
/// }
/// ```
class HitdMapConfig {
  static HitdMapConfig? _instance;

  /// Base URL for PMTiles hosted on your CDN (e.g., Cloudflare R2)
  final String pmtilesBaseUrl;

  /// URL or asset path for the basemap style JSON
  final String basemapStyleUrl;

  /// Whether to use the pmtiles:// protocol (requires MapLibre Native 6.14+)
  final bool usePmtilesProtocol;

  /// Default zoom level for maps
  final double defaultZoom;

  /// Minimum zoom level allowed
  final double minZoom;

  /// Maximum zoom level allowed
  final double maxZoom;

  /// Enable debug logging
  final bool debugMode;

  /// Cache duration for tile data (in minutes)
  final int cacheDurationMinutes;

  /// Open-Meteo API base URL (for wind data)
  final String openMeteoBaseUrl;

  HitdMapConfig._({
    required this.pmtilesBaseUrl,
    required this.basemapStyleUrl,
    this.usePmtilesProtocol = true,
    this.defaultZoom = 14.0,
    this.minZoom = 4.0,
    this.maxZoom = 18.0,
    this.debugMode = false,
    this.cacheDurationMinutes = 30,
    this.openMeteoBaseUrl = 'https://api.open-meteo.com/v1',
  });

  /// Initialize the HITD Maps configuration.
  ///
  /// Must be called before using any map features.
  ///
  /// [pmtilesBaseUrl] - Base URL where your PMTiles are hosted
  /// [basemapStyleUrl] - URL or asset path for MapLibre style JSON
  static void initialize({
    required String pmtilesBaseUrl,
    required String basemapStyleUrl,
    bool usePmtilesProtocol = true,
    double defaultZoom = 14.0,
    double minZoom = 4.0,
    double maxZoom = 18.0,
    bool debugMode = false,
    int cacheDurationMinutes = 30,
    String openMeteoBaseUrl = 'https://api.open-meteo.com/v1',
  }) {
    _instance = HitdMapConfig._(
      pmtilesBaseUrl: pmtilesBaseUrl,
      basemapStyleUrl: basemapStyleUrl,
      usePmtilesProtocol: usePmtilesProtocol,
      defaultZoom: defaultZoom,
      minZoom: minZoom,
      maxZoom: maxZoom,
      debugMode: debugMode,
      cacheDurationMinutes: cacheDurationMinutes,
      openMeteoBaseUrl: openMeteoBaseUrl,
    );
  }

  /// Get the current configuration instance.
  ///
  /// Throws [StateError] if [initialize] hasn't been called.
  static HitdMapConfig get instance {
    if (_instance == null) {
      throw StateError(
        'HitdMapConfig has not been initialized. '
        'Call HitdMapConfig.initialize() before using HITD Maps.',
      );
    }
    return _instance!;
  }

  /// Check if the configuration has been initialized.
  static bool get isInitialized => _instance != null;

  /// Reset configuration (for testing only).
  @visibleForTesting
  static void resetForTesting() {
    _instance = null;
  }

  /// Get PMTiles URL for a specific layer and state.
  String getPmtilesUrl(String layerName, {String? stateCode}) {
    final filename = stateCode != null
        ? '${layerName}_${stateCode.toLowerCase()}.pmtiles'
        : '$layerName.pmtiles';

    if (usePmtilesProtocol) {
      return 'pmtiles://$pmtilesBaseUrl/$filename';
    }
    return '$pmtilesBaseUrl/$filename';
  }
}

/// Predefined tile configurations for common setups.
class HitdMapPresets {
  HitdMapPresets._();

  /// Configuration for GSpot Outdoors Cloudflare R2 setup.
  ///
  /// Uses the production GSpot Outdoors tile server with
  /// the outdoor-focused basemap.
  static void useGSpotOutdoors({bool debugMode = false}) {
    HitdMapConfig.initialize(
      pmtilesBaseUrl: 'https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev',
      basemapStyleUrl: HitdMapStyles.osmSimple,
      debugMode: debugMode,
    );
  }

  /// Configuration for local development with test tiles.
  static void useLocalDevelopment() {
    HitdMapConfig.initialize(
      pmtilesBaseUrl: 'http://localhost:8080/tiles',
      basemapStyleUrl: HitdMapStyles.osmSimple,
      debugMode: true,
    );
  }

  /// Configuration using free OSM tiles only (no API key required).
  ///
  /// Best for development and testing without a tile provider account.
  static void useFreeOsm({bool debugMode = false}) {
    HitdMapConfig.initialize(
      pmtilesBaseUrl: '', // No PMTiles in this mode
      basemapStyleUrl: HitdMapStyles.osmSimple,
      debugMode: debugMode,
    );
  }

  /// Configuration with MapTiler outdoor style.
  ///
  /// Requires a MapTiler API key. Get one at https://www.maptiler.com/
  static void useMapTilerOutdoor({
    required String apiKey,
    String? pmtilesBaseUrl,
    bool debugMode = false,
  }) {
    HitdMapConfig.initialize(
      pmtilesBaseUrl: pmtilesBaseUrl ?? '',
      basemapStyleUrl: 'https://api.maptiler.com/maps/outdoor/style.json?key=$apiKey',
      debugMode: debugMode,
    );
  }
}

/// Built-in map style paths.
///
/// These are asset paths bundled with the hitd_maps package.
class HitdMapStyles {
  HitdMapStyles._();

  /// Simple OSM raster basemap (free, no API key).
  static const String osmSimple = 'packages/hitd_maps/assets/styles/osm_simple.json';

  /// Outdoor-focused vector basemap (requires MapTiler key).
  static const String outdoorBasemap = 'packages/hitd_maps/assets/styles/outdoor_basemap.json';

  /// Demo tiles URL for testing (MapLibre demo).
  static const String demotiles = 'https://demotiles.maplibre.org/style.json';
}
