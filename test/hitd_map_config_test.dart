import 'package:flutter_test/flutter_test.dart';
import 'package:hitd_maps/src/hitd_map_config.dart';

void main() {
  group('HitdMapConfig', () {
    tearDown(() {
      // Reset singleton for next test
      // ignore: invalid_use_of_visible_for_testing_member
      HitdMapConfig.resetForTesting();
    });

    group('initialize', () {
      test('initializes with required parameters', () {
        HitdMapConfig.initialize(
          pmtilesBaseUrl: 'https://example.com/tiles',
          basemapStyleUrl: 'assets/map/style.json',
        );

        expect(HitdMapConfig.isInitialized, isTrue);
        expect(HitdMapConfig.instance.pmtilesBaseUrl, equals('https://example.com/tiles'));
        expect(HitdMapConfig.instance.basemapStyleUrl, equals('assets/map/style.json'));
      });

      test('uses default values when not specified', () {
        HitdMapConfig.initialize(
          pmtilesBaseUrl: 'https://example.com/tiles',
          basemapStyleUrl: 'assets/map/style.json',
        );

        expect(HitdMapConfig.instance.usePmtilesProtocol, isTrue);
        expect(HitdMapConfig.instance.defaultZoom, equals(14.0));
        expect(HitdMapConfig.instance.minZoom, equals(4.0));
        expect(HitdMapConfig.instance.maxZoom, equals(18.0));
        expect(HitdMapConfig.instance.debugMode, isFalse);
        expect(HitdMapConfig.instance.cacheDurationMinutes, equals(30));
      });

      test('accepts custom values', () {
        HitdMapConfig.initialize(
          pmtilesBaseUrl: 'https://example.com/tiles',
          basemapStyleUrl: 'assets/map/style.json',
          usePmtilesProtocol: false,
          defaultZoom: 10.0,
          minZoom: 2.0,
          maxZoom: 20.0,
          debugMode: true,
          cacheDurationMinutes: 60,
        );

        expect(HitdMapConfig.instance.usePmtilesProtocol, isFalse);
        expect(HitdMapConfig.instance.defaultZoom, equals(10.0));
        expect(HitdMapConfig.instance.minZoom, equals(2.0));
        expect(HitdMapConfig.instance.maxZoom, equals(20.0));
        expect(HitdMapConfig.instance.debugMode, isTrue);
        expect(HitdMapConfig.instance.cacheDurationMinutes, equals(60));
      });
    });

    group('isInitialized', () {
      test('returns false before initialization', () {
        expect(HitdMapConfig.isInitialized, isFalse);
      });

      test('returns true after initialization', () {
        HitdMapConfig.initialize(
          pmtilesBaseUrl: 'https://example.com/tiles',
          basemapStyleUrl: 'assets/map/style.json',
        );

        expect(HitdMapConfig.isInitialized, isTrue);
      });
    });

    group('instance', () {
      test('throws StateError when not initialized', () {
        expect(
          () => HitdMapConfig.instance,
          throwsA(isA<StateError>()),
        );
      });

      test('returns instance when initialized', () {
        HitdMapConfig.initialize(
          pmtilesBaseUrl: 'https://example.com/tiles',
          basemapStyleUrl: 'assets/map/style.json',
        );

        expect(HitdMapConfig.instance, isNotNull);
      });
    });

    group('getPmtilesUrl', () {
      test('generates URL with pmtiles protocol', () {
        HitdMapConfig.initialize(
          pmtilesBaseUrl: 'https://example.com/tiles',
          basemapStyleUrl: 'assets/map/style.json',
          usePmtilesProtocol: true,
        );

        final url = HitdMapConfig.instance.getPmtilesUrl('parcels');

        expect(url, equals('pmtiles://https://example.com/tiles/parcels.pmtiles'));
      });

      test('generates URL without pmtiles protocol', () {
        HitdMapConfig.initialize(
          pmtilesBaseUrl: 'https://example.com/tiles',
          basemapStyleUrl: 'assets/map/style.json',
          usePmtilesProtocol: false,
        );

        final url = HitdMapConfig.instance.getPmtilesUrl('parcels');

        expect(url, equals('https://example.com/tiles/parcels.pmtiles'));
      });

      test('includes state code when provided', () {
        HitdMapConfig.initialize(
          pmtilesBaseUrl: 'https://example.com/tiles',
          basemapStyleUrl: 'assets/map/style.json',
        );

        final url = HitdMapConfig.instance.getPmtilesUrl('parcels', stateCode: 'tx');

        expect(url, contains('parcels_tx.pmtiles'));
      });

      test('lowercases state code', () {
        HitdMapConfig.initialize(
          pmtilesBaseUrl: 'https://example.com/tiles',
          basemapStyleUrl: 'assets/map/style.json',
        );

        final url = HitdMapConfig.instance.getPmtilesUrl('parcels', stateCode: 'TX');

        expect(url, contains('parcels_tx.pmtiles'));
      });
    });
  });

  group('HitdMapPresets', () {
    tearDown(() {
      // ignore: invalid_use_of_visible_for_testing_member
      HitdMapConfig.resetForTesting();
    });

    test('useGSpotOutdoors sets correct values', () {
      HitdMapPresets.useGSpotOutdoors();

      expect(HitdMapConfig.isInitialized, isTrue);
      expect(
        HitdMapConfig.instance.pmtilesBaseUrl,
        contains('r2.dev'),
      );
      expect(HitdMapConfig.instance.debugMode, isFalse);
    });

    test('useGSpotOutdoors respects debug flag', () {
      HitdMapPresets.useGSpotOutdoors(debugMode: true);

      expect(HitdMapConfig.instance.debugMode, isTrue);
    });

    test('useLocalDevelopment sets localhost URL', () {
      HitdMapPresets.useLocalDevelopment();

      expect(HitdMapConfig.instance.pmtilesBaseUrl, contains('localhost'));
      expect(HitdMapConfig.instance.debugMode, isTrue);
    });
  });
}

// Extension to reset singleton for testing
extension HitdMapConfigTesting on HitdMapConfig {
  static void resetForTesting() {
    // This requires adding a reset method to HitdMapConfig
  }
}
