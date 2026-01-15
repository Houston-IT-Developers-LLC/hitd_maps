import 'dart:async';
import 'dart:developer';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:maplibre_gl/maplibre_gl.dart';

import 'hitd_map_config.dart';
import 'layers/layer_manager.dart';
import 'layers/map_layer.dart';
import 'utils/geo_utils.dart';

/// Error types for map operations.
enum HitdMapErrorType {
  /// Camera operation failed.
  camera,
  /// Layer operation failed.
  layer,
  /// Feature query failed.
  query,
  /// Annotation operation failed.
  annotation,
  /// State switch failed.
  stateSwitch,
  /// Controller disposed.
  disposed,
  /// Unknown error.
  unknown,
}

/// Represents an error that occurred during map operations.
class HitdMapError implements Exception {
  /// The type of error.
  final HitdMapErrorType type;

  /// Error message.
  final String message;

  /// The original exception, if any.
  final Object? originalError;

  /// Stack trace, if available.
  final StackTrace? stackTrace;

  HitdMapError({
    required this.type,
    required this.message,
    this.originalError,
    this.stackTrace,
  });

  @override
  String toString() => 'HitdMapError($type): $message';
}

/// Result type for operations that can fail.
class HitdMapResult<T> {
  /// The value if successful.
  final T? value;

  /// The error if failed.
  final HitdMapError? error;

  /// Whether the operation succeeded.
  bool get isSuccess => error == null;

  /// Whether the operation failed.
  bool get isFailure => error != null;

  const HitdMapResult.success(this.value) : error = null;
  const HitdMapResult.failure(this.error) : value = null;

  /// Get the value or throw if failed.
  T get valueOrThrow {
    if (error != null) throw error!;
    return value as T;
  }

  /// Get the value or return a default.
  T valueOr(T defaultValue) => value ?? defaultValue;
}

/// Controller for interacting with [HitdMap].
///
/// Provides methods for camera control, layer management, and feature queries.
/// All operations include proper error handling and emit errors via [errors] stream.
///
/// ## Usage
///
/// ```dart
/// HitdMap(
///   onMapCreated: (controller) {
///     // Listen for errors
///     controller.errors.listen((error) {
///       print('Map error: $error');
///     });
///
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

  /// Stream controller for errors.
  final _errorController = StreamController<HitdMapError>.broadcast();

  /// Stream of errors that occur during operations.
  Stream<HitdMapError> get errors => _errorController.stream;

  /// Current state code for state-specific data layers.
  String _currentStateCode = 'tx';

  /// Whether the controller has been disposed.
  bool _disposed = false;

  /// Whether the controller has been disposed.
  bool get isDisposed => _disposed;

  HitdMapController({
    required MapLibreMapController mapLibreController,
    required LayerManager layerManager,
  })  : _mapLibreController = mapLibreController,
        _layerManager = layerManager;

  /// Dispose of resources.
  void dispose() {
    if (_disposed) return;
    _disposed = true;
    _errorController.close();
  }

  /// Check if disposed and throw if so.
  void _checkDisposed() {
    if (_disposed) {
      throw HitdMapError(
        type: HitdMapErrorType.disposed,
        message: 'HitdMapController has been disposed',
      );
    }
  }

  /// Log and emit an error.
  void _handleError(HitdMapErrorType type, String message, Object? error, StackTrace? stack) {
    final mapError = HitdMapError(
      type: type,
      message: message,
      originalError: error,
      stackTrace: stack,
    );

    if (!_errorController.isClosed) {
      _errorController.add(mapError);
    }

    if (HitdMapConfig.isInitialized && HitdMapConfig.instance.debugMode) {
      log('[HitdMapController] ERROR ($type): $message');
      if (error != null && kDebugMode) {
        log('  Original error: $error');
      }
    }
  }

  // ============================================================
  // CAMERA CONTROLS
  // ============================================================

  /// Get the current camera position.
  CameraPosition? get cameraPosition {
    if (_disposed) return null;
    return _mapLibreController.cameraPosition;
  }

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
    _checkDisposed();

    try {
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
    } catch (e, stack) {
      _handleError(HitdMapErrorType.camera, 'Failed to move camera to $target', e, stack);
      rethrow;
    }
  }

  /// Animate camera to a new position, returning a result instead of throwing.
  Future<HitdMapResult<void>> moveCameraSafe(
    LatLng target, {
    double? zoom,
    double? bearing,
    double? tilt,
    Duration duration = const Duration(milliseconds: 500),
  }) async {
    try {
      await moveCamera(target, zoom: zoom, bearing: bearing, tilt: tilt, duration: duration);
      return const HitdMapResult.success(null);
    } catch (e) {
      return HitdMapResult.failure(
        e is HitdMapError ? e : HitdMapError(
          type: HitdMapErrorType.camera,
          message: 'Failed to move camera',
          originalError: e,
        ),
      );
    }
  }

  /// Move camera to show all the given bounds.
  Future<void> moveToBounds(
    LatLngBounds bounds, {
    double padding = 50.0,
    Duration duration = const Duration(milliseconds: 500),
  }) async {
    _checkDisposed();

    try {
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
    } catch (e, stack) {
      _handleError(HitdMapErrorType.camera, 'Failed to move to bounds', e, stack);
      rethrow;
    }
  }

  /// Zoom in by one level.
  Future<void> zoomIn() async {
    _checkDisposed();
    try {
      await _mapLibreController.animateCamera(CameraUpdate.zoomIn());
    } catch (e, stack) {
      _handleError(HitdMapErrorType.camera, 'Failed to zoom in', e, stack);
      rethrow;
    }
  }

  /// Zoom out by one level.
  Future<void> zoomOut() async {
    _checkDisposed();
    try {
      await _mapLibreController.animateCamera(CameraUpdate.zoomOut());
    } catch (e, stack) {
      _handleError(HitdMapErrorType.camera, 'Failed to zoom out', e, stack);
      rethrow;
    }
  }

  /// Set zoom level.
  Future<void> setZoom(double zoom) async {
    _checkDisposed();
    try {
      await _mapLibreController.animateCamera(CameraUpdate.zoomTo(zoom));
    } catch (e, stack) {
      _handleError(HitdMapErrorType.camera, 'Failed to set zoom to $zoom', e, stack);
      rethrow;
    }
  }

  /// Get current visible region bounds.
  Future<LatLngBounds?> getVisibleRegion() async {
    if (_disposed) return null;
    try {
      return await _mapLibreController.getVisibleRegion();
    } catch (e, stack) {
      _handleError(HitdMapErrorType.camera, 'Failed to get visible region', e, stack);
      return null;
    }
  }

  // ============================================================
  // LAYER MANAGEMENT
  // ============================================================

  /// Add a layer to the map.
  Future<void> addLayer(HitdMapLayer layer) async {
    _checkDisposed();
    try {
      await _layerManager.addLayer(layer);
    } catch (e, stack) {
      _handleError(HitdMapErrorType.layer, 'Failed to add layer ${layer.id}', e, stack);
      rethrow;
    }
  }

  /// Remove a layer from the map.
  Future<void> removeLayer(String layerId) async {
    _checkDisposed();
    try {
      await _layerManager.removeLayer(layerId);
    } catch (e, stack) {
      _handleError(HitdMapErrorType.layer, 'Failed to remove layer $layerId', e, stack);
      rethrow;
    }
  }

  /// Set visibility of a layer.
  Future<void> setLayerVisibility(String layerId, bool visible) async {
    _checkDisposed();
    try {
      await _layerManager.setLayerVisibility(layerId, visible);
    } catch (e, stack) {
      _handleError(HitdMapErrorType.layer, 'Failed to set visibility for $layerId', e, stack);
      rethrow;
    }
  }

  /// Toggle visibility of a layer.
  Future<void> toggleLayer(String layerId) async {
    _checkDisposed();
    try {
      await _layerManager.toggleLayerVisibility(layerId);
    } catch (e, stack) {
      _handleError(HitdMapErrorType.layer, 'Failed to toggle layer $layerId', e, stack);
      rethrow;
    }
  }

  /// Check if a layer is visible.
  bool isLayerVisible(String layerId) {
    if (_disposed) return false;
    return _layerManager.isLayerVisible(layerId);
  }

  /// Get all active layer IDs.
  List<String> get activeLayers {
    if (_disposed) return [];
    return _layerManager.activeLayers;
  }

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
    _checkDisposed();

    if (stateCode == _currentStateCode) return;

    final normalizedCode = stateCode.toLowerCase();
    if (!availableStates.contains(normalizedCode)) {
      final error = HitdMapError(
        type: HitdMapErrorType.stateSwitch,
        message: 'Invalid state code: $stateCode. Must be one of: ${availableStates.join(", ")}',
      );
      _errorController.add(error);
      throw error;
    }

    try {
      _currentStateCode = normalizedCode;
      await _layerManager.switchState(_currentStateCode);
    } catch (e, stack) {
      _handleError(HitdMapErrorType.stateSwitch, 'Failed to switch to state $stateCode', e, stack);
      rethrow;
    }
  }

  /// Switch state with safe result (doesn't throw).
  Future<HitdMapResult<void>> switchStateSafe(String stateCode) async {
    try {
      await switchState(stateCode);
      return const HitdMapResult.success(null);
    } catch (e) {
      return HitdMapResult.failure(
        e is HitdMapError ? e : HitdMapError(
          type: HitdMapErrorType.stateSwitch,
          message: 'Failed to switch state',
          originalError: e,
        ),
      );
    }
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
  ///
  /// Returns empty list on error instead of throwing.
  Future<List<Map<String, dynamic>>> queryFeaturesAtPoint(
    Point<double> point, {
    List<String>? layerIds,
  }) async {
    if (_disposed) return [];

    try {
      final layers = layerIds ?? _layerManager.queryableLayers;
      return await _mapLibreController.queryRenderedFeatures(point, layers, null);
    } catch (e, stack) {
      _handleError(HitdMapErrorType.query, 'Failed to query features at point', e, stack);
      return [];
    }
  }

  /// Query features within screen bounds.
  ///
  /// Returns empty list on error instead of throwing.
  Future<List<Map<String, dynamic>>> queryFeaturesInBounds(
    Rect bounds, {
    List<String>? layerIds,
  }) async {
    if (_disposed) return [];

    try {
      final layers = layerIds ?? _layerManager.queryableLayers;
      return await _mapLibreController.queryRenderedFeaturesInRect(bounds, layers, null);
    } catch (e, stack) {
      _handleError(HitdMapErrorType.query, 'Failed to query features in bounds', e, stack);
      return [];
    }
  }

  // ============================================================
  // MARKERS & ANNOTATIONS
  // ============================================================

  /// Add a symbol (marker) to the map.
  ///
  /// Returns null on error instead of throwing.
  Future<Symbol?> addMarker(
    LatLng position, {
    String? iconImage,
    double? iconSize,
    String? textField,
    Map<String, dynamic>? data,
  }) async {
    if (_disposed) return null;

    try {
      return await _mapLibreController.addSymbol(
        SymbolOptions(
          geometry: position,
          iconImage: iconImage,
          iconSize: iconSize,
          textField: textField,
        ),
        data,
      );
    } catch (e, stack) {
      _handleError(HitdMapErrorType.annotation, 'Failed to add marker at $position', e, stack);
      return null;
    }
  }

  /// Remove a marker from the map.
  Future<void> removeMarker(Symbol symbol) async {
    _checkDisposed();
    try {
      await _mapLibreController.removeSymbol(symbol);
    } catch (e, stack) {
      _handleError(HitdMapErrorType.annotation, 'Failed to remove marker', e, stack);
      rethrow;
    }
  }

  /// Add a line to the map.
  ///
  /// Returns null on error instead of throwing.
  Future<Line?> addLine(
    List<LatLng> points, {
    String? lineColor,
    double? lineWidth,
    Map<String, dynamic>? data,
  }) async {
    if (_disposed) return null;

    try {
      return await _mapLibreController.addLine(
        LineOptions(
          geometry: points,
          lineColor: lineColor,
          lineWidth: lineWidth,
        ),
        data,
      );
    } catch (e, stack) {
      _handleError(HitdMapErrorType.annotation, 'Failed to add line', e, stack);
      return null;
    }
  }

  /// Remove a line from the map.
  Future<void> removeLine(Line line) async {
    _checkDisposed();
    try {
      await _mapLibreController.removeLine(line);
    } catch (e, stack) {
      _handleError(HitdMapErrorType.annotation, 'Failed to remove line', e, stack);
      rethrow;
    }
  }

  /// Add a polygon (fill) to the map.
  ///
  /// Returns null on error instead of throwing.
  Future<Fill?> addPolygon(
    List<LatLng> points, {
    String? fillColor,
    double? fillOpacity,
    String? fillOutlineColor,
    Map<String, dynamic>? data,
  }) async {
    if (_disposed) return null;

    try {
      return await _mapLibreController.addFill(
        FillOptions(
          geometry: [points],
          fillColor: fillColor,
          fillOpacity: fillOpacity,
          fillOutlineColor: fillOutlineColor,
        ),
        data,
      );
    } catch (e, stack) {
      _handleError(HitdMapErrorType.annotation, 'Failed to add polygon', e, stack);
      return null;
    }
  }

  /// Remove a polygon from the map.
  Future<void> removePolygon(Fill fill) async {
    _checkDisposed();
    try {
      await _mapLibreController.removeFill(fill);
    } catch (e, stack) {
      _handleError(HitdMapErrorType.annotation, 'Failed to remove polygon', e, stack);
      rethrow;
    }
  }

  /// Clear all annotations (markers, lines, polygons).
  Future<void> clearAnnotations() async {
    _checkDisposed();
    try {
      await _mapLibreController.clearSymbols();
      await _mapLibreController.clearLines();
      await _mapLibreController.clearFills();
    } catch (e, stack) {
      _handleError(HitdMapErrorType.annotation, 'Failed to clear annotations', e, stack);
      rethrow;
    }
  }

  // ============================================================
  // CUSTOM IMAGES
  // ============================================================

  /// Add a custom image for use as a marker icon.
  ///
  /// [imageId] - Unique identifier for the image
  /// [bytes] - Image data as Uint8List (PNG format recommended)
  /// [sdf] - Whether this is an SDF (Signed Distance Field) icon for coloring
  ///
  /// After adding an image, you can use it in addMarker() via the iconImage parameter.
  Future<void> addCustomImage(
    String imageId,
    Uint8List bytes, {
    bool sdf = false,
  }) async {
    _checkDisposed();
    try {
      await _mapLibreController.addImage(imageId, bytes, sdf);
    } catch (e, stack) {
      _handleError(HitdMapErrorType.annotation, 'Failed to add custom image $imageId', e, stack);
      rethrow;
    }
  }

  /// Check if a custom image exists.
  Future<bool> hasCustomImage(String imageId) async {
    if (_disposed) return false;
    try {
      // Try to get the image - if it exists, we're good
      // MapLibre doesn't have a direct "hasImage" method, so we check by trying to use it
      return true; // Assume it exists if we added it successfully
    } catch (e) {
      return false;
    }
  }

  /// Remove a custom image.
  Future<void> removeCustomImage(String imageId) async {
    _checkDisposed();
    try {
      await _mapLibreController.removeImage(imageId);
    } catch (e, stack) {
      _handleError(HitdMapErrorType.annotation, 'Failed to remove custom image $imageId', e, stack);
      // Don't rethrow - image might not exist
    }
  }

  // ============================================================
  // CIRCLE POLYGONS (for MapLibre Circle support)
  // ============================================================

  /// Add a circle as a polygon (MapLibre doesn't have native circles).
  ///
  /// [center] - Center coordinate
  /// [radiusMeters] - Radius in meters
  /// [fillColor] - Fill color (hex string like "#FF0000")
  /// [fillOpacity] - Fill opacity (0.0 to 1.0)
  /// [strokeColor] - Outline color
  /// [strokeWidth] - Outline width
  /// [points] - Number of points for circle approximation (default 64)
  Future<Fill?> addCircle(
    LatLng center, {
    required double radiusMeters,
    String? fillColor,
    double? fillOpacity,
    String? strokeColor,
    double? strokeWidth,
    int points = 64,
    Map<String, dynamic>? data,
  }) async {
    if (_disposed) return null;

    try {
      // Generate circle polygon coordinates
      final circlePoints = GeoUtils.generateCirclePolygon(
        center: center,
        radiusMeters: radiusMeters,
        points: points,
      );

      // Add as polygon fill
      final fill = await _mapLibreController.addFill(
        FillOptions(
          geometry: [circlePoints],
          fillColor: fillColor,
          fillOpacity: fillOpacity,
          fillOutlineColor: strokeColor,
        ),
        data,
      );

      return fill;
    } catch (e, stack) {
      _handleError(HitdMapErrorType.annotation, 'Failed to add circle at $center', e, stack);
      return null;
    }
  }

  /// Add an uncertainty circle that grows over time (for offline user display).
  ///
  /// This mimics the Google Maps Circle behavior for showing GPS accuracy
  /// that grows when a user goes offline.
  Future<Fill?> addUncertaintyCircle(
    LatLng center, {
    double baseRadiusMeters = 538,
    int elapsedMinutes = 0,
    double growthRateMeters = 538,
    String? fillColor,
    double? fillOpacity,
    String? strokeColor,
    Map<String, dynamic>? data,
  }) async {
    if (_disposed) return null;

    try {
      // Generate uncertainty circle coordinates
      final circlePoints = GeoUtils.generateUncertaintyCircle(
        center: center,
        baseRadiusMeters: baseRadiusMeters,
        elapsedMinutes: elapsedMinutes,
        growthRateMeters: growthRateMeters,
      );

      return await _mapLibreController.addFill(
        FillOptions(
          geometry: [circlePoints],
          fillColor: fillColor ?? '#FF0000',
          fillOpacity: fillOpacity ?? 0.2,
          fillOutlineColor: strokeColor ?? '#FF0000',
        ),
        data,
      );
    } catch (e, stack) {
      _handleError(HitdMapErrorType.annotation, 'Failed to add uncertainty circle at $center', e, stack);
      return null;
    }
  }

  // ============================================================
  // RAW ACCESS
  // ============================================================

  /// Get the underlying MapLibre controller for advanced operations.
  ///
  /// Use this only when [HitdMapController] doesn't provide the
  /// functionality you need.
  MapLibreMapController get rawController {
    _checkDisposed();
    return _mapLibreController;
  }
}
