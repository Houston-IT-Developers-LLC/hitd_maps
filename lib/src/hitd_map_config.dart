/// Configuration for HITD Maps package
///
/// Use [HitdMapConfig] to configure the map package with your
/// tile server URLs, API keys, and default settings.
library;

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

/// Predefined tile configurations for common setups
class HitdMapPresets {
  HitdMapPresets._();

  /// Configuration for GSpot Outdoors Cloudflare R2 setup
  static void useGSpotOutdoors({bool debugMode = false}) {
    HitdMapConfig.initialize(
      pmtilesBaseUrl: 'https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels',
      basemapStyleUrl: 'assets/map/basemap_style.json',
      debugMode: debugMode,
    );
  }

  /// Configuration for local development with test tiles
  static void useLocalDevelopment() {
    HitdMapConfig.initialize(
      pmtilesBaseUrl: 'http://localhost:8080/tiles',
      basemapStyleUrl: 'assets/styles/osm_liberty.json',
      debugMode: true,
    );
  }
}
