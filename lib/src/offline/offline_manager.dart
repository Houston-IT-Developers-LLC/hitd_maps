import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';

import '../hitd_map_config.dart';

/// Status of an offline region.
enum OfflineRegionStatus {
  /// Not downloaded.
  notDownloaded,
  /// Currently downloading.
  downloading,
  /// Download paused.
  paused,
  /// Fully downloaded and available offline.
  complete,
  /// Download failed.
  failed,
}

/// Represents a downloadable map region.
class OfflineRegion {
  /// Unique identifier for this region.
  final String id;

  /// Human-readable name.
  final String name;

  /// Bounding box: [minLon, minLat, maxLon, maxLat].
  final List<double> bounds;

  /// Minimum zoom level to cache.
  final int minZoom;

  /// Maximum zoom level to cache.
  final int maxZoom;

  /// State code for state-specific layers.
  final String stateCode;

  /// Layers to include in offline package.
  final List<String> layers;

  /// Current download status.
  OfflineRegionStatus status;

  /// Download progress (0.0 to 1.0).
  double progress;

  /// Estimated size in bytes.
  int estimatedBytes;

  /// Actual downloaded size in bytes.
  int downloadedBytes;

  /// Timestamp when download completed.
  DateTime? completedAt;

  /// Error message if failed.
  String? errorMessage;

  OfflineRegion({
    required this.id,
    required this.name,
    required this.bounds,
    this.minZoom = 8,
    this.maxZoom = 14,
    this.stateCode = 'tx',
    this.layers = const ['parcels', 'public-lands'],
    this.status = OfflineRegionStatus.notDownloaded,
    this.progress = 0.0,
    this.estimatedBytes = 0,
    this.downloadedBytes = 0,
    this.completedAt,
    this.errorMessage,
  });

  /// Create from JSON.
  factory OfflineRegion.fromJson(Map<String, dynamic> json) {
    return OfflineRegion(
      id: json['id'] as String,
      name: json['name'] as String,
      bounds: (json['bounds'] as List).cast<double>(),
      minZoom: json['minZoom'] as int? ?? 8,
      maxZoom: json['maxZoom'] as int? ?? 14,
      stateCode: json['stateCode'] as String? ?? 'tx',
      layers: (json['layers'] as List?)?.cast<String>() ?? ['parcels', 'public-lands'],
      status: OfflineRegionStatus.values.byName(json['status'] as String? ?? 'notDownloaded'),
      progress: (json['progress'] as num?)?.toDouble() ?? 0.0,
      estimatedBytes: json['estimatedBytes'] as int? ?? 0,
      downloadedBytes: json['downloadedBytes'] as int? ?? 0,
      completedAt: json['completedAt'] != null
          ? DateTime.parse(json['completedAt'] as String)
          : null,
      errorMessage: json['errorMessage'] as String?,
    );
  }

  /// Convert to JSON.
  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'bounds': bounds,
    'minZoom': minZoom,
    'maxZoom': maxZoom,
    'stateCode': stateCode,
    'layers': layers,
    'status': status.name,
    'progress': progress,
    'estimatedBytes': estimatedBytes,
    'downloadedBytes': downloadedBytes,
    'completedAt': completedAt?.toIso8601String(),
    'errorMessage': errorMessage,
  };

  /// Calculate estimated number of tiles.
  int get estimatedTileCount {
    var count = 0;
    for (var z = minZoom; z <= maxZoom; z++) {
      final tilesX = _getTileRange(bounds[0], bounds[2], z);
      final tilesY = _getTileRange(bounds[1], bounds[3], z);
      count += tilesX * tilesY * layers.length;
    }
    return count;
  }

  int _getTileRange(double min, double max, int zoom) {
    final tileMin = _lonLatToTile(min, zoom);
    final tileMax = _lonLatToTile(max, zoom);
    return (tileMax - tileMin).abs() + 1;
  }

  int _lonLatToTile(double coord, int zoom) {
    return ((coord + 180.0) / 360.0 * (1 << zoom)).floor();
  }

  @override
  String toString() => 'OfflineRegion($id: $name, $status)';
}

/// Progress callback for downloads.
typedef OfflineProgressCallback = void Function(OfflineRegion region, double progress);

/// Manages offline map regions and tile caching.
///
/// ## Usage
///
/// ```dart
/// final offlineManager = OfflineManager();
/// await offlineManager.initialize();
///
/// // Create a region
/// final region = OfflineRegion(
///   id: 'my-hunting-spot',
///   name: 'Hill Country Ranch',
///   bounds: [-99.5, 29.5, -98.5, 30.5],
///   minZoom: 10,
///   maxZoom: 15,
///   stateCode: 'tx',
/// );
///
/// // Download with progress
/// await offlineManager.downloadRegion(
///   region,
///   onProgress: (r, progress) => print('Download: ${(progress * 100).toInt()}%'),
/// );
///
/// // Check if offline
/// if (await offlineManager.isRegionAvailableOffline(region.id)) {
///   print('Ready for offline use!');
/// }
/// ```
class OfflineManager {
  static OfflineManager? _instance;

  /// Get singleton instance.
  static OfflineManager get instance {
    _instance ??= OfflineManager._();
    return _instance!;
  }

  OfflineManager._();

  /// Create a new instance (for testing).
  @visibleForTesting
  factory OfflineManager.forTesting() => OfflineManager._();

  final Dio _dio = Dio();
  Directory? _cacheDir;
  final Map<String, OfflineRegion> _regions = {};
  final Map<String, CancelToken> _activeDownloads = {};

  /// Stream of region status changes.
  final _statusController = StreamController<OfflineRegion>.broadcast();
  Stream<OfflineRegion> get regionStatusChanges => _statusController.stream;

  /// Whether the manager has been initialized.
  bool _initialized = false;
  bool get isInitialized => _initialized;

  /// Initialize the offline manager.
  ///
  /// Must be called before using any offline features.
  Future<void> initialize({String? customCachePath}) async {
    if (_initialized) return;

    // Set up cache directory
    if (customCachePath != null) {
      _cacheDir = Directory(customCachePath);
    } else {
      // Use platform-specific temp/cache directory
      final tempDir = Directory.systemTemp;
      _cacheDir = Directory('${tempDir.path}/hitd_maps_cache');
    }

    await _cacheDir!.create(recursive: true);
    await _loadSavedRegions();
    _initialized = true;

    _log('Offline manager initialized at ${_cacheDir!.path}');
  }

  /// Load previously saved regions from disk.
  Future<void> _loadSavedRegions() async {
    final regionsFile = File('${_cacheDir!.path}/regions.json');
    if (await regionsFile.exists()) {
      try {
        final content = await regionsFile.readAsString();
        final List<dynamic> jsonList = jsonDecode(content);
        for (final json in jsonList) {
          final region = OfflineRegion.fromJson(json as Map<String, dynamic>);
          _regions[region.id] = region;
        }
        _log('Loaded ${_regions.length} saved regions');
      } catch (e) {
        _log('Error loading regions: $e');
      }
    }
  }

  /// Save regions to disk.
  Future<void> _saveRegions() async {
    final regionsFile = File('${_cacheDir!.path}/regions.json');
    final jsonList = _regions.values.map((r) => r.toJson()).toList();
    await regionsFile.writeAsString(jsonEncode(jsonList));
  }

  /// Get all known regions.
  List<OfflineRegion> get regions => _regions.values.toList();

  /// Get a specific region by ID.
  OfflineRegion? getRegion(String id) => _regions[id];

  /// Check if a region is available offline.
  Future<bool> isRegionAvailableOffline(String regionId) async {
    final region = _regions[regionId];
    return region != null && region.status == OfflineRegionStatus.complete;
  }

  /// Create and register a new offline region.
  OfflineRegion createRegion({
    required String id,
    required String name,
    required List<double> bounds,
    int minZoom = 8,
    int maxZoom = 14,
    String stateCode = 'tx',
    List<String> layers = const ['parcels', 'public-lands'],
  }) {
    if (_regions.containsKey(id)) {
      throw StateError('Region with id "$id" already exists');
    }

    final region = OfflineRegion(
      id: id,
      name: name,
      bounds: bounds,
      minZoom: minZoom,
      maxZoom: maxZoom,
      stateCode: stateCode,
      layers: layers,
    );

    // Estimate size (rough: ~50KB per tile for vector tiles)
    region.estimatedBytes = region.estimatedTileCount * 50 * 1024;

    _regions[id] = region;
    _saveRegions();

    return region;
  }

  /// Delete a region and its cached tiles.
  Future<void> deleteRegion(String regionId) async {
    final region = _regions[regionId];
    if (region == null) return;

    // Cancel any active download
    _activeDownloads[regionId]?.cancel();
    _activeDownloads.remove(regionId);

    // Delete cached files
    final regionDir = Directory('${_cacheDir!.path}/regions/$regionId');
    if (await regionDir.exists()) {
      await regionDir.delete(recursive: true);
    }

    _regions.remove(regionId);
    await _saveRegions();

    _log('Deleted region: $regionId');
  }

  /// Download a region for offline use.
  ///
  /// [region] - The region to download
  /// [onProgress] - Optional progress callback
  /// [retryCount] - Number of retries for failed tiles
  Future<void> downloadRegion(
    OfflineRegion region, {
    OfflineProgressCallback? onProgress,
    int retryCount = 3,
  }) async {
    _ensureInitialized();

    if (!_regions.containsKey(region.id)) {
      _regions[region.id] = region;
    }

    region.status = OfflineRegionStatus.downloading;
    region.progress = 0.0;
    region.downloadedBytes = 0;
    region.errorMessage = null;
    _notifyStatus(region);

    final cancelToken = CancelToken();
    _activeDownloads[region.id] = cancelToken;

    try {
      final regionDir = Directory('${_cacheDir!.path}/regions/${region.id}');
      await regionDir.create(recursive: true);

      final config = HitdMapConfig.instance;
      final totalTiles = region.estimatedTileCount;
      var downloadedCount = 0;

      // Download tiles for each layer
      for (final layer in region.layers) {
        final layerDir = Directory('${regionDir.path}/$layer');
        await layerDir.create(recursive: true);

        for (var z = region.minZoom; z <= region.maxZoom; z++) {
          if (cancelToken.isCancelled) {
            region.status = OfflineRegionStatus.paused;
            _notifyStatus(region);
            return;
          }

          final tiles = _getTilesForZoom(region.bounds, z);

          for (final tile in tiles) {
            if (cancelToken.isCancelled) {
              region.status = OfflineRegionStatus.paused;
              _notifyStatus(region);
              return;
            }

            final tileFile = File('${layerDir.path}/${tile.z}_${tile.x}_${tile.y}.pbf');

            // Skip if already downloaded
            if (await tileFile.exists()) {
              downloadedCount++;
              continue;
            }

            // Download tile with retries
            var success = false;
            for (var attempt = 0; attempt < retryCount && !success; attempt++) {
              try {
                final url = _getTileUrl(config, layer, region.stateCode, tile);
                final response = await _dio.get<List<int>>(
                  url,
                  options: Options(responseType: ResponseType.bytes),
                  cancelToken: cancelToken,
                );

                if (response.data != null) {
                  await tileFile.writeAsBytes(response.data!);
                  region.downloadedBytes += response.data!.length;
                  success = true;
                }
              } catch (e) {
                if (e is DioException && e.type == DioExceptionType.cancel) {
                  rethrow;
                }
                if (attempt == retryCount - 1) {
                  _log('Failed to download tile after $retryCount attempts: $tile');
                }
              }
            }

            downloadedCount++;
            region.progress = downloadedCount / totalTiles;
            onProgress?.call(region, region.progress);
          }
        }
      }

      // Download basemap style
      await _downloadBasemapStyle(regionDir, cancelToken);

      region.status = OfflineRegionStatus.complete;
      region.completedAt = DateTime.now();
      _log('Region download complete: ${region.id}');
    } on DioException catch (e) {
      if (e.type == DioExceptionType.cancel) {
        region.status = OfflineRegionStatus.paused;
      } else {
        region.status = OfflineRegionStatus.failed;
        region.errorMessage = e.message;
      }
    } catch (e) {
      region.status = OfflineRegionStatus.failed;
      region.errorMessage = e.toString();
      _log('Region download failed: $e');
    } finally {
      _activeDownloads.remove(region.id);
      await _saveRegions();
      _notifyStatus(region);
    }
  }

  /// Pause an active download.
  void pauseDownload(String regionId) {
    _activeDownloads[regionId]?.cancel();
  }

  /// Resume a paused download.
  Future<void> resumeDownload(
    String regionId, {
    OfflineProgressCallback? onProgress,
  }) async {
    final region = _regions[regionId];
    if (region == null) {
      throw StateError('Region not found: $regionId');
    }
    if (region.status != OfflineRegionStatus.paused) {
      throw StateError('Region is not paused: ${region.status}');
    }

    await downloadRegion(region, onProgress: onProgress);
  }

  /// Get a cached tile if available.
  Future<Uint8List?> getCachedTile(
    String regionId,
    String layer,
    int z,
    int x,
    int y,
  ) async {
    final tileFile = File(
      '${_cacheDir!.path}/regions/$regionId/$layer/${z}_${x}_${y}.pbf',
    );

    if (await tileFile.exists()) {
      return await tileFile.readAsBytes();
    }
    return null;
  }

  /// Check if a specific tile is cached.
  Future<bool> isTileCached(
    String regionId,
    String layer,
    int z,
    int x,
    int y,
  ) async {
    final tileFile = File(
      '${_cacheDir!.path}/regions/$regionId/$layer/${z}_${x}_${y}.pbf',
    );
    return await tileFile.exists();
  }

  /// Get the path to the offline basemap style.
  String? getOfflineStylePath(String regionId) {
    final stylePath = '${_cacheDir!.path}/regions/$regionId/style.json';
    if (File(stylePath).existsSync()) {
      return stylePath;
    }
    return null;
  }

  /// Calculate total cache size in bytes.
  Future<int> getCacheSize() async {
    _ensureInitialized();

    var totalSize = 0;
    await for (final entity in _cacheDir!.list(recursive: true)) {
      if (entity is File) {
        totalSize += await entity.length();
      }
    }
    return totalSize;
  }

  /// Clear all cached data.
  Future<void> clearCache() async {
    _ensureInitialized();

    // Cancel all downloads
    for (final token in _activeDownloads.values) {
      token.cancel();
    }
    _activeDownloads.clear();

    // Delete cache directory
    if (await _cacheDir!.exists()) {
      await _cacheDir!.delete(recursive: true);
      await _cacheDir!.create(recursive: true);
    }

    _regions.clear();
    _log('Cache cleared');
  }

  /// Get cache directory path.
  String? get cachePath => _cacheDir?.path;

  // ============================================================
  // PRIVATE HELPERS
  // ============================================================

  void _ensureInitialized() {
    if (!_initialized) {
      throw StateError(
        'OfflineManager not initialized. Call initialize() first.',
      );
    }
  }

  void _notifyStatus(OfflineRegion region) {
    if (!_statusController.isClosed) {
      _statusController.add(region);
    }
  }

  Future<void> _downloadBasemapStyle(Directory regionDir, CancelToken cancelToken) async {
    try {
      final config = HitdMapConfig.instance;
      final styleUrl = config.basemapStyleUrl;

      // If it's a local asset, we don't need to download
      if (styleUrl.startsWith('assets/')) {
        return;
      }

      final response = await _dio.get<String>(
        styleUrl,
        cancelToken: cancelToken,
      );

      if (response.data != null) {
        final styleFile = File('${regionDir.path}/style.json');
        await styleFile.writeAsString(response.data!);
      }
    } catch (e) {
      _log('Failed to download basemap style: $e');
    }
  }

  List<TileCoord> _getTilesForZoom(List<double> bounds, int zoom) {
    final tiles = <TileCoord>[];

    final minX = _lonToTileX(bounds[0], zoom);
    final maxX = _lonToTileX(bounds[2], zoom);
    final minY = _latToTileY(bounds[3], zoom); // Note: Y is inverted
    final maxY = _latToTileY(bounds[1], zoom);

    for (var x = minX; x <= maxX; x++) {
      for (var y = minY; y <= maxY; y++) {
        tiles.add(TileCoord(z: zoom, x: x, y: y));
      }
    }

    return tiles;
  }

  int _lonToTileX(double lon, int zoom) {
    return ((lon + 180.0) / 360.0 * (1 << zoom)).floor().clamp(0, (1 << zoom) - 1);
  }

  int _latToTileY(double lat, int zoom) {
    final latRad = lat * 3.141592653589793 / 180.0;
    final n = 1 << zoom;
    return ((1.0 - (latRad.tan() + 1.0 / latRad.cos()).log() / 3.141592653589793) / 2.0 * n)
        .floor()
        .clamp(0, n - 1);
  }

  String _getTileUrl(HitdMapConfig config, String layer, String stateCode, TileCoord tile) {
    // For PMTiles, construct the tile URL
    // Format: {baseUrl}/{layer}_{state}/{z}/{x}/{y}.pbf
    return '${config.pmtilesBaseUrl}/${layer}_$stateCode/${tile.z}/${tile.x}/${tile.y}.pbf';
  }

  void _log(String message) {
    if (HitdMapConfig.isInitialized && HitdMapConfig.instance.debugMode) {
      // ignore: avoid_print
      print('[OfflineManager] $message');
    }
  }

  /// Dispose resources.
  void dispose() {
    for (final token in _activeDownloads.values) {
      token.cancel();
    }
    _activeDownloads.clear();
    _statusController.close();
  }
}

/// Represents a tile coordinate.
class TileCoord {
  final int z;
  final int x;
  final int y;

  const TileCoord({required this.z, required this.x, required this.y});

  @override
  String toString() => 'TileCoord($z/$x/$y)';

  @override
  bool operator ==(Object other) =>
      other is TileCoord && z == other.z && x == other.x && y == other.y;

  @override
  int get hashCode => Object.hash(z, x, y);
}
