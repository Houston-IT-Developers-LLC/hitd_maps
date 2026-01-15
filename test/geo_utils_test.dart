import 'package:flutter_test/flutter_test.dart';
import 'package:hitd_maps/src/utils/geo_utils.dart';

void main() {
  group('GeoUtils', () {
    group('calculateDistance', () {
      test('calculates distance between two points', () {
        // Austin to Houston: approximately 260 km
        const austinLat = 30.2672;
        const austinLng = -97.7431;
        const houstonLat = 29.7604;
        const houstonLng = -95.3698;

        final distance = GeoUtils.calculateDistance(
          austinLat,
          austinLng,
          houstonLat,
          houstonLng,
        );

        // Should be approximately 260 km (within 10%)
        expect(distance, greaterThan(230));
        expect(distance, lessThan(290));
      });

      test('returns 0 for same point', () {
        final distance = GeoUtils.calculateDistance(
          30.0,
          -97.0,
          30.0,
          -97.0,
        );

        expect(distance, equals(0));
      });

      test('handles antipodal points', () {
        // Points on opposite sides of Earth
        final distance = GeoUtils.calculateDistance(
          0,
          0,
          0,
          180,
        );

        // Half Earth circumference: ~20,000 km
        expect(distance, greaterThan(19000));
        expect(distance, lessThan(21000));
      });
    });

    group('calculateBearing', () {
      test('calculates bearing north', () {
        final bearing = GeoUtils.calculateBearing(
          30.0, -97.0, // From
          31.0, -97.0, // To (due north)
        );

        // Should be approximately 0 degrees (north)
        expect(bearing, closeTo(0, 5));
      });

      test('calculates bearing east', () {
        final bearing = GeoUtils.calculateBearing(
          30.0, -97.0, // From
          30.0, -96.0, // To (due east)
        );

        // Should be approximately 90 degrees (east)
        expect(bearing, closeTo(90, 5));
      });

      test('calculates bearing south', () {
        final bearing = GeoUtils.calculateBearing(
          30.0, -97.0, // From
          29.0, -97.0, // To (due south)
        );

        // Should be approximately 180 degrees (south)
        expect(bearing, closeTo(180, 5));
      });

      test('calculates bearing west', () {
        final bearing = GeoUtils.calculateBearing(
          30.0, -97.0, // From
          30.0, -98.0, // To (due west)
        );

        // Should be approximately 270 degrees (west)
        expect(bearing, closeTo(270, 5));
      });
    });

    group('degreesToCardinal', () {
      test('converts 0 to N', () {
        expect(GeoUtils.degreesToCardinal(0), equals('N'));
      });

      test('converts 45 to NE', () {
        expect(GeoUtils.degreesToCardinal(45), equals('NE'));
      });

      test('converts 90 to E', () {
        expect(GeoUtils.degreesToCardinal(90), equals('E'));
      });

      test('converts 135 to SE', () {
        expect(GeoUtils.degreesToCardinal(135), equals('SE'));
      });

      test('converts 180 to S', () {
        expect(GeoUtils.degreesToCardinal(180), equals('S'));
      });

      test('converts 225 to SW', () {
        expect(GeoUtils.degreesToCardinal(225), equals('SW'));
      });

      test('converts 270 to W', () {
        expect(GeoUtils.degreesToCardinal(270), equals('W'));
      });

      test('converts 315 to NW', () {
        expect(GeoUtils.degreesToCardinal(315), equals('NW'));
      });

      test('wraps 360 to N', () {
        expect(GeoUtils.degreesToCardinal(360), equals('N'));
      });

      test('handles negative degrees', () {
        expect(GeoUtils.degreesToCardinal(-90), equals('W'));
      });
    });

    group('cardinalToDegrees', () {
      test('converts N to 0', () {
        expect(GeoUtils.cardinalToDegrees('N'), equals(0));
      });

      test('converts E to 90', () {
        expect(GeoUtils.cardinalToDegrees('E'), equals(90));
      });

      test('converts S to 180', () {
        expect(GeoUtils.cardinalToDegrees('S'), equals(180));
      });

      test('converts W to 270', () {
        expect(GeoUtils.cardinalToDegrees('W'), equals(270));
      });

      test('handles lowercase', () {
        expect(GeoUtils.cardinalToDegrees('ne'), equals(45));
      });
    });

    group('isPointInPolygon', () {
      test('detects point inside polygon', () {
        final polygon = [
          [0.0, 0.0],
          [0.0, 10.0],
          [10.0, 10.0],
          [10.0, 0.0],
        ];

        final isInside = GeoUtils.isPointInPolygon(5.0, 5.0, polygon);

        expect(isInside, isTrue);
      });

      test('detects point outside polygon', () {
        final polygon = [
          [0.0, 0.0],
          [0.0, 10.0],
          [10.0, 10.0],
          [10.0, 0.0],
        ];

        final isInside = GeoUtils.isPointInPolygon(15.0, 15.0, polygon);

        expect(isInside, isFalse);
      });

      test('handles point on edge', () {
        final polygon = [
          [0.0, 0.0],
          [0.0, 10.0],
          [10.0, 10.0],
          [10.0, 0.0],
        ];

        // Point on edge might be considered inside or outside
        // depending on implementation - just verify it doesn't crash
        expect(
          () => GeoUtils.isPointInPolygon(0.0, 5.0, polygon),
          returnsNormally,
        );
      });

      test('handles complex polygon', () {
        // L-shaped polygon
        final polygon = [
          [0.0, 0.0],
          [0.0, 10.0],
          [5.0, 10.0],
          [5.0, 5.0],
          [10.0, 5.0],
          [10.0, 0.0],
        ];

        // Point in the "notch" of the L
        final isInsideNotch = GeoUtils.isPointInPolygon(7.0, 7.0, polygon);
        expect(isInsideNotch, isFalse);

        // Point in the main body
        final isInsideBody = GeoUtils.isPointInPolygon(2.0, 2.0, polygon);
        expect(isInsideBody, isTrue);
      });
    });

    group('destinationPoint', () {
      test('calculates point due north', () {
        final dest = GeoUtils.destinationPoint(
          30.0,
          -97.0,
          0, // North
          111, // ~1 degree of latitude in km
        );

        // Should be approximately 1 degree north
        expect(dest['lat'], closeTo(31.0, 0.1));
        expect(dest['lng'], closeTo(-97.0, 0.1));
      });

      test('calculates point due east', () {
        final dest = GeoUtils.destinationPoint(
          0.0, // Equator for simpler calculation
          0.0,
          90, // East
          111, // ~1 degree of longitude at equator
        );

        expect(dest['lat'], closeTo(0.0, 0.1));
        expect(dest['lng'], closeTo(1.0, 0.1));
      });
    });

    group('metersToMiles', () {
      test('converts meters to miles', () {
        // 1609.34 meters = 1 mile
        final miles = GeoUtils.metersToMiles(1609.34);
        expect(miles, closeTo(1.0, 0.01));
      });

      test('converts 0 to 0', () {
        expect(GeoUtils.metersToMiles(0), equals(0));
      });
    });

    group('milesToMeters', () {
      test('converts miles to meters', () {
        final meters = GeoUtils.milesToMeters(1.0);
        expect(meters, closeTo(1609.34, 1));
      });
    });

    group('kmToMiles', () {
      test('converts kilometers to miles', () {
        final miles = GeoUtils.kmToMiles(1.60934);
        expect(miles, closeTo(1.0, 0.01));
      });
    });

    group('milesToKm', () {
      test('converts miles to kilometers', () {
        final km = GeoUtils.milesToKm(1.0);
        expect(km, closeTo(1.60934, 0.01));
      });
    });

    group('formatDistance', () {
      test('formats short distance in feet', () {
        final formatted = GeoUtils.formatDistance(0.1); // 100 meters
        expect(formatted, contains('ft'));
      });

      test('formats longer distance in miles', () {
        final formatted = GeoUtils.formatDistance(5.0); // 5 km
        expect(formatted, contains('mi'));
      });
    });
  });
}
