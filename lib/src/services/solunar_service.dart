import 'dart:math' as math;

import 'package:flutter/foundation.dart';
import 'package:get/get.dart';

/// Solunar Calculator Service for hunting/fishing activity predictions.
///
/// This service implements solunar theory calculations using pure Dart
/// astronomical algorithms. No external API calls are required.
///
/// Solunar theory suggests that fish and game are more active during
/// certain periods related to the moon's position:
/// - Major Periods: When the moon is directly overhead (transit) or
///   underfoot (anti-transit) - lasting approximately 2 hours each
/// - Minor Periods: During moonrise and moonset - lasting approximately
///   1 hour each
///
/// Usage:
/// ```dart
/// final solunar = Get.put(SolunarService());
/// final today = solunar.getSolunarDay(30.2672, -97.7431, DateTime.now());
/// print('Day Rating: ${today.dayRating}');
/// print('Moon Phase: ${today.moonPhase.displayName}');
/// ```
class SolunarService extends GetxService {
  // ============================================================
  // ASTRONOMICAL CONSTANTS
  // ============================================================

  /// Julian date of J2000.0 epoch (January 1, 2000, 12:00 TT)
  static const double _j2000 = 2451545.0;

  /// Days per Julian century
  static const double _julianCentury = 36525.0;

  /// Degrees to radians conversion factor
  static const double _deg2rad = math.pi / 180.0;

  /// Radians to degrees conversion factor
  static const double _rad2deg = 180.0 / math.pi;

  /// Mean synodic month (new moon to new moon) in days
  static const double _synodicMonth = 29.530588853;

  /// Known new moon reference date (January 6, 2000 at 18:14 UTC)
  /// Julian date for this reference new moon
  static const double _newMoonReference = 2451550.1;

  // ============================================================
  // PUBLIC API
  // ============================================================

  /// Initialize the service
  Future<SolunarService> init() async {
    debugPrint('[SolunarService] Initialized');
    return this;
  }

  /// Get complete solunar data for a specific date and location.
  ///
  /// [lat] Latitude in decimal degrees (-90 to 90)
  /// [lng] Longitude in decimal degrees (-180 to 180)
  /// [date] The date to calculate solunar data for
  ///
  /// Returns a [SolunarDay] containing all solunar information for that day.
  SolunarDay getSolunarDay(double lat, double lng, DateTime date) {
    // Normalize the date to local midnight
    final localDate = DateTime(date.year, date.month, date.day);

    // Calculate moon phase
    final moonPhase = getMoonPhase(localDate);

    // Calculate moon times (rise, set, transit)
    final moonTimes = _calculateMoonTimes(lat, lng, localDate);

    // Calculate sun times for golden hour alignment
    final sunTimes = _calculateSunTimes(lat, lng, localDate);

    // Build major periods (moon transit and anti-transit)
    final majorPeriods = _buildMajorPeriods(
      moonTimes,
      sunTimes,
      localDate,
    );

    // Build minor periods (moonrise and moonset)
    final minorPeriods = _buildMinorPeriods(
      moonTimes,
      sunTimes,
      localDate,
    );

    // Calculate overall day rating
    final dayRating = _calculateDayRating(
      moonPhase,
      majorPeriods,
      minorPeriods,
      sunTimes,
    );

    return SolunarDay(
      date: localDate,
      majorPeriods: majorPeriods,
      minorPeriods: minorPeriods,
      moonPhase: moonPhase,
      moonrise: moonTimes.rise,
      moonset: moonTimes.set,
      moonTransit: moonTimes.transit,
      sunrise: sunTimes.rise,
      sunset: sunTimes.set,
      dayRating: dayRating,
    );
  }

  /// Get the current hunting/fishing rating for a location.
  ///
  /// Returns an integer from 0-100, where:
  /// - 0-25: Poor activity expected
  /// - 26-50: Fair activity expected
  /// - 51-75: Good activity expected
  /// - 76-100: Excellent activity expected
  int getCurrentRating(double lat, double lng) {
    final now = DateTime.now();
    final solunarDay = getSolunarDay(lat, lng, now);
    return _calculateCurrentRating(solunarDay, now);
  }

  /// Get the next upcoming solunar period (major or minor).
  ///
  /// Returns null if no periods remain for today.
  SolunarPeriod? getNextPeriod(double lat, double lng) {
    final now = DateTime.now();
    final solunarDay = getSolunarDay(lat, lng, now);

    // Combine and sort all periods
    final allPeriods = [...solunarDay.majorPeriods, ...solunarDay.minorPeriods]
      ..sort((a, b) => a.start.compareTo(b.start));

    // Find the next period that hasn't ended yet
    for (final period in allPeriods) {
      if (period.end.isAfter(now)) {
        return period;
      }
    }

    return null;
  }

  /// Get detailed moon phase information for a specific date.
  MoonPhase getMoonPhase(DateTime date) {
    final jd = _dateToJulian(date);
    final daysSinceNewMoon = _calculateMoonAge(jd);
    final phaseAngle = (daysSinceNewMoon / _synodicMonth) * 360.0;
    final illumination = _calculateIllumination(phaseAngle);

    return MoonPhase(
      phase: _getMoonPhaseType(daysSinceNewMoon),
      age: daysSinceNewMoon,
      illumination: illumination,
      angle: phaseAngle % 360.0,
    );
  }

  /// Get solunar forecast for multiple days.
  ///
  /// [days] Number of days to forecast (including today)
  List<SolunarDay> getForecast(double lat, double lng, {int days = 7}) {
    final forecast = <SolunarDay>[];
    final startDate = DateTime.now();

    for (int i = 0; i < days; i++) {
      final date = startDate.add(Duration(days: i));
      forecast.add(getSolunarDay(lat, lng, date));
    }

    return forecast;
  }

  /// Check if the current time is within a solunar period.
  bool isInSolunarPeriod(double lat, double lng) {
    final now = DateTime.now();
    final solunarDay = getSolunarDay(lat, lng, now);

    for (final period in [...solunarDay.majorPeriods, ...solunarDay.minorPeriods]) {
      if (now.isAfter(period.start) && now.isBefore(period.end)) {
        return true;
      }
    }

    return false;
  }

  /// Get the current active period, if any.
  SolunarPeriod? getCurrentPeriod(double lat, double lng) {
    final now = DateTime.now();
    final solunarDay = getSolunarDay(lat, lng, now);

    for (final period in [...solunarDay.majorPeriods, ...solunarDay.minorPeriods]) {
      if (now.isAfter(period.start) && now.isBefore(period.end)) {
        return period;
      }
    }

    return null;
  }

  // ============================================================
  // JULIAN DATE CALCULATIONS
  // ============================================================

  /// Convert a DateTime to Julian Date.
  ///
  /// Julian Date is a continuous count of days since the beginning of
  /// the Julian Period (January 1, 4713 BC in the proleptic Julian calendar).
  double _dateToJulian(DateTime date) {
    final utc = date.toUtc();
    final year = utc.year;
    final month = utc.month;
    final day = utc.day +
        (utc.hour + utc.minute / 60.0 + utc.second / 3600.0) / 24.0;

    // Algorithm from Meeus, "Astronomical Algorithms"
    int a = ((14 - month) / 12).floor();
    int y = year + 4800 - a;
    int m = month + 12 * a - 3;

    double jdn = day +
        ((153 * m + 2) / 5).floor() +
        365 * y +
        (y / 4).floor() -
        (y / 100).floor() +
        (y / 400).floor() -
        32045;

    return jdn;
  }

  /// Convert Julian Date back to DateTime.
  DateTime _julianToDate(double jd) {
    // Algorithm from Meeus, "Astronomical Algorithms"
    int z = (jd + 0.5).floor();
    double f = jd + 0.5 - z;

    int a;
    if (z < 2299161) {
      a = z;
    } else {
      int alpha = ((z - 1867216.25) / 36524.25).floor();
      a = z + 1 + alpha - (alpha / 4).floor();
    }

    int b = a + 1524;
    int c = ((b - 122.1) / 365.25).floor();
    int d = (365.25 * c).floor();
    int e = ((b - d) / 30.6001).floor();

    int day = b - d - (30.6001 * e).floor();
    int month = e < 14 ? e - 1 : e - 13;
    int year = month > 2 ? c - 4716 : c - 4715;

    // Convert fractional day to hours/minutes/seconds
    double hours = f * 24.0;
    int hour = hours.floor();
    double minutes = (hours - hour) * 60.0;
    int minute = minutes.floor();
    int second = ((minutes - minute) * 60.0).round();

    return DateTime.utc(year, month, day, hour, minute, second);
  }

  // ============================================================
  // MOON POSITION CALCULATIONS
  // ============================================================

  /// Calculate the moon's age (days since last new moon).
  double _calculateMoonAge(double jd) {
    // Days since reference new moon
    double daysSinceRef = jd - _newMoonReference;

    // Normalize to current lunation
    double age = daysSinceRef % _synodicMonth;
    if (age < 0) age += _synodicMonth;

    return age;
  }

  /// Calculate moon's ecliptic longitude using simplified algorithm.
  ///
  /// This provides accuracy within about 0.5 degrees, sufficient for
  /// solunar calculations.
  double _getMoonEclipticLongitude(double jd) {
    double t = (jd - _j2000) / _julianCentury;

    // Mean longitude of the Moon (degrees)
    double l0 = 218.3164477 +
        481267.88123421 * t -
        0.0015786 * t * t +
        t * t * t / 538841.0 -
        t * t * t * t / 65194000.0;

    // Mean elongation of the Moon (degrees)
    double d = 297.8501921 +
        445267.1114034 * t -
        0.0018819 * t * t +
        t * t * t / 545868.0 -
        t * t * t * t / 113065000.0;

    // Mean anomaly of the Sun (degrees)
    double m = 357.5291092 +
        35999.0502909 * t -
        0.0001536 * t * t +
        t * t * t / 24490000.0;

    // Mean anomaly of the Moon (degrees)
    double mPrime = 134.9633964 +
        477198.8675055 * t +
        0.0087414 * t * t +
        t * t * t / 69699.0 -
        t * t * t * t / 14712000.0;

    // Moon's argument of latitude (degrees)
    double f = 93.2720950 +
        483202.0175233 * t -
        0.0036539 * t * t -
        t * t * t / 3526000.0 +
        t * t * t * t / 863310000.0;

    // Convert to radians
    d = _normalizeAngle(d) * _deg2rad;
    m = _normalizeAngle(m) * _deg2rad;
    mPrime = _normalizeAngle(mPrime) * _deg2rad;
    f = _normalizeAngle(f) * _deg2rad;

    // Longitude corrections (simplified - main terms only)
    double longitude = l0 +
        6.288774 * math.sin(mPrime) +
        1.274027 * math.sin(2 * d - mPrime) +
        0.658314 * math.sin(2 * d) +
        0.213618 * math.sin(2 * mPrime) -
        0.185116 * math.sin(m) -
        0.114332 * math.sin(2 * f) +
        0.058793 * math.sin(2 * d - 2 * mPrime) +
        0.057066 * math.sin(2 * d - m - mPrime) +
        0.053322 * math.sin(2 * d + mPrime) +
        0.045758 * math.sin(2 * d - m) -
        0.040923 * math.sin(m - mPrime) -
        0.034720 * math.sin(d) -
        0.030383 * math.sin(m + mPrime) +
        0.015327 * math.sin(2 * d - 2 * f) -
        0.012528 * math.sin(mPrime + 2 * f) +
        0.010980 * math.sin(mPrime - 2 * f);

    return _normalizeAngle(longitude);
  }

  /// Calculate moon's declination (angular distance from celestial equator).
  double _getMoonDeclination(double jd) {
    double t = (jd - _j2000) / _julianCentury;

    // Get ecliptic longitude and latitude
    double lambda = _getMoonEclipticLongitude(jd) * _deg2rad;

    // Simplified ecliptic latitude (typically small for moon)
    double beta = _getMoonEclipticLatitude(jd) * _deg2rad;

    // Obliquity of the ecliptic
    double epsilon = (23.439291 - 0.0130042 * t) * _deg2rad;

    // Convert ecliptic to equatorial coordinates
    double declination = math.asin(
      math.sin(beta) * math.cos(epsilon) +
          math.cos(beta) * math.sin(epsilon) * math.sin(lambda),
    );

    return declination * _rad2deg;
  }

  /// Calculate moon's ecliptic latitude (simplified).
  double _getMoonEclipticLatitude(double jd) {
    double t = (jd - _j2000) / _julianCentury;

    // Mean anomaly of the Moon
    double mPrime = 134.9633964 +
        477198.8675055 * t +
        0.0087414 * t * t;

    // Moon's argument of latitude
    double f = 93.2720950 +
        483202.0175233 * t -
        0.0036539 * t * t;

    mPrime = _normalizeAngle(mPrime) * _deg2rad;
    f = _normalizeAngle(f) * _deg2rad;

    // Simplified latitude calculation
    double latitude = 5.128122 * math.sin(f) +
        0.280602 * math.sin(mPrime + f) +
        0.277693 * math.sin(mPrime - f);

    return latitude;
  }

  /// Calculate moon's right ascension.
  double _getMoonRightAscension(double jd) {
    double t = (jd - _j2000) / _julianCentury;

    double lambda = _getMoonEclipticLongitude(jd) * _deg2rad;
    double beta = _getMoonEclipticLatitude(jd) * _deg2rad;
    double epsilon = (23.439291 - 0.0130042 * t) * _deg2rad;

    double y = math.sin(lambda) * math.cos(epsilon) -
        math.tan(beta) * math.sin(epsilon);
    double x = math.cos(lambda);

    double ra = math.atan2(y, x) * _rad2deg;
    return _normalizeAngle(ra);
  }

  // ============================================================
  // MOON TIMES CALCULATIONS
  // ============================================================

  /// Calculate moonrise, moonset, and transit times.
  _MoonTimes _calculateMoonTimes(double lat, double lng, DateTime date) {
    // Calculate Julian date at midnight UTC for the given date
    final midnight = DateTime.utc(date.year, date.month, date.day, 0);
    final jdMidnight = _dateToJulian(midnight);

    // Find transit time (when moon crosses local meridian)
    DateTime? transit = _findMoonTransit(lat, lng, jdMidnight);

    // Find rise and set times
    DateTime? rise = _findMoonRiseSet(lat, lng, jdMidnight, isRise: true);
    DateTime? set = _findMoonRiseSet(lat, lng, jdMidnight, isRise: false);

    // Calculate anti-transit (moon underfoot, opposite side of Earth)
    DateTime? antiTransit;
    if (transit != null) {
      // Anti-transit is approximately 12 hours from transit
      // but we need to account for moon's motion
      antiTransit = transit.add(const Duration(hours: 12, minutes: 25));
      // Adjust to keep within the day if needed
      if (antiTransit.day != date.day) {
        antiTransit = transit.subtract(const Duration(hours: 11, minutes: 35));
      }
    }

    // Convert from UTC to local time
    final offset = date.timeZoneOffset;

    return _MoonTimes(
      rise: rise?.add(offset),
      set: set?.add(offset),
      transit: transit?.add(offset),
      antiTransit: antiTransit?.add(offset),
    );
  }

  /// Find moon transit time using iterative refinement.
  DateTime? _findMoonTransit(double lat, double lng, double jdStart) {
    // Greenwich Sidereal Time at 0h UT
    double gst0 = _getGreenwichSiderealTime(jdStart);

    // Initial estimate: when local hour angle = 0
    double ra = _getMoonRightAscension(jdStart);
    double hourAngle = ra - gst0 - lng;
    hourAngle = _normalizeAngle(hourAngle);
    if (hourAngle > 180) hourAngle -= 360;

    // Convert hour angle to time (15 degrees per hour)
    double transitTime = -hourAngle / 15.0;
    if (transitTime < 0) transitTime += 24;
    if (transitTime >= 24) transitTime -= 24;

    // Refine estimate (moon moves about 0.5 degrees per hour)
    double jdTransit = jdStart + transitTime / 24.0;

    // Iterate to refine
    for (int i = 0; i < 3; i++) {
      ra = _getMoonRightAscension(jdTransit);
      double gst = _getGreenwichSiderealTime(jdTransit);
      hourAngle = ra - gst - lng;
      hourAngle = _normalizeAngle(hourAngle);
      if (hourAngle > 180) hourAngle -= 360;

      double correction = -hourAngle / 15.0 / 24.0;
      jdTransit += correction;

      if (correction.abs() < 0.0001) break;
    }

    return _julianToDate(jdTransit);
  }

  /// Find moonrise or moonset time.
  DateTime? _findMoonRiseSet(
    double lat,
    double lng,
    double jdStart, {
    required bool isRise,
  }) {
    // Moon's apparent radius for rise/set calculation (degrees)
    // We use -0.833 degrees to account for atmospheric refraction
    // and the moon's average angular diameter
    const double h0 = -0.833;

    // Start search from transit time
    double jd = jdStart;
    double? prevAlt;
    double searchStep = 1.0 / 24.0; // 1 hour steps

    // Search through the day
    for (int hour = 0; hour <= 24; hour++) {
      jd = jdStart + hour * searchStep;
      double alt = _getMoonAltitude(lat, lng, jd);

      if (prevAlt != null) {
        bool risingNow = alt >= h0 && prevAlt < h0;
        bool settingNow = alt < h0 && prevAlt >= h0;

        if ((isRise && risingNow) || (!isRise && settingNow)) {
          // Refine with interpolation
          double fraction = (h0 - prevAlt) / (alt - prevAlt);
          double refinedJd = jd - searchStep + fraction * searchStep;

          // Further refinement
          for (int i = 0; i < 3; i++) {
            alt = _getMoonAltitude(lat, lng, refinedJd);
            double altDiff = alt - h0;
            refinedJd -= altDiff / 15.0 / 24.0; // Approximate correction
          }

          return _julianToDate(refinedJd);
        }
      }
      prevAlt = alt;
    }

    return null;
  }

  /// Calculate moon's altitude above horizon.
  double _getMoonAltitude(double lat, double lng, double jd) {
    double dec = _getMoonDeclination(jd) * _deg2rad;
    double ra = _getMoonRightAscension(jd);
    double gst = _getGreenwichSiderealTime(jd);

    // Local hour angle
    double ha = (gst + lng - ra) * _deg2rad;
    double latRad = lat * _deg2rad;

    // Calculate altitude
    double sinAlt = math.sin(latRad) * math.sin(dec) +
        math.cos(latRad) * math.cos(dec) * math.cos(ha);

    return math.asin(sinAlt.clamp(-1.0, 1.0)) * _rad2deg;
  }

  /// Calculate Greenwich Sidereal Time for a Julian Date.
  double _getGreenwichSiderealTime(double jd) {
    double t = (jd - _j2000) / _julianCentury;

    // Mean sidereal time at Greenwich (degrees)
    double gst = 280.46061837 +
        360.98564736629 * (jd - _j2000) +
        0.000387933 * t * t -
        t * t * t / 38710000.0;

    return _normalizeAngle(gst);
  }

  // ============================================================
  // SUN CALCULATIONS (Simplified for golden hour alignment)
  // ============================================================

  /// Calculate sunrise, sunset, and golden hours.
  _SunTimes _calculateSunTimes(double lat, double lng, DateTime date) {
    final jd = _dateToJulian(DateTime.utc(date.year, date.month, date.day, 12));

    // Sun's declination
    double t = (jd - _j2000) / _julianCentury;
    double meanLong = _normalizeAngle(280.46646 + 36000.76983 * t);
    double meanAnomaly = _normalizeAngle(357.52911 + 35999.05029 * t);
    double eclipticLong = meanLong +
        1.9146 * math.sin(meanAnomaly * _deg2rad) +
        0.02 * math.sin(2 * meanAnomaly * _deg2rad);

    double obliquity = 23.439 - 0.00000036 * (jd - _j2000);
    double declination = math.asin(
      math.sin(obliquity * _deg2rad) * math.sin(eclipticLong * _deg2rad),
    ) * _rad2deg;

    // Hour angle at sunrise/sunset
    double latRad = lat * _deg2rad;
    double decRad = declination * _deg2rad;

    // Standard altitude for sunrise/sunset (-0.833 degrees)
    double cosH = (math.sin(-0.833 * _deg2rad) -
            math.sin(latRad) * math.sin(decRad)) /
        (math.cos(latRad) * math.cos(decRad));

    DateTime? rise;
    DateTime? set;
    DateTime? goldenHourMorningStart;
    DateTime? goldenHourMorningEnd;
    DateTime? goldenHourEveningStart;
    DateTime? goldenHourEveningEnd;

    if (cosH.abs() <= 1.0) {
      double hourAngle = math.acos(cosH.clamp(-1.0, 1.0)) * _rad2deg;

      // Equation of time
      double b = 2 * math.pi * ((jd - _j2000) / 365.25);
      double eot = 229.18 *
          (0.000075 +
              0.001868 * math.cos(b) -
              0.032077 * math.sin(b) -
              0.014615 * math.cos(2 * b) -
              0.040849 * math.sin(2 * b));

      // Solar noon
      double solarNoon = 12.0 - lng / 15.0 - eot / 60.0;

      // Sunrise and sunset times (in hours UTC)
      double sunriseHour = solarNoon - hourAngle / 15.0;
      double sunsetHour = solarNoon + hourAngle / 15.0;

      // Convert to DateTime
      final offset = date.timeZoneOffset;
      rise = _hoursToDateTime(date, sunriseHour).add(offset);
      set = _hoursToDateTime(date, sunsetHour).add(offset);

      // Golden hour: roughly 1 hour after sunrise and 1 hour before sunset
      goldenHourMorningStart = rise;
      goldenHourMorningEnd = rise?.add(const Duration(hours: 1));
      goldenHourEveningStart = set?.subtract(const Duration(hours: 1));
      goldenHourEveningEnd = set;
    }

    return _SunTimes(
      rise: rise,
      set: set,
      goldenHourMorningStart: goldenHourMorningStart,
      goldenHourMorningEnd: goldenHourMorningEnd,
      goldenHourEveningStart: goldenHourEveningStart,
      goldenHourEveningEnd: goldenHourEveningEnd,
    );
  }

  /// Convert decimal hours to DateTime.
  DateTime _hoursToDateTime(DateTime date, double hours) {
    int h = hours.floor();
    double minFrac = (hours - h) * 60;
    int m = minFrac.floor();
    int s = ((minFrac - m) * 60).round();

    return DateTime.utc(date.year, date.month, date.day, h, m, s);
  }

  // ============================================================
  // MOON PHASE CALCULATIONS
  // ============================================================

  /// Determine the moon phase type from its age.
  MoonPhaseType _getMoonPhaseType(double age) {
    // Each phase spans about 3.69 days (29.53 / 8)
    double phaseLength = _synodicMonth / 8.0;

    if (age < phaseLength) {
      return MoonPhaseType.newMoon;
    } else if (age < 2 * phaseLength) {
      return MoonPhaseType.waxingCrescent;
    } else if (age < 3 * phaseLength) {
      return MoonPhaseType.firstQuarter;
    } else if (age < 4 * phaseLength) {
      return MoonPhaseType.waxingGibbous;
    } else if (age < 5 * phaseLength) {
      return MoonPhaseType.fullMoon;
    } else if (age < 6 * phaseLength) {
      return MoonPhaseType.waningGibbous;
    } else if (age < 7 * phaseLength) {
      return MoonPhaseType.lastQuarter;
    } else {
      return MoonPhaseType.waningCrescent;
    }
  }

  /// Calculate moon illumination percentage.
  double _calculateIllumination(double phaseAngle) {
    // Use cosine function: 0% at new moon (0 degrees), 100% at full (180)
    return ((1.0 - math.cos(phaseAngle * _deg2rad)) / 2.0 * 100.0);
  }

  // ============================================================
  // SOLUNAR PERIOD CALCULATIONS
  // ============================================================

  /// Build major solunar periods (transit and anti-transit).
  List<SolunarPeriod> _buildMajorPeriods(
    _MoonTimes moonTimes,
    _SunTimes sunTimes,
    DateTime date,
  ) {
    final periods = <SolunarPeriod>[];

    // Major period duration: 2 hours (1 hour before and after peak)
    const halfDuration = Duration(hours: 1);

    // Moon transit (overhead)
    if (moonTimes.transit != null) {
      final start = moonTimes.transit!.subtract(halfDuration);
      final end = moonTimes.transit!.add(halfDuration);
      final intensity = _calculatePeriodIntensity(
        moonTimes.transit!,
        sunTimes,
        isMajor: true,
      );

      periods.add(SolunarPeriod(
        start: start,
        end: end,
        type: SolunarPeriodType.major,
        intensity: intensity,
        description: 'Moon Overhead (Transit)',
        peakTime: moonTimes.transit!,
      ));
    }

    // Moon anti-transit (underfoot)
    if (moonTimes.antiTransit != null) {
      final start = moonTimes.antiTransit!.subtract(halfDuration);
      final end = moonTimes.antiTransit!.add(halfDuration);
      final intensity = _calculatePeriodIntensity(
        moonTimes.antiTransit!,
        sunTimes,
        isMajor: true,
      );

      periods.add(SolunarPeriod(
        start: start,
        end: end,
        type: SolunarPeriodType.major,
        intensity: intensity,
        description: 'Moon Underfoot (Anti-Transit)',
        peakTime: moonTimes.antiTransit!,
      ));
    }

    return periods;
  }

  /// Build minor solunar periods (moonrise and moonset).
  List<SolunarPeriod> _buildMinorPeriods(
    _MoonTimes moonTimes,
    _SunTimes sunTimes,
    DateTime date,
  ) {
    final periods = <SolunarPeriod>[];

    // Minor period duration: 1 hour (30 min before and after)
    const halfDuration = Duration(minutes: 30);

    // Moonrise
    if (moonTimes.rise != null) {
      final start = moonTimes.rise!.subtract(halfDuration);
      final end = moonTimes.rise!.add(halfDuration);
      final intensity = _calculatePeriodIntensity(
        moonTimes.rise!,
        sunTimes,
        isMajor: false,
      );

      periods.add(SolunarPeriod(
        start: start,
        end: end,
        type: SolunarPeriodType.minor,
        intensity: intensity,
        description: 'Moonrise',
        peakTime: moonTimes.rise!,
      ));
    }

    // Moonset
    if (moonTimes.set != null) {
      final start = moonTimes.set!.subtract(halfDuration);
      final end = moonTimes.set!.add(halfDuration);
      final intensity = _calculatePeriodIntensity(
        moonTimes.set!,
        sunTimes,
        isMajor: false,
      );

      periods.add(SolunarPeriod(
        start: start,
        end: end,
        type: SolunarPeriodType.minor,
        intensity: intensity,
        description: 'Moonset',
        peakTime: moonTimes.set!,
      ));
    }

    return periods;
  }

  /// Calculate the intensity boost for a period based on sun alignment.
  int _calculatePeriodIntensity(
    DateTime periodTime,
    _SunTimes sunTimes,
    {required bool isMajor}
  ) {
    int baseIntensity = isMajor ? 70 : 50;
    int sunBonus = 0;

    // Check alignment with golden hours
    if (_isWithinGoldenHour(periodTime, sunTimes)) {
      sunBonus = 25; // Significant boost for golden hour alignment
    } else if (_isWithinTwilight(periodTime, sunTimes)) {
      sunBonus = 15; // Moderate boost for twilight alignment
    }

    return math.min(100, baseIntensity + sunBonus);
  }

  /// Check if a time falls within golden hour.
  bool _isWithinGoldenHour(DateTime time, _SunTimes sunTimes) {
    // Morning golden hour
    if (sunTimes.goldenHourMorningStart != null &&
        sunTimes.goldenHourMorningEnd != null) {
      if (time.isAfter(sunTimes.goldenHourMorningStart!) &&
          time.isBefore(sunTimes.goldenHourMorningEnd!)) {
        return true;
      }
    }

    // Evening golden hour
    if (sunTimes.goldenHourEveningStart != null &&
        sunTimes.goldenHourEveningEnd != null) {
      if (time.isAfter(sunTimes.goldenHourEveningStart!) &&
          time.isBefore(sunTimes.goldenHourEveningEnd!)) {
        return true;
      }
    }

    return false;
  }

  /// Check if a time falls within twilight period.
  bool _isWithinTwilight(DateTime time, _SunTimes sunTimes) {
    // Extended twilight: 30 minutes before sunrise, 30 minutes after sunset
    if (sunTimes.rise != null) {
      final twilightStart = sunTimes.rise!.subtract(const Duration(minutes: 30));
      if (time.isAfter(twilightStart) && time.isBefore(sunTimes.rise!)) {
        return true;
      }
    }

    if (sunTimes.set != null) {
      final twilightEnd = sunTimes.set!.add(const Duration(minutes: 30));
      if (time.isAfter(sunTimes.set!) && time.isBefore(twilightEnd)) {
        return true;
      }
    }

    return false;
  }

  // ============================================================
  // RATING CALCULATIONS
  // ============================================================

  /// Calculate the overall day rating (0-100).
  int _calculateDayRating(
    MoonPhase moonPhase,
    List<SolunarPeriod> majorPeriods,
    List<SolunarPeriod> minorPeriods,
    _SunTimes sunTimes,
  ) {
    double rating = 30.0; // Base score

    // Moon phase bonus
    switch (moonPhase.phase) {
      case MoonPhaseType.fullMoon:
        rating += 20.0;
        break;
      case MoonPhaseType.newMoon:
        rating += 15.0;
        break;
      case MoonPhaseType.firstQuarter:
      case MoonPhaseType.lastQuarter:
        rating += 5.0;
        break;
      default:
        rating += 2.0;
    }

    // Bonus for period quality
    for (final period in majorPeriods) {
      if (period.intensity > 80) {
        rating += 10.0;
      } else if (period.intensity > 60) {
        rating += 5.0;
      }
    }

    for (final period in minorPeriods) {
      if (period.intensity > 80) {
        rating += 7.0;
      } else if (period.intensity > 60) {
        rating += 3.0;
      }
    }

    // Bonus for having all 4 periods in the day
    if (majorPeriods.length == 2 && minorPeriods.length == 2) {
      rating += 5.0;
    }

    return rating.clamp(0, 100).round();
  }

  /// Calculate the current instant rating.
  int _calculateCurrentRating(SolunarDay solunarDay, DateTime now) {
    double rating = 20.0; // Base score for any time

    // Check if currently in a major period
    for (final period in solunarDay.majorPeriods) {
      if (now.isAfter(period.start) && now.isBefore(period.end)) {
        // Within major period
        double proximity = _calculateProximityToCenter(now, period);
        rating += 40.0 * proximity; // Up to 40 bonus points
        break;
      } else {
        // Check proximity to major period (within 1 hour)
        final minutesToStart = period.start.difference(now).inMinutes.abs();
        final minutesToEnd = period.end.difference(now).inMinutes.abs();
        final minDistance = math.min(minutesToStart, minutesToEnd);

        if (minDistance < 60) {
          rating += 15.0 * (1 - minDistance / 60.0);
        }
      }
    }

    // Check if currently in a minor period
    for (final period in solunarDay.minorPeriods) {
      if (now.isAfter(period.start) && now.isBefore(period.end)) {
        double proximity = _calculateProximityToCenter(now, period);
        rating += 25.0 * proximity;
        break;
      } else {
        final minutesToStart = period.start.difference(now).inMinutes.abs();
        final minutesToEnd = period.end.difference(now).inMinutes.abs();
        final minDistance = math.min(minutesToStart, minutesToEnd);

        if (minDistance < 30) {
          rating += 10.0 * (1 - minDistance / 30.0);
        }
      }
    }

    // Moon phase bonus
    switch (solunarDay.moonPhase.phase) {
      case MoonPhaseType.fullMoon:
        rating += 20.0;
        break;
      case MoonPhaseType.newMoon:
        rating += 15.0;
        break;
      case MoonPhaseType.firstQuarter:
      case MoonPhaseType.lastQuarter:
        rating += 5.0;
        break;
      default:
        rating += 2.0;
    }

    // Golden hour bonus
    if (solunarDay.sunrise != null && solunarDay.sunset != null) {
      final sunriseEnd = solunarDay.sunrise!.add(const Duration(hours: 1));
      final sunsetStart = solunarDay.sunset!.subtract(const Duration(hours: 1));

      if ((now.isAfter(solunarDay.sunrise!) && now.isBefore(sunriseEnd)) ||
          (now.isAfter(sunsetStart) && now.isBefore(solunarDay.sunset!))) {
        rating += 10.0;
      }
    }

    return rating.clamp(0, 100).round();
  }

  /// Calculate how close we are to the center of a period (0 to 1).
  double _calculateProximityToCenter(DateTime now, SolunarPeriod period) {
    final duration = period.end.difference(period.start).inMinutes;
    final elapsed = now.difference(period.start).inMinutes;
    final center = duration / 2.0;

    // Distance from center (0 at center, 1 at edges)
    double distanceFromCenter = (elapsed - center).abs() / center;

    // Invert: 1 at center, 0 at edges
    return 1.0 - distanceFromCenter.clamp(0.0, 1.0);
  }

  // ============================================================
  // UTILITY FUNCTIONS
  // ============================================================

  /// Normalize an angle to 0-360 degrees.
  double _normalizeAngle(double angle) {
    angle = angle % 360.0;
    if (angle < 0) angle += 360.0;
    return angle;
  }
}

// ============================================================
// DATA CLASSES
// ============================================================

/// Complete solunar data for a single day.
class SolunarDay {
  /// The date this data is for
  final DateTime date;

  /// Major solunar periods (moon transit and anti-transit)
  /// Typically 2 per day, each lasting about 2 hours
  final List<SolunarPeriod> majorPeriods;

  /// Minor solunar periods (moonrise and moonset)
  /// Typically 2 per day, each lasting about 1 hour
  final List<SolunarPeriod> minorPeriods;

  /// Current moon phase information
  final MoonPhase moonPhase;

  /// Time of moonrise (null if moon doesn't rise this day)
  final DateTime? moonrise;

  /// Time of moonset (null if moon doesn't set this day)
  final DateTime? moonset;

  /// Time of moon transit (overhead)
  final DateTime? moonTransit;

  /// Time of sunrise
  final DateTime? sunrise;

  /// Time of sunset
  final DateTime? sunset;

  /// Overall day rating for hunting/fishing (0-100)
  final int dayRating;

  SolunarDay({
    required this.date,
    required this.majorPeriods,
    required this.minorPeriods,
    required this.moonPhase,
    this.moonrise,
    this.moonset,
    this.moonTransit,
    this.sunrise,
    this.sunset,
    required this.dayRating,
  });

  /// Get all periods sorted by start time.
  List<SolunarPeriod> get allPeriods {
    return [...majorPeriods, ...minorPeriods]
      ..sort((a, b) => a.start.compareTo(b.start));
  }

  /// Human-readable rating description.
  String get ratingDescription {
    if (dayRating >= 80) return 'Excellent';
    if (dayRating >= 60) return 'Good';
    if (dayRating >= 40) return 'Fair';
    if (dayRating >= 20) return 'Poor';
    return 'Very Poor';
  }

  /// Convert to JSON for storage/API.
  Map<String, dynamic> toJson() => {
        'date': date.toIso8601String(),
        'majorPeriods': majorPeriods.map((p) => p.toJson()).toList(),
        'minorPeriods': minorPeriods.map((p) => p.toJson()).toList(),
        'moonPhase': moonPhase.toJson(),
        'moonrise': moonrise?.toIso8601String(),
        'moonset': moonset?.toIso8601String(),
        'moonTransit': moonTransit?.toIso8601String(),
        'sunrise': sunrise?.toIso8601String(),
        'sunset': sunset?.toIso8601String(),
        'dayRating': dayRating,
      };

  /// Create from JSON.
  factory SolunarDay.fromJson(Map<String, dynamic> json) {
    return SolunarDay(
      date: DateTime.parse(json['date'] as String),
      majorPeriods: (json['majorPeriods'] as List)
          .map((p) => SolunarPeriod.fromJson(p as Map<String, dynamic>))
          .toList(),
      minorPeriods: (json['minorPeriods'] as List)
          .map((p) => SolunarPeriod.fromJson(p as Map<String, dynamic>))
          .toList(),
      moonPhase: MoonPhase.fromJson(json['moonPhase'] as Map<String, dynamic>),
      moonrise: json['moonrise'] != null
          ? DateTime.parse(json['moonrise'] as String)
          : null,
      moonset: json['moonset'] != null
          ? DateTime.parse(json['moonset'] as String)
          : null,
      moonTransit: json['moonTransit'] != null
          ? DateTime.parse(json['moonTransit'] as String)
          : null,
      sunrise: json['sunrise'] != null
          ? DateTime.parse(json['sunrise'] as String)
          : null,
      sunset: json['sunset'] != null
          ? DateTime.parse(json['sunset'] as String)
          : null,
      dayRating: json['dayRating'] as int,
    );
  }

  @override
  String toString() {
    return 'SolunarDay(date: $date, rating: $dayRating, phase: ${moonPhase.phase.displayName})';
  }
}

/// A solunar activity period.
class SolunarPeriod {
  /// Start time of the period
  final DateTime start;

  /// End time of the period
  final DateTime end;

  /// Type of period (major or minor)
  final SolunarPeriodType type;

  /// Intensity rating (0-100), higher during sun alignment
  final int intensity;

  /// Human-readable description
  final String description;

  /// Peak time (center of the period)
  final DateTime peakTime;

  SolunarPeriod({
    required this.start,
    required this.end,
    required this.type,
    required this.intensity,
    required this.description,
    required this.peakTime,
  });

  /// Duration of this period.
  Duration get duration => end.difference(start);

  /// Whether this period is currently active.
  bool get isActive {
    final now = DateTime.now();
    return now.isAfter(start) && now.isBefore(end);
  }

  /// Minutes until this period starts (negative if already started/passed).
  int get minutesUntilStart {
    return start.difference(DateTime.now()).inMinutes;
  }

  /// Convert to JSON.
  Map<String, dynamic> toJson() => {
        'start': start.toIso8601String(),
        'end': end.toIso8601String(),
        'type': type.name,
        'intensity': intensity,
        'description': description,
        'peakTime': peakTime.toIso8601String(),
      };

  /// Create from JSON.
  factory SolunarPeriod.fromJson(Map<String, dynamic> json) {
    return SolunarPeriod(
      start: DateTime.parse(json['start'] as String),
      end: DateTime.parse(json['end'] as String),
      type: SolunarPeriodType.values.firstWhere(
        (t) => t.name == json['type'],
      ),
      intensity: json['intensity'] as int,
      description: json['description'] as String,
      peakTime: DateTime.parse(json['peakTime'] as String),
    );
  }

  @override
  String toString() {
    return 'SolunarPeriod($description, ${start.hour}:${start.minute.toString().padLeft(2, '0')} - ${end.hour}:${end.minute.toString().padLeft(2, '0')}, intensity: $intensity)';
  }
}

/// Type of solunar period.
enum SolunarPeriodType {
  /// Major period (2 hours) - moon transit or anti-transit
  major,

  /// Minor period (1 hour) - moonrise or moonset
  minor;

  String get displayName {
    switch (this) {
      case SolunarPeriodType.major:
        return 'Major Period';
      case SolunarPeriodType.minor:
        return 'Minor Period';
    }
  }
}

/// Moon phase information.
class MoonPhase {
  /// The phase type
  final MoonPhaseType phase;

  /// Age of the moon in days since new moon
  final double age;

  /// Illumination percentage (0-100)
  final double illumination;

  /// Phase angle in degrees (0-360)
  final double angle;

  MoonPhase({
    required this.phase,
    required this.age,
    required this.illumination,
    required this.angle,
  });

  /// Whether this is a "best day" for hunting (full or new moon).
  bool get isBestDay =>
      phase == MoonPhaseType.fullMoon || phase == MoonPhaseType.newMoon;

  /// Days until the next new moon.
  double get daysUntilNewMoon {
    const synodicMonth = 29.530588853;
    return synodicMonth - age;
  }

  /// Days until the next full moon.
  double get daysUntilFullMoon {
    const synodicMonth = 29.530588853;
    const halfCycle = synodicMonth / 2;

    if (age < halfCycle) {
      return halfCycle - age;
    } else {
      return synodicMonth - age + halfCycle;
    }
  }

  /// Convert to JSON.
  Map<String, dynamic> toJson() => {
        'phase': phase.name,
        'age': age,
        'illumination': illumination,
        'angle': angle,
      };

  /// Create from JSON.
  factory MoonPhase.fromJson(Map<String, dynamic> json) {
    return MoonPhase(
      phase: MoonPhaseType.values.firstWhere(
        (p) => p.name == json['phase'],
      ),
      age: (json['age'] as num).toDouble(),
      illumination: (json['illumination'] as num).toDouble(),
      angle: (json['angle'] as num).toDouble(),
    );
  }

  @override
  String toString() {
    return 'MoonPhase(${phase.displayName}, ${illumination.toStringAsFixed(1)}% illuminated)';
  }
}

/// Moon phase types.
enum MoonPhaseType {
  newMoon,
  waxingCrescent,
  firstQuarter,
  waxingGibbous,
  fullMoon,
  waningGibbous,
  lastQuarter,
  waningCrescent;

  /// Human-readable name.
  String get displayName {
    switch (this) {
      case MoonPhaseType.newMoon:
        return 'New Moon';
      case MoonPhaseType.waxingCrescent:
        return 'Waxing Crescent';
      case MoonPhaseType.firstQuarter:
        return 'First Quarter';
      case MoonPhaseType.waxingGibbous:
        return 'Waxing Gibbous';
      case MoonPhaseType.fullMoon:
        return 'Full Moon';
      case MoonPhaseType.waningGibbous:
        return 'Waning Gibbous';
      case MoonPhaseType.lastQuarter:
        return 'Last Quarter';
      case MoonPhaseType.waningCrescent:
        return 'Waning Crescent';
    }
  }

  /// Emoji representation of the phase.
  String get emoji {
    switch (this) {
      case MoonPhaseType.newMoon:
        return '🌑';
      case MoonPhaseType.waxingCrescent:
        return '🌒';
      case MoonPhaseType.firstQuarter:
        return '🌓';
      case MoonPhaseType.waxingGibbous:
        return '🌔';
      case MoonPhaseType.fullMoon:
        return '🌕';
      case MoonPhaseType.waningGibbous:
        return '🌖';
      case MoonPhaseType.lastQuarter:
        return '🌗';
      case MoonPhaseType.waningCrescent:
        return '🌘';
    }
  }

  /// Hunting quality rating for this phase.
  int get huntingRating {
    switch (this) {
      case MoonPhaseType.fullMoon:
        return 5; // Best - most nighttime visibility
      case MoonPhaseType.newMoon:
        return 4; // Excellent - deer move more during day
      case MoonPhaseType.firstQuarter:
      case MoonPhaseType.lastQuarter:
        return 3; // Good
      case MoonPhaseType.waxingGibbous:
      case MoonPhaseType.waningGibbous:
        return 2; // Fair
      case MoonPhaseType.waxingCrescent:
      case MoonPhaseType.waningCrescent:
        return 1; // Average
    }
  }
}

// ============================================================
// INTERNAL DATA CLASSES
// ============================================================

/// Internal class for moon time calculations.
class _MoonTimes {
  final DateTime? rise;
  final DateTime? set;
  final DateTime? transit;
  final DateTime? antiTransit;

  _MoonTimes({
    this.rise,
    this.set,
    this.transit,
    this.antiTransit,
  });
}

/// Internal class for sun time calculations.
class _SunTimes {
  final DateTime? rise;
  final DateTime? set;
  final DateTime? goldenHourMorningStart;
  final DateTime? goldenHourMorningEnd;
  final DateTime? goldenHourEveningStart;
  final DateTime? goldenHourEveningEnd;

  _SunTimes({
    this.rise,
    this.set,
    this.goldenHourMorningStart,
    this.goldenHourMorningEnd,
    this.goldenHourEveningStart,
    this.goldenHourEveningEnd,
  });
}
