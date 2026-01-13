import 'dart:async';

import 'package:maplibre_gl/maplibre_gl.dart';

import 'layers/layer_manager.dart';
import 'layers/map_layer.dart';

/// Controller for interacting with [HitdMap].
///
/// Provides methods for camera control, layer management, and feature queries.
///
/// ## Usage
///
/// ```dart
/// HitdMap(
///   onMapCreated: (controller) {
///     // Move camera
///     controller.moveCamera(LatLng(30.0, -97.0), zoom: 12);
///
///     // Toggle layers
///     controller.setLayerVisibility('parcels', false);
///
///     // Switch state data
///     controller.switchState('tx');
///   },
/// )
/// ```
class HitdMapController {
  final MapLibreMapController _mapLibreController;
  final LayerManager _layerManager;

  /// Current state code for state-specific data layers.
  String _currentStateCode = 'tx';

  HitdMapController({
    required MapLibreMapController mapLibreController,
    required LayerManager layerManager,
  })  : _mapLibreController = mapLibreController,
        _layerManager = layerManager;

  /// Dispose of resources.
  void dispose() {
    // Cleanup if needed
  }

  // ============================================================
  // CAMERA CONTROLS
  // ============================================================

  /// Get the current camera position.
  CameraPosition? get cameraPosition => _mapLibreController.cameraPosition;

  /// Animate camera to a new position.
  ///
  /// [target] - Center coordinates
  /// [zoom] - Optional zoom level (keeps current if not specified)
  /// [bearing] - Optional bearing in degrees
  /// [tilt] - Optional tilt in degrees
  /// [duration] - Animation duration
  Future<void> moveCamera(
    LatLng target, {
    double? zoom,
    double? bearing,
    double? tilt,
    Duration duration = const Duration(milliseconds: 500),
  }) async {
    final currentPosition = _mapLibreController.cameraPosition;

    await _mapLibreController.animateCamera(
      CameraUpdate.newCameraPosition(
        CameraPosition(
          target: target,
          zoom: zoom ?? currentPosition?.zoom ?? 14.0,
          bearing: bearing ?? currentPosition?.bearing ?? 0.0,
          tilt: tilt ?? currentPosition?.tilt ?? 0.0,
        ),
      ),
      duration: duration,
    );
  }

  /// Move camera to show all the given bounds.
  Future<void> moveToBounds(
    LatLngBounds bounds, {
    double padding = 50.0,
    Duration duration = const Duration(milliseconds: 500),
  }) async {
    await _mapLibreController.animateCamera(
      CameraUpdate.newLatLngBounds(
        bounds,
        left: padding,
        top: padding,
        right: padding,
        bottom: padding,
      ),
      duration: duration,
    );
  }

  /// Zoom in by one level.
  Future<void> zoomIn() async {
    await _mapLibreController.animateCamera(CameraUpdate.zoomIn());
  }

  /// Zoom out by one level.
  Future<void> zoomOut() async {
    await _mapLibreController.animateCamera(CameraUpdate.zoomOut());
  }

  /// Set zoom level.
  Future<void> setZoom(double zoom) async {
    await _mapLibreController.animateCamera(CameraUpdate.zoomTo(zoom));
  }

  /// Get current visible region bounds.
  Future<LatLngBounds?> getVisibleRegion() async {
    return await _mapLibreController.getVisibleRegion();
  }

  // ============================================================
  // LAYER MANAGEMENT
  // ============================================================

  /// Add a layer to the map.
  Future<void> addLayer(HitdMapLayer layer) async {
    await _layerManager.addLayer(layer);
  }

  /// Remove a layer from the map.
  Future<void> removeLayer(String layerId) async {
    await _layerManager.removeLayer(layerId);
  }

  /// Set visibility of a layer.
  Future<void> setLayerVisibility(String layerId, bool visible) async {
    await _layerManager.setLayerVisibility(layerId, visible);
  }

  /// Toggle visibility of a layer.
  Future<void> toggleLayer(String layerId) async {
    await _layerManager.toggleLayerVisibility(layerId);
  }

  /// Check if a layer is visible.
  bool isLayerVisible(String layerId) {
    return _layerManager.isLayerVisible(layerId);
  }

  /// Get all active layer IDs.
  List<String> get activeLayers => _layerManager.activeLayers;

  // ============================================================
  // STATE MANAGEMENT (for state-specific data)
  // ============================================================

  /// Current state code (e.g., 'tx', 'ca', 'co').
  String get currentStateCode => _currentStateCode;

  /// Switch to a different state's data.
  ///
  /// This reloads state-specific layers (parcels, public lands, etc.)
  /// with data for the new state.
  Future<void> switchState(String stateCode) async {
    if (stateCode == _currentStateCode) return;

    _currentStateCode = stateCode.toLowerCase();
    await _layerManager.switchState(_currentStateCode);
  }

  /// Available state codes with data.
  static const List<String> availableStates = [
    'ak', 'al', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga',
    'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md',
    'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj',
    'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc',
    'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy',
  ];

  /// Get full state name from code.
  static String? getStateName(String stateCode) {
    return _stateNames[stateCode.toLowerCase()];
  }

  static const Map<String, String> _stateNames = {
    'ak': 'Alaska', 'al': 'Alabama', 'az': 'Arizona', 'ar': 'Arkansas',
    'ca': 'California', 'co': 'Colorado', 'ct': 'Connecticut', 'de': 'Delaware',
    'fl': 'Florida', 'ga': 'Georgia', 'hi': 'Hawaii', 'id': 'Idaho',
    'il': 'Illinois', 'in': 'Indiana', 'ia': 'Iowa', 'ks': 'Kansas',
    'ky': 'Kentucky', 'la': 'Louisiana', 'me': 'Maine', 'md': 'Maryland',
    'ma': 'Massachusetts', 'mi': 'Michigan', 'mn': 'Minnesota', 'ms': 'Mississippi',
    'mo': 'Missouri', 'mt': 'Montana', 'ne': 'Nebraska', 'nv': 'Nevada',
    'nh': 'New Hampshire', 'nj': 'New Jersey', 'nm': 'New Mexico', 'ny': 'New York',
    'nc': 'North Carolina', 'nd': 'North Dakota', 'oh': 'Ohio', 'ok': 'Oklahoma',
    'or': 'Oregon', 'pa': 'Pennsylvania', 'ri': 'Rhode Island', 'sc': 'South Carolina',
    'sd': 'South Dakota', 'tn': 'Tennessee', 'tx': 'Texas', 'ut': 'Utah',
    'vt': 'Vermont', 'va': 'Virginia', 'wa': 'Washington', 'wv': 'West Virginia',
    'wi': 'Wisconsin', 'wy': 'Wyoming',
  };

  // ============================================================
  // FEATURE QUERIES
  // ============================================================

  /// Query features at a screen point.
  Future<List<Map<String, dynamic>>> queryFeaturesAtPoint(
    Point<double> point, {
    List<String>? layerIds,
  }) async {
    final layers = layerIds ?? _layerManager.queryableLayers;
    return await _mapLibreController.queryRenderedFeatures(point, layers, null);
  }

  /// Query features within screen bounds.
  Future<List<Map<String, dynamic>>> queryFeaturesInBounds(
    Rect bounds, {
    List<String>? layerIds,
  }) async {
    final layers = layerIds ?? _layerManager.queryableLayers;
    return await _mapLibreController.queryRenderedFeaturesInRect(bounds, layers, null);
  }

  // ============================================================
  // MARKERS & ANNOTATIONS
  // ============================================================

  /// Add a symbol (marker) to the map.
  Future<Symbol> addMarker(
    LatLng position, {
    String? iconImage,
    double? iconSize,
    String? textField,
    Map<String, dynamic>? data,
  }) async {
    return await _mapLibreController.addSymbol(
      SymbolOptions(
        geometry: position,
        iconImage: iconImage,
        iconSize: iconSize,
        textField: textField,
      ),
      data,
    );
  }

  /// Remove a marker from the map.
  Future<void> removeMarker(Symbol symbol) async {
    await _mapLibreController.removeSymbol(symbol);
  }

  /// Add a line to the map.
  Future<Line> addLine(
    List<LatLng> points, {
    String? lineColor,
    double? lineWidth,
    Map<String, dynamic>? data,
  }) async {
    return await _mapLibreController.addLine(
      LineOptions(
        geometry: points,
        lineColor: lineColor,
        lineWidth: lineWidth,
      ),
      data,
    );
  }

  /// Remove a line from the map.
  Future<void> removeLine(Line line) async {
    await _mapLibreController.removeLine(line);
  }

  /// Add a polygon (fill) to the map.
  Future<Fill> addPolygon(
    List<LatLng> points, {
    String? fillColor,
    double? fillOpacity,
    String? fillOutlineColor,
    Map<String, dynamic>? data,
  }) async {
    return await _mapLibreController.addFill(
      FillOptions(
        geometry: [points],
        fillColor: fillColor,
        fillOpacity: fillOpacity,
        fillOutlineColor: fillOutlineColor,
      ),
      data,
    );
  }

  /// Remove a polygon from the map.
  Future<void> removePolygon(Fill fill) async {
    await _mapLibreController.removeFill(fill);
  }

  /// Clear all annotations (markers, lines, polygons).
  Future<void> clearAnnotations() async {
    await _mapLibreController.clearSymbols();
    await _mapLibreController.clearLines();
    await _mapLibreController.clearFills();
  }

  // ============================================================
  // RAW ACCESS
  // ============================================================

  /// Get the underlying MapLibre controller for advanced operations.
  ///
  /// Use this only when [HitdMapController] doesn't provide the
  /// functionality you need.
  MapLibreMapController get rawController => _mapLibreController;
}
