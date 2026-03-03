import 'dart:async';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:maplibre_gl/maplibre_gl.dart';

import 'hitd_map_config.dart';
import 'hitd_map_controller.dart';
import 'layers/layer_manager.dart';
import 'layers/map_layer.dart';

/// A customizable map widget with PMTiles and layer management support.
///
/// [HitdMap] provides a high-level interface for MapLibre GL maps with
/// built-in support for:
/// - PMTiles vector tile sources
/// - Layer management (parcels, public lands, etc.)
/// - Touch interaction handling
/// - Camera controls
///
/// ## Basic Usage
///
/// ```dart
/// HitdMap(
///   initialPosition: LatLng(30.2672, -97.7431),
///   initialZoom: 12.0,
///   layers: [HitdMapLayer.parcels()],
///   onMapCreated: (controller) {
///     // Store controller for later use
///   },
///   onTap: (latLng) {
///     print('Tapped at: $latLng');
///   },
/// )
/// ```
class HitdMap extends StatefulWidget {
  /// Initial center position for the map.
  final LatLng? initialPosition;

  /// Initial zoom level.
  final double initialZoom;

  /// Layers to display on the map.
  final List<HitdMapLayer> layers;

  /// Callback when the map is created and ready.
  final void Function(HitdMapController controller)? onMapCreated;

  /// Callback when the map is tapped.
  final void Function(LatLng latLng)? onTap;

  /// Callback when a feature is tapped (returns feature properties).
  final void Function(LatLng latLng, Map<String, dynamic>? properties)? onFeatureTap;

  /// Callback when the camera position changes.
  final void Function(CameraPosition position)? onCameraMove;

  /// Callback when camera movement ends.
  final void Function(CameraPosition position)? onCameraIdle;

  /// Whether to show the user's location.
  final bool showUserLocation;

  /// User location tracking mode.
  final MyLocationTrackingMode locationTrackingMode;

  /// Whether to show the compass.
  final bool compassEnabled;

  /// Whether to allow rotation gestures.
  final bool rotateGesturesEnabled;

  /// Whether to allow scroll gestures.
  final bool scrollGesturesEnabled;

  /// Whether to allow tilt gestures.
  final bool tiltGesturesEnabled;

  /// Whether to allow zoom gestures.
  final bool zoomGesturesEnabled;

  /// Custom style URL (overrides config).
  final String? styleUrl;

  /// Minimum zoom level (overrides config).
  final double? minZoom;

  /// Maximum zoom level (overrides config).
  final double? maxZoom;

  const HitdMap({
    super.key,
    this.initialPosition,
    this.initialZoom = 14.0,
    this.layers = const [],
    this.onMapCreated,
    this.onTap,
    this.onFeatureTap,
    this.onCameraMove,
    this.onCameraIdle,
    this.showUserLocation = true,
    this.locationTrackingMode = MyLocationTrackingMode.none,
    this.compassEnabled = true,
    this.rotateGesturesEnabled = true,
    this.scrollGesturesEnabled = true,
    this.tiltGesturesEnabled = true,
    this.zoomGesturesEnabled = true,
    this.styleUrl,
    this.minZoom,
    this.maxZoom,
  });

  @override
  State<HitdMap> createState() => _HitdMapState();
}

class _HitdMapState extends State<HitdMap> {
  MapLibreMapController? _mapLibreController;
  HitdMapController? _hitdController;
  LayerManager? _layerManager;
  bool _styleLoaded = false;

  @override
  void dispose() {
    _hitdController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final config = HitdMapConfig.instance;
    final styleUrl = widget.styleUrl ?? config.basemapStyleUrl;

    // Default to Houston, TX if no position provided
    final initialPosition = widget.initialPosition ?? const LatLng(29.7604, -95.3698);

    return MapLibreMap(
      styleString: styleUrl,
      initialCameraPosition: CameraPosition(
        target: initialPosition,
        zoom: widget.initialZoom,
      ),
      onMapCreated: _onMapCreated,
      onStyleLoadedCallback: _onStyleLoaded,
      onMapClick: _onMapClick,
      onCameraTrackingChanged: _onCameraTrackingChanged,
      onCameraIdle: _onCameraIdle,
      myLocationEnabled: widget.showUserLocation,
      myLocationTrackingMode: widget.locationTrackingMode,
      trackCameraPosition: true,
      compassEnabled: widget.compassEnabled,
      rotateGesturesEnabled: widget.rotateGesturesEnabled,
      scrollGesturesEnabled: widget.scrollGesturesEnabled,
      tiltGesturesEnabled: widget.tiltGesturesEnabled,
      zoomGesturesEnabled: widget.zoomGesturesEnabled,
      minMaxZoomPreference: MinMaxZoomPreference(
        widget.minZoom ?? config.minZoom,
        widget.maxZoom ?? config.maxZoom,
      ),
    );
  }

  void _onMapCreated(MapLibreMapController controller) {
    _mapLibreController = controller;
    _layerManager = LayerManager(controller);
    _hitdController = HitdMapController(
      mapLibreController: controller,
      layerManager: _layerManager!,
    );
  }

  Future<void> _onStyleLoaded() async {
    setState(() => _styleLoaded = true);

    // Style reload destroys all MapLibre sources/layers — recreate
    // LayerManager and controller so internal tracking is fresh.
    if (_mapLibreController != null) {
      _layerManager = LayerManager(_mapLibreController!);
      _hitdController = HitdMapController(
        mapLibreController: _mapLibreController!,
        layerManager: _layerManager!,
      );
    }

    if (_layerManager != null) {
      // Add all configured layers
      for (final layer in widget.layers) {
        await _layerManager!.addLayer(layer);
      }
    }

    // Notify that map is ready — callers re-add their dynamic layers here
    if (_hitdController != null) {
      widget.onMapCreated?.call(_hitdController!);
    }
  }

  Future<void> _onMapClick(Point<double> point, LatLng coordinates) async {
    widget.onTap?.call(coordinates);

    // Query features if callback is set
    if (widget.onFeatureTap != null && _mapLibreController != null) {
      try {
        final features = await _mapLibreController!.queryRenderedFeatures(
          point,
          _layerManager?.queryableLayers ?? [],
          null,
        );

        if (features.isNotEmpty) {
          final properties = features.first['properties'] as Map<String, dynamic>?;
          widget.onFeatureTap?.call(coordinates, properties);
        } else {
          widget.onFeatureTap?.call(coordinates, null);
        }
      } catch (e) {
        widget.onFeatureTap?.call(coordinates, null);
      }
    }
  }

  void _onCameraTrackingChanged(MyLocationTrackingMode mode) {
    // Camera tracking mode changed
  }

  void _onCameraIdle() {
    if (_mapLibreController != null) {
      final position = _mapLibreController!.cameraPosition;
      if (position != null) {
        widget.onCameraIdle?.call(position);
      }
    }
  }
}
