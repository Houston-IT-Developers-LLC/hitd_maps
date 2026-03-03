import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:maplibre_gl/maplibre_gl.dart';

import '../hitd_map_config.dart';
import 'map_layer.dart';

/// Manages map layers for [HitdMap].
///
/// Handles adding, removing, and updating vector tile layers from PMTiles sources.
class LayerManager {
  final MapLibreMapController _controller;

  /// Currently active layers by ID.
  final Map<String, HitdMapLayer> _layers = {};

  /// Layer visibility state.
  final Map<String, bool> _visibility = {};

  /// Current state code for state-specific layers.
  String _currentState = 'tx';

  LayerManager(this._controller);

  /// Get list of active layer IDs.
  List<String> get activeLayers => _layers.keys.toList();

  /// Get list of queryable layer IDs (for tap handling).
  List<String> get queryableLayers =>
      _layers.entries
          .where((e) => e.value.queryable && (_visibility[e.key] ?? true))
          .map((e) => '${e.key}-fill')
          .toList();

  /// Check if a layer is visible.
  bool isLayerVisible(String layerId) => _visibility[layerId] ?? true;

  /// Add a layer to the map.
  Future<void> addLayer(HitdMapLayer layer) async {
    if (_layers.containsKey(layer.id)) {
      _log('Layer ${layer.id} already exists');
      return;
    }

    try {
      // Add the source
      await _addSource(layer);

      // Add fill layer (if layer has fill color)
      if (layer.fillColor != null) {
        await _addFillLayer(layer);
      }

      // Add line/outline layer (if layer has line color)
      if (layer.lineColor != null) {
        await _addLineLayer(layer);
      }

      _layers[layer.id] = layer;
      _visibility[layer.id] = layer.visible;

      _log('Added layer: ${layer.id}');
    } catch (e) {
      _log('Error adding layer ${layer.id}: $e', isError: true);
    }
  }

  /// Remove a layer from the map.
  Future<void> removeLayer(String layerId) async {
    if (!_layers.containsKey(layerId)) {
      _log('Layer $layerId not found');
      return;
    }

    try {
      // Remove layers
      await _controller.removeLayer('$layerId-fill');
      await _controller.removeLayer('$layerId-outline');

      // Remove source
      final layer = _layers[layerId]!;
      await _controller.removeSource(layer.sourceId);

      _layers.remove(layerId);
      _visibility.remove(layerId);

      _log('Removed layer: $layerId');
    } catch (e) {
      _log('Error removing layer $layerId: $e', isError: true);
    }
  }

  /// Set visibility of a layer.
  Future<void> setLayerVisibility(String layerId, bool visible) async {
    if (!_layers.containsKey(layerId)) return;

    try {
      await _controller.setLayerVisibility('$layerId-fill', visible);
      await _controller.setLayerVisibility('$layerId-outline', visible);
      _visibility[layerId] = visible;

      _log('Set ${visible ? 'visible' : 'hidden'}: $layerId');
    } catch (e) {
      _log('Error setting visibility for $layerId: $e', isError: true);
    }
  }

  /// Toggle visibility of a layer.
  Future<void> toggleLayerVisibility(String layerId) async {
    final currentVisibility = _visibility[layerId] ?? true;
    await setLayerVisibility(layerId, !currentVisibility);
  }

  /// Switch to a different state's data.
  ///
  /// Reloads all state-specific layers with data for the new state.
  Future<void> switchState(String stateCode) async {
    if (stateCode == _currentState) return;

    _currentState = stateCode.toLowerCase();

    // Find all state-specific layers and reload them
    final stateSpecificLayers = _layers.values
        .where((l) => l.isStateSpecific)
        .toList();

    for (final layer in stateSpecificLayers) {
      await _reloadLayer(layer);
    }

    _log('Switched to state: $_currentState');
  }

  /// Reload a layer with current state data.
  Future<void> _reloadLayer(HitdMapLayer layer) async {
    final wasVisible = _visibility[layer.id] ?? true;

    // Remove existing — wrap individually so a failed remove doesn't
    // prevent the new source from being added (e.g. old source was 404)
    try { await _controller.removeLayer('${layer.id}-fill'); } catch (_) {}
    try { await _controller.removeLayer('${layer.id}-outline'); } catch (_) {}
    try { await _controller.removeSource(layer.sourceId); } catch (_) {}

    try {
      // Re-add with new state
      await _addSource(layer);

      if (layer.fillColor != null) {
        await _addFillLayer(layer);
      }
      if (layer.lineColor != null) {
        await _addLineLayer(layer);
      }

      // Restore visibility
      await setLayerVisibility(layer.id, wasVisible);

      _log('Reloaded layer: ${layer.id}');
    } catch (e) {
      _log('Error reloading layer ${layer.id}: $e', isError: true);
    }
  }

  /// Add a PMTiles source for a layer.
  Future<void> _addSource(HitdMapLayer layer) async {
    final url = layer.getPmtilesUrl(stateCode: _currentState);
    _log('Adding source ${layer.sourceId}: $url (state=$_currentState)');

    await _controller.addSource(
      layer.sourceId,
      VectorSourceProperties(
        url: url,
        minzoom: layer.minZoom,
        maxzoom: layer.maxZoom,
      ),
    );
  }

  /// Add a fill layer.
  Future<void> _addFillLayer(HitdMapLayer layer) async {
    final fillColor = _colorToHex(layer.fillColor!);

    await _controller.addLayer(
      layer.sourceId,
      '${layer.id}-fill',
      FillLayerProperties(
        fillColor: [
          'case',
          ['boolean', ['feature-state', 'selected'], false],
          '#FF6B6B', // Selected color
          fillColor,
        ],
        fillOpacity: [
          'interpolate',
          ['linear'],
          ['zoom'],
          layer.minZoom, layer.fillOpacity * 0.5,
          layer.minZoom + 4, layer.fillOpacity,
          layer.maxZoom, layer.fillOpacity,
        ],
      ),
      sourceLayer: layer.sourceLayer,
      minzoom: layer.minZoom,
    );
  }

  /// Add a line/outline layer.
  Future<void> _addLineLayer(HitdMapLayer layer) async {
    final lineColor = _colorToHex(layer.lineColor!);

    await _controller.addLayer(
      layer.sourceId,
      '${layer.id}-outline',
      LineLayerProperties(
        lineColor: lineColor,
        lineWidth: [
          'interpolate',
          ['linear'],
          ['zoom'],
          layer.minZoom, layer.lineWidth * 0.5,
          layer.minZoom + 4, layer.lineWidth,
          layer.maxZoom, layer.lineWidth * 1.5,
        ],
        lineOpacity: [
          'interpolate',
          ['linear'],
          ['zoom'],
          layer.minZoom, layer.lineOpacity * 0.5,
          layer.minZoom + 4, layer.lineOpacity,
        ],
      ),
      sourceLayer: layer.sourceLayer,
      minzoom: layer.minZoom,
    );
  }

  /// Convert Color to hex string.
  String _colorToHex(Color color) {
    return '#${color.value.toRadixString(16).substring(2).toUpperCase()}';
  }

  /// Log message if debug mode is enabled.
  void _log(String message, {bool isError = false}) {
    if (HitdMapConfig.isInitialized && HitdMapConfig.instance.debugMode) {
      if (isError) {
        debugPrint('[LayerManager] ERROR: $message');
      } else if (kDebugMode) {
        debugPrint('[LayerManager] $message');
      }
    }
  }
}
