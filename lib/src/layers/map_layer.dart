import 'package:flutter/material.dart';

import '../hitd_map_config.dart';

/// Represents a map layer that can be added to [HitdMap].
///
/// Layers can be created using factory constructors for common types:
/// - [HitdMapLayer.parcels] - Property boundary data
/// - [HitdMapLayer.publicLands] - Federal and state public lands
/// - [HitdMapLayer.wetlands] - NWI wetland data
/// - [HitdMapLayer.custom] - Custom vector tile layer
class HitdMapLayer {
  /// Unique identifier for this layer.
  final String id;

  /// Display name for UI.
  final String displayName;

  /// Type of layer.
  final HitdLayerType type;

  /// Source ID in MapLibre.
  final String sourceId;

  /// Source layer name in the vector tiles.
  final String sourceLayer;

  /// PMTiles filename pattern (with {state} placeholder if state-specific).
  final String pmtilesPattern;

  /// Whether this layer requires state-specific data.
  final bool isStateSpecific;

  /// Minimum zoom level to show this layer.
  final double minZoom;

  /// Maximum zoom level to show this layer.
  final double maxZoom;

  /// Fill color (for polygon layers).
  final Color? fillColor;

  /// Fill opacity.
  final double fillOpacity;

  /// Line/outline color.
  final Color? lineColor;

  /// Line width.
  final double lineWidth;

  /// Line opacity.
  final double lineOpacity;

  /// Whether this layer is queryable (responds to taps).
  final bool queryable;

  /// Initial visibility.
  final bool visible;

  const HitdMapLayer._({
    required this.id,
    required this.displayName,
    required this.type,
    required this.sourceId,
    required this.sourceLayer,
    required this.pmtilesPattern,
    this.isStateSpecific = false,
    this.minZoom = 0,
    this.maxZoom = 24,
    this.fillColor,
    this.fillOpacity = 0.2,
    this.lineColor,
    this.lineWidth = 1.0,
    this.lineOpacity = 0.8,
    this.queryable = true,
    this.visible = true,
  });

  /// Create a parcel (property boundary) layer.
  ///
  /// Displays property boundaries from county assessor data.
  /// State-specific - requires state code to load data.
  factory HitdMapLayer.parcels({
    Color fillColor = const Color(0xFFE53935),
    Color lineColor = const Color(0xFFB71C1C),
    double fillOpacity = 0.15,
    bool visible = true,
  }) {
    return HitdMapLayer._(
      id: 'parcels',
      displayName: 'Property Boundaries',
      type: HitdLayerType.parcels,
      sourceId: 'parcels-source',
      sourceLayer: 'parcels',
      pmtilesPattern: 'parcels_{state}_statewide.pmtiles',
      isStateSpecific: true,
      minZoom: 10,
      maxZoom: 18,
      fillColor: fillColor,
      fillOpacity: fillOpacity,
      lineColor: lineColor,
      lineWidth: 1.0,
      queryable: true,
      visible: visible,
    );
  }

  /// Create a public lands layer.
  ///
  /// Displays federal and state public lands from PAD-US data.
  /// Nationwide data - does not require state code.
  factory HitdMapLayer.publicLands({
    Color fillColor = const Color(0xFF4CAF50),
    double fillOpacity = 0.2,
    bool visible = true,
  }) {
    return HitdMapLayer._(
      id: 'public-lands',
      displayName: 'Public Lands',
      type: HitdLayerType.publicLands,
      sourceId: 'public-lands-source',
      sourceLayer: 'public_lands',
      pmtilesPattern: 'public_lands.pmtiles',
      isStateSpecific: false,
      minZoom: 6,
      maxZoom: 18,
      fillColor: fillColor,
      fillOpacity: fillOpacity,
      lineColor: const Color(0xFF2E7D32),
      lineWidth: 1.5,
      queryable: true,
      visible: visible,
    );
  }

  /// Create a BLM lands layer.
  factory HitdMapLayer.blmLands({
    Color fillColor = const Color(0xFFFF9800),
    double fillOpacity = 0.2,
    bool visible = true,
  }) {
    return HitdMapLayer._(
      id: 'blm-lands',
      displayName: 'BLM Lands',
      type: HitdLayerType.blm,
      sourceId: 'blm-source',
      sourceLayer: 'blm',
      pmtilesPattern: 'blm.pmtiles',
      isStateSpecific: false,
      minZoom: 6,
      maxZoom: 18,
      fillColor: fillColor,
      fillOpacity: fillOpacity,
      lineColor: const Color(0xFFE65100),
      queryable: true,
      visible: visible,
    );
  }

  /// Create a National Forest layer.
  factory HitdMapLayer.nationalForest({
    Color fillColor = const Color(0xFF4CAF50),
    double fillOpacity = 0.2,
    bool visible = true,
  }) {
    return HitdMapLayer._(
      id: 'usfs-lands',
      displayName: 'National Forest',
      type: HitdLayerType.usfs,
      sourceId: 'usfs-source',
      sourceLayer: 'usfs',
      pmtilesPattern: 'usfs.pmtiles',
      isStateSpecific: false,
      minZoom: 6,
      maxZoom: 18,
      fillColor: fillColor,
      fillOpacity: fillOpacity,
      lineColor: const Color(0xFF1B5E20),
      queryable: true,
      visible: visible,
    );
  }

  /// Create a wetlands layer.
  factory HitdMapLayer.wetlands({
    Color fillColor = const Color(0xFF2196F3),
    double fillOpacity = 0.25,
    bool visible = false,
  }) {
    return HitdMapLayer._(
      id: 'wetlands',
      displayName: 'Wetlands',
      type: HitdLayerType.wetlands,
      sourceId: 'wetlands-source',
      sourceLayer: 'wetlands',
      pmtilesPattern: 'nwi_{state}.pmtiles',
      isStateSpecific: true,
      minZoom: 10,
      maxZoom: 18,
      fillColor: fillColor,
      fillOpacity: fillOpacity,
      lineColor: const Color(0xFF1565C0),
      queryable: true,
      visible: visible,
    );
  }

  /// Create a wildlife management area (WMA) layer.
  factory HitdMapLayer.wma({
    Color fillColor = const Color(0xFF8BC34A),
    double fillOpacity = 0.2,
    bool visible = true,
  }) {
    return HitdMapLayer._(
      id: 'wma',
      displayName: 'Wildlife Management Areas',
      type: HitdLayerType.wma,
      sourceId: 'wma-source',
      sourceLayer: 'wma',
      pmtilesPattern: 'wma_{state}.pmtiles',
      isStateSpecific: true,
      minZoom: 8,
      maxZoom: 18,
      fillColor: fillColor,
      fillOpacity: fillOpacity,
      lineColor: const Color(0xFF689F38),
      queryable: true,
      visible: visible,
    );
  }

  /// Create a custom vector tile layer.
  factory HitdMapLayer.custom({
    required String id,
    required String displayName,
    required String sourceLayer,
    required String pmtilesFilename,
    bool isStateSpecific = false,
    double minZoom = 0,
    double maxZoom = 24,
    Color? fillColor,
    double fillOpacity = 0.2,
    Color? lineColor,
    double lineWidth = 1.0,
    bool queryable = true,
    bool visible = true,
  }) {
    return HitdMapLayer._(
      id: id,
      displayName: displayName,
      type: HitdLayerType.custom,
      sourceId: '$id-source',
      sourceLayer: sourceLayer,
      pmtilesPattern: pmtilesFilename,
      isStateSpecific: isStateSpecific,
      minZoom: minZoom,
      maxZoom: maxZoom,
      fillColor: fillColor,
      fillOpacity: fillOpacity,
      lineColor: lineColor,
      lineWidth: lineWidth,
      queryable: queryable,
      visible: visible,
    );
  }

  /// Get the PMTiles URL for this layer.
  String getPmtilesUrl({String stateCode = 'tx'}) {
    final config = HitdMapConfig.instance;
    String filename = pmtilesPattern;

    if (isStateSpecific) {
      filename = filename.replaceAll('{state}', stateCode.toLowerCase());
    }

    if (config.usePmtilesProtocol) {
      return 'pmtiles://${config.pmtilesBaseUrl}/$filename';
    }
    return '${config.pmtilesBaseUrl}/$filename';
  }

  /// Create a copy with modified properties.
  HitdMapLayer copyWith({
    Color? fillColor,
    double? fillOpacity,
    Color? lineColor,
    double? lineWidth,
    double? lineOpacity,
    bool? visible,
    double? minZoom,
    double? maxZoom,
  }) {
    return HitdMapLayer._(
      id: id,
      displayName: displayName,
      type: type,
      sourceId: sourceId,
      sourceLayer: sourceLayer,
      pmtilesPattern: pmtilesPattern,
      isStateSpecific: isStateSpecific,
      minZoom: minZoom ?? this.minZoom,
      maxZoom: maxZoom ?? this.maxZoom,
      fillColor: fillColor ?? this.fillColor,
      fillOpacity: fillOpacity ?? this.fillOpacity,
      lineColor: lineColor ?? this.lineColor,
      lineWidth: lineWidth ?? this.lineWidth,
      lineOpacity: lineOpacity ?? this.lineOpacity,
      queryable: queryable,
      visible: visible ?? this.visible,
    );
  }
}

/// Types of map layers supported by HITD Maps.
enum HitdLayerType {
  /// Property boundaries from county assessor data.
  parcels,

  /// All public lands (PAD-US).
  publicLands,

  /// Bureau of Land Management lands.
  blm,

  /// US Forest Service lands.
  usfs,

  /// State lands.
  state,

  /// National Wildlife Refuge.
  nwr,

  /// Wildlife Management Areas.
  wma,

  /// National Wetlands Inventory.
  wetlands,

  /// Hydrography (rivers, streams, lakes).
  hydrography,

  /// Wildfires.
  wildfires,

  /// Crop data.
  crops,

  /// Terrain/elevation.
  terrain,

  /// Custom layer.
  custom,
}
