import 'package:flutter_test/flutter_test.dart';
import 'package:hitd_maps/src/services/solunar_service.dart';

void main() {
  late SolunarService solunar;

  setUp(() {
    solunar = SolunarService();
  });

  group('SolunarService', () {
    group('getMoonPhase', () {
      test('returns valid moon phase for any date', () {
        final phase = solunar.getMoonPhase(DateTime(2026, 1, 13));

        expect(phase, isNotNull);
        expect(phase.illumination, greaterThanOrEqualTo(0));
        expect(phase.illumination, lessThanOrEqualTo(100));
        expect(phase.age, greaterThanOrEqualTo(0));
        expect(phase.age, lessThan(29.54)); // Less than synodic month
        expect(phase.angle, greaterThanOrEqualTo(0));
        expect(phase.angle, lessThan(360));
      });

      test('full moon has high illumination', () {
        // Find a known full moon date
        // Full moon was around January 13, 2025
        final phase = solunar.getMoonPhase(DateTime(2025, 1, 13));

        // Full moon should have > 95% illumination
        if (phase.phase == MoonPhaseType.fullMoon) {
          expect(phase.illumination, greaterThan(95));
        }
      });

      test('new moon has low illumination', () {
        // New moon was around December 30, 2024
        final phase = solunar.getMoonPhase(DateTime(2024, 12, 30));

        // New moon should have < 5% illumination
        if (phase.phase == MoonPhaseType.newMoon) {
          expect(phase.illumination, lessThan(5));
        }
      });

      test('moon phase types cycle correctly', () {
        final phases = <MoonPhaseType>[];

        // Check phases over a full synodic month
        for (int i = 0; i < 30; i++) {
          final date = DateTime(2026, 1, 1).add(Duration(days: i));
          final phase = solunar.getMoonPhase(date);
          if (phases.isEmpty || phases.last != phase.phase) {
            phases.add(phase.phase);
          }
        }

        // Should have multiple phase types
        expect(phases.length, greaterThan(4));
      });
    });

    group('getSolunarDay', () {
      test('returns valid solunar data for Austin, TX', () {
        const lat = 30.2672;
        const lng = -97.7431;
        final date = DateTime(2026, 1, 13);

        final day = solunar.getSolunarDay(lat, lng, date);

        expect(day, isNotNull);
        expect(day.date.year, equals(2026));
        expect(day.date.month, equals(1));
        expect(day.date.day, equals(13));
        expect(day.dayRating, greaterThanOrEqualTo(0));
        expect(day.dayRating, lessThanOrEqualTo(100));
      });

      test('returns major periods (usually 2)', () {
        const lat = 30.2672;
        const lng = -97.7431;
        final date = DateTime(2026, 1, 13);

        final day = solunar.getSolunarDay(lat, lng, date);

        // Should have at least 1 major period
        expect(day.majorPeriods, isNotEmpty);

        for (final period in day.majorPeriods) {
          expect(period.type, equals(SolunarPeriodType.major));
          expect(period.intensity, greaterThan(0));
          expect(period.intensity, lessThanOrEqualTo(100));
          expect(period.start.isBefore(period.end), isTrue);
          expect(period.duration.inMinutes, greaterThan(0));
        }
      });

      test('returns minor periods (usually 2)', () {
        const lat = 30.2672;
        const lng = -97.7431;
        final date = DateTime(2026, 1, 13);

        final day = solunar.getSolunarDay(lat, lng, date);

        // Minor periods may be 0-2 depending on moon rise/set
        for (final period in day.minorPeriods) {
          expect(period.type, equals(SolunarPeriodType.minor));
          expect(period.intensity, greaterThan(0));
          expect(period.duration.inMinutes, greaterThan(0));
        }
      });

      test('major periods are 2 hours', () {
        const lat = 30.2672;
        const lng = -97.7431;
        final date = DateTime(2026, 1, 13);

        final day = solunar.getSolunarDay(lat, lng, date);

        for (final period in day.majorPeriods) {
          // Should be approximately 2 hours (120 minutes)
          expect(period.duration.inMinutes, equals(120));
        }
      });

      test('minor periods are 1 hour', () {
        const lat = 30.2672;
        const lng = -97.7431;
        final date = DateTime(2026, 1, 13);

        final day = solunar.getSolunarDay(lat, lng, date);

        for (final period in day.minorPeriods) {
          // Should be approximately 1 hour (60 minutes)
          expect(period.duration.inMinutes, equals(60));
        }
      });

      test('includes moon times', () {
        const lat = 30.2672;
        const lng = -97.7431;
        final date = DateTime(2026, 1, 13);

        final day = solunar.getSolunarDay(lat, lng, date);

        // Moon transit should always be present
        expect(day.moonTransit, isNotNull);
      });

      test('includes sun times', () {
        const lat = 30.2672;
        const lng = -97.7431;
        final date = DateTime(2026, 1, 13);

        final day = solunar.getSolunarDay(lat, lng, date);

        expect(day.sunrise, isNotNull);
        expect(day.sunset, isNotNull);
        expect(day.sunrise!.isBefore(day.sunset!), isTrue);
      });

      test('works for extreme latitudes (Alaska)', () {
        const lat = 64.2;
        const lng = -149.5;
        final date = DateTime(2026, 6, 21); // Summer solstice

        final day = solunar.getSolunarDay(lat, lng, date);

        expect(day, isNotNull);
        expect(day.dayRating, greaterThanOrEqualTo(0));
      });

      test('works for southern hemisphere', () {
        const lat = -33.9;
        const lng = 151.2; // Sydney
        final date = DateTime(2026, 1, 13);

        final day = solunar.getSolunarDay(lat, lng, date);

        expect(day, isNotNull);
        expect(day.dayRating, greaterThanOrEqualTo(0));
      });
    });

    group('getCurrentRating', () {
      test('returns rating between 0 and 100', () {
        const lat = 30.2672;
        const lng = -97.7431;

        final rating = solunar.getCurrentRating(lat, lng);

        expect(rating, greaterThanOrEqualTo(0));
        expect(rating, lessThanOrEqualTo(100));
      });
    });

    group('getNextPeriod', () {
      test('returns next period or null', () {
        const lat = 30.2672;
        const lng = -97.7431;

        final nextPeriod = solunar.getNextPeriod(lat, lng);

        // May be null if all periods have passed today
        if (nextPeriod != null) {
          expect(nextPeriod.end.isAfter(DateTime.now()), isTrue);
        }
      });
    });

    group('getForecast', () {
      test('returns correct number of days', () {
        const lat = 30.2672;
        const lng = -97.7431;

        final forecast = solunar.getForecast(lat, lng, days: 7);

        expect(forecast.length, equals(7));
      });

      test('days are consecutive', () {
        const lat = 30.2672;
        const lng = -97.7431;

        final forecast = solunar.getForecast(lat, lng, days: 7);

        for (int i = 1; i < forecast.length; i++) {
          final diff = forecast[i].date.difference(forecast[i - 1].date);
          expect(diff.inDays, equals(1));
        }
      });
    });

    group('SolunarDay serialization', () {
      test('toJson and fromJson round-trip', () {
        const lat = 30.2672;
        const lng = -97.7431;
        final date = DateTime(2026, 1, 13);

        final original = solunar.getSolunarDay(lat, lng, date);
        final json = original.toJson();
        final restored = SolunarDay.fromJson(json);

        expect(restored.date.year, equals(original.date.year));
        expect(restored.date.month, equals(original.date.month));
        expect(restored.date.day, equals(original.date.day));
        expect(restored.dayRating, equals(original.dayRating));
        expect(restored.moonPhase.phase, equals(original.moonPhase.phase));
        expect(restored.majorPeriods.length, equals(original.majorPeriods.length));
        expect(restored.minorPeriods.length, equals(original.minorPeriods.length));
      });
    });

    group('MoonPhase serialization', () {
      test('toJson and fromJson round-trip', () {
        final original = solunar.getMoonPhase(DateTime(2026, 1, 13));
        final json = original.toJson();
        final restored = MoonPhase.fromJson(json);

        expect(restored.phase, equals(original.phase));
        expect(restored.age, closeTo(original.age, 0.001));
        expect(restored.illumination, closeTo(original.illumination, 0.001));
        expect(restored.angle, closeTo(original.angle, 0.001));
      });
    });

    group('SolunarPeriod', () {
      test('isActive returns correct value', () {
        const lat = 30.2672;
        const lng = -97.7431;

        final day = solunar.getSolunarDay(lat, lng, DateTime.now());
        final now = DateTime.now();

        for (final period in [...day.majorPeriods, ...day.minorPeriods]) {
          final shouldBeActive = now.isAfter(period.start) && now.isBefore(period.end);
          expect(period.isActive, equals(shouldBeActive));
        }
      });
    });

    group('MoonPhaseType', () {
      test('all phases have display names', () {
        for (final phase in MoonPhaseType.values) {
          expect(phase.displayName, isNotEmpty);
        }
      });

      test('all phases have emojis', () {
        for (final phase in MoonPhaseType.values) {
          expect(phase.emoji, isNotEmpty);
        }
      });

      test('all phases have hunting ratings', () {
        for (final phase in MoonPhaseType.values) {
          expect(phase.huntingRating, greaterThan(0));
          expect(phase.huntingRating, lessThanOrEqualTo(5));
        }
      });
    });
  });
}
