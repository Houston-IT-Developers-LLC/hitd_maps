import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:hitd_maps/src/offline/offline_manager.dart';
import 'package:hitd_maps/src/hitd_map_config.dart';

void main() {
  late OfflineManager offlineManager;
  late Directory tempDir;

  setUp(() async {
    // Create a fresh instance for each test
    offlineManager = OfflineManager.forTesting();

    // Create a temp directory for cache
    tempDir = await Directory.systemTemp.createTemp('hitd_maps_test_');

    // Initialize config
    HitdMapConfig.initialize(
      pmtilesBaseUrl: 'https://test.example.com/tiles',
      basemapStyleUrl: 'https://test.example.com/style.json',
      debugMode: false,
    );

    await offlineManager.initialize(customCachePath: tempDir.path);
  });

  tearDown(() async {
    HitdMapConfig.resetForTesting();
    offlineManager.dispose();

    // Clean up temp directory
    if (await tempDir.exists()) {
      await tempDir.delete(recursive: true);
    }
  });

  group('OfflineRegion', () {
    test('creates with required parameters', () {
      final region = OfflineRegion(
        id: 'test-region',
        name: 'Test Region',
        bounds: [-100.0, 30.0, -99.0, 31.0],
      );

      expect(region.id, 'test-region');
      expect(region.name, 'Test Region');
      expect(region.bounds, [-100.0, 30.0, -99.0, 31.0]);
      expect(region.minZoom, 8);
      expect(region.maxZoom, 14);
      expect(region.stateCode, 'tx');
      expect(region.status, OfflineRegionStatus.notDownloaded);
    });

    test('serializes to and from JSON', () {
      final region = OfflineRegion(
        id: 'json-test',
        name: 'JSON Test',
        bounds: [-100.0, 30.0, -99.0, 31.0],
        minZoom: 10,
        maxZoom: 16,
        stateCode: 'ca',
        layers: ['parcels'],
        status: OfflineRegionStatus.complete,
        progress: 1.0,
        downloadedBytes: 1000000,
        completedAt: DateTime(2024, 1, 15, 12, 0),
      );

      final json = region.toJson();
      final restored = OfflineRegion.fromJson(json);

      expect(restored.id, region.id);
      expect(restored.name, region.name);
      expect(restored.bounds, region.bounds);
      expect(restored.minZoom, region.minZoom);
      expect(restored.maxZoom, region.maxZoom);
      expect(restored.stateCode, region.stateCode);
      expect(restored.layers, region.layers);
      expect(restored.status, region.status);
      expect(restored.progress, region.progress);
      expect(restored.downloadedBytes, region.downloadedBytes);
      expect(restored.completedAt, region.completedAt);
    });

    test('estimates tile count based on bounds and zoom', () {
      final region = OfflineRegion(
        id: 'tile-count-test',
        name: 'Tile Count Test',
        bounds: [-100.0, 30.0, -99.0, 31.0], // ~1 degree square
        minZoom: 10,
        maxZoom: 10, // Single zoom level for predictable count
        layers: ['parcels'],
      );

      final count = region.estimatedTileCount;

      // At zoom 10, a 1x1 degree area should have a reasonable number of tiles
      expect(count, greaterThan(0));
      expect(count, lessThan(1000)); // Sanity check
    });
  });

  group('OfflineManager', () {
    test('initializes correctly', () {
      expect(offlineManager.isInitialized, true);
      expect(offlineManager.cachePath, tempDir.path);
    });

    test('creates and retrieves regions', () {
      final region = offlineManager.createRegion(
        id: 'my-region',
        name: 'My Hunting Spot',
        bounds: [-99.5, 29.5, -98.5, 30.5],
        stateCode: 'tx',
      );

      expect(region.id, 'my-region');
      expect(offlineManager.regions.length, 1);
      expect(offlineManager.getRegion('my-region'), isNotNull);
      expect(offlineManager.getRegion('nonexistent'), isNull);
    });

    test('throws when creating duplicate region ID', () {
      offlineManager.createRegion(
        id: 'duplicate',
        name: 'First',
        bounds: [-100.0, 30.0, -99.0, 31.0],
      );

      expect(
        () => offlineManager.createRegion(
          id: 'duplicate',
          name: 'Second',
          bounds: [-100.0, 30.0, -99.0, 31.0],
        ),
        throwsStateError,
      );
    });

    test('deletes regions', () async {
      offlineManager.createRegion(
        id: 'to-delete',
        name: 'Delete Me',
        bounds: [-100.0, 30.0, -99.0, 31.0],
      );

      expect(offlineManager.regions.length, 1);

      await offlineManager.deleteRegion('to-delete');

      expect(offlineManager.regions.length, 0);
      expect(offlineManager.getRegion('to-delete'), isNull);
    });

    test('reports offline availability correctly', () async {
      final region = offlineManager.createRegion(
        id: 'availability-test',
        name: 'Test',
        bounds: [-100.0, 30.0, -99.0, 31.0],
      );

      // Not downloaded yet
      expect(await offlineManager.isRegionAvailableOffline('availability-test'), false);

      // Simulate completion
      region.status = OfflineRegionStatus.complete;
      expect(await offlineManager.isRegionAvailableOffline('availability-test'), true);

      // Downloading doesn't count as available
      region.status = OfflineRegionStatus.downloading;
      expect(await offlineManager.isRegionAvailableOffline('availability-test'), false);
    });

    test('clears cache correctly', () async {
      offlineManager.createRegion(
        id: 'region1',
        name: 'Region 1',
        bounds: [-100.0, 30.0, -99.0, 31.0],
      );
      offlineManager.createRegion(
        id: 'region2',
        name: 'Region 2',
        bounds: [-100.0, 30.0, -99.0, 31.0],
      );

      expect(offlineManager.regions.length, 2);

      await offlineManager.clearCache();

      expect(offlineManager.regions.length, 0);
    });

    test('returns cache size', () async {
      final size = await offlineManager.getCacheSize();
      expect(size, greaterThanOrEqualTo(0));
    });
  });

  group('TileCoord', () {
    test('equality and hashCode work correctly', () {
      const coord1 = TileCoord(z: 10, x: 100, y: 200);
      const coord2 = TileCoord(z: 10, x: 100, y: 200);
      const coord3 = TileCoord(z: 10, x: 100, y: 201);

      expect(coord1, equals(coord2));
      expect(coord1.hashCode, coord2.hashCode);
      expect(coord1, isNot(equals(coord3)));
    });

    test('toString returns readable format', () {
      const coord = TileCoord(z: 10, x: 100, y: 200);
      expect(coord.toString(), 'TileCoord(10/100/200)');
    });
  });

  group('OfflineRegionStatus', () {
    test('all statuses are defined', () {
      expect(OfflineRegionStatus.values, containsAll([
        OfflineRegionStatus.notDownloaded,
        OfflineRegionStatus.downloading,
        OfflineRegionStatus.paused,
        OfflineRegionStatus.complete,
        OfflineRegionStatus.failed,
      ]));
    });
  });
}
