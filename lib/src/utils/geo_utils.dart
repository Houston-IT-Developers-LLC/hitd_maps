import 'dart:math' as math;

import 'package:maplibre_gl/maplibre_gl.dart';

/// Geographic utility functions.
class GeoUtils {
  GeoUtils._();

  /// Earth's radius in meters.
  static const double earthRadiusMeters = 6371000;

  /// Earth's radius in kilometers.
  static const double earthRadiusKm = 6371.0;

  /// Earth's radius in miles.
  static const double earthRadiusMiles = 3959;

  /// Meters per mile.
  static const double metersPerMile = 1609.34;

  /// Calculate distance between two points in kilometers.
  ///
  /// Uses Haversine formula for great-circle distance.
  static double calculateDistance(
    double lat1,
    double lng1,
    double lat2,
    double lng2,
  ) {
    final dLat = _toRadians(lat2 - lat1);
    final dLng = _toRadians(lng2 - lng1);

    final a = math.sin(dLat / 2) * math.sin(dLat / 2) +
        math.cos(_toRadians(lat1)) *
            math.cos(_toRadians(lat2)) *
            math.sin(dLng / 2) *
            math.sin(dLng / 2);
    final c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));

    return earthRadiusKm * c;
  }

  /// Calculate distance between two LatLng points in meters.
  static double distanceMeters(LatLng point1, LatLng point2) {
    return calculateDistance(
      point1.latitude,
      point1.longitude,
      point2.latitude,
      point2.longitude,
    ) * 1000;
  }

  /// Calculate distance between two LatLng points in miles.
  static double distanceMiles(LatLng point1, LatLng point2) {
    return calculateDistance(
      point1.latitude,
      point1.longitude,
      point2.latitude,
      point2.longitude,
    ) / 1.60934;
  }

  /// Calculate distance between two LatLng points in feet.
  static double distanceFeet(LatLng point1, LatLng point2) {
    return distanceMiles(point1, point2) * 5280;
  }

  /// Calculate bearing from point1 to point2 in degrees (0-360).
  static double calculateBearing(
    double lat1,
    double lng1,
    double lat2,
    double lng2,
  ) {
    final dLng = _toRadians(lng2 - lng1);
    final lat1Rad = _toRadians(lat1);
    final lat2Rad = _toRadians(lat2);

    final y = math.sin(dLng) * math.cos(lat2Rad);
    final x = math.cos(lat1Rad) * math.sin(lat2Rad) -
        math.sin(lat1Rad) * math.cos(lat2Rad) * math.cos(dLng);

    final bearing = math.atan2(y, x) * 180 / math.pi;
    return (bearing + 360) % 360;
  }

  /// Calculate bearing between two LatLng points.
  static double bearing(LatLng point1, LatLng point2) {
    return calculateBearing(
      point1.latitude,
      point1.longitude,
      point2.latitude,
      point2.longitude,
    );
  }

  /// Calculate a destination point given start coordinates, bearing, and distance.
  ///
  /// Returns a map with 'lat' and 'lng' keys.
  static Map<String, double> destinationPoint(
    double lat,
    double lng,
    double bearingDeg,
    double distanceKm,
  ) {
    final bearingRad = _toRadians(bearingDeg);
    final latRad = _toRadians(lat);
    final lngRad = _toRadians(lng);
    final angularDistance = distanceKm / earthRadiusKm;

    final lat2 = math.asin(
      math.sin(latRad) * math.cos(angularDistance) +
          math.cos(latRad) * math.sin(angularDistance) * math.cos(bearingRad),
    );
    final lng2 = lngRad +
        math.atan2(
          math.sin(bearingRad) * math.sin(angularDistance) * math.cos(latRad),
          math.cos(angularDistance) - math.sin(latRad) * math.sin(lat2),
        );

    return {
      'lat': _toDegrees(lat2),
      'lng': _toDegrees(lng2),
    };
  }

  /// Calculate a destination point from LatLng, bearing, and distance in meters.
  static LatLng destinationPointLatLng(
    LatLng start,
    double bearingDeg,
    double distanceMeters,
  ) {
    final result = destinationPoint(
      start.latitude,
      start.longitude,
      bearingDeg,
      distanceMeters / 1000,
    );
    return LatLng(result['lat']!, result['lng']!);
  }

  /// Convert cardinal direction to degrees.
  static double cardinalToDegrees(String cardinal) {
    final directions = {
      'N': 0.0, 'NNE': 22.5, 'NE': 45.0, 'ENE': 67.5,
      'E': 90.0, 'ESE': 112.5, 'SE': 135.0, 'SSE': 157.5,
      'S': 180.0, 'SSW': 202.5, 'SW': 225.0, 'WSW': 247.5,
      'W': 270.0, 'WNW': 292.5, 'NW': 315.0, 'NNW': 337.5,
    };
    return directions[cardinal.toUpperCase()] ?? 0.0;
  }

  /// Convert degrees to cardinal direction (8-point).
  static String degreesToCardinal(double degrees) {
    // Normalize to 0-360
    final normalized = ((degrees % 360) + 360) % 360;

    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    final index = ((normalized + 22.5) / 45).floor() % 8;
    return directions[index];
  }

  /// Convert degrees to 16-point cardinal direction.
  static String degreesToCardinal16(double degrees) {
    final normalized = ((degrees % 360) + 360) % 360;

    const directions = [
      'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
      'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW',
    ];
    final index = ((normalized + 11.25) / 22.5).floor() % 16;
    return directions[index];
  }

  /// Check if a point is inside a polygon.
  ///
  /// Uses ray casting algorithm.
  /// Polygon is a list of [lat, lng] coordinate pairs.
  static bool isPointInPolygon(
    double lat,
    double lng,
    List<List<double>> polygon,
  ) {
    if (polygon.length < 3) return false;

    bool inside = false;
    int j = polygon.length - 1;

    for (int i = 0; i < polygon.length; i++) {
      final yi = polygon[i][0];
      final xi = polygon[i][1];
      final yj = polygon[j][0];
      final xj = polygon[j][1];

      if ((yi > lat) != (yj > lat) &&
          lng < (xj - xi) * (lat - yi) / (yj - yi) + xi) {
        inside = !inside;
      }
      j = i;
    }

    return inside;
  }

  /// Check if a LatLng point is inside a polygon of LatLng points.
  static bool pointInPolygon(LatLng point, List<LatLng> polygon) {
    if (polygon.length < 3) return false;

    bool inside = false;
    int j = polygon.length - 1;

    for (int i = 0; i < polygon.length; i++) {
      if ((polygon[i].latitude > point.latitude) !=
              (polygon[j].latitude > point.latitude) &&
          point.longitude <
              (polygon[j].longitude - polygon[i].longitude) *
                      (point.latitude - polygon[i].latitude) /
                      (polygon[j].latitude - polygon[i].latitude) +
                  polygon[i].longitude) {
        inside = !inside;
      }
      j = i;
    }

    return inside;
  }

  /// Convert meters to miles.
  static double metersToMiles(double meters) {
    return meters / metersPerMile;
  }

  /// Convert miles to meters.
  static double milesToMeters(double miles) {
    return miles * metersPerMile;
  }

  /// Convert kilometers to miles.
  static double kmToMiles(double km) {
    return km / 1.60934;
  }

  /// Convert miles to kilometers.
  static double milesToKm(double miles) {
    return miles * 1.60934;
  }

  /// Format distance for display (auto-selects units - imperial).
  static String formatDistance(double km) {
    final meters = km * 1000;
    final feet = meters * 3.28084;

    if (feet < 1000) {
      return '${feet.toStringAsFixed(0)} ft';
    } else {
      final miles = feet / 5280;
      if (miles < 10) {
        return '${miles.toStringAsFixed(1)} mi';
      } else {
        return '${miles.toStringAsFixed(0)} mi';
      }
    }
  }

  /// Format distance in metric units.
  static String formatDistanceMetric(double meters) {
    if (meters < 1000) {
      return '${meters.toStringAsFixed(0)} m';
    } else if (meters < 10000) {
      return '${(meters / 1000).toStringAsFixed(1)} km';
    } else {
      return '${(meters / 1000).toStringAsFixed(0)} km';
    }
  }

  /// Format distance in imperial units.
  static String formatDistanceImperial(double meters) {
    final feet = meters * 3.28084;
    if (feet < 1000) {
      return '${feet.toStringAsFixed(0)} ft';
    } else {
      final miles = feet / 5280;
      if (miles < 10) {
        return '${miles.toStringAsFixed(1)} mi';
      } else {
        return '${miles.toStringAsFixed(0)} mi';
      }
    }
  }

  /// Calculate the center point of a list of coordinates.
  static LatLng centerOfPoints(List<LatLng> points) {
    if (points.isEmpty) return const LatLng(0, 0);
    if (points.length == 1) return points.first;

    double x = 0, y = 0, z = 0;

    for (final point in points) {
      final lat = point.latitude * math.pi / 180;
      final lon = point.longitude * math.pi / 180;
      x += math.cos(lat) * math.cos(lon);
      y += math.cos(lat) * math.sin(lon);
      z += math.sin(lat);
    }

    final total = points.length;
    x /= total;
    y /= total;
    z /= total;

    final centralLon = math.atan2(y, x);
    final centralLat = math.atan2(z, math.sqrt(x * x + y * y));

    return LatLng(
      centralLat * 180 / math.pi,
      centralLon * 180 / math.pi,
    );
  }

  /// Calculate bounds that contain all points.
  static LatLngBounds boundsOfPoints(List<LatLng> points) {
    if (points.isEmpty) {
      return LatLngBounds(
        southwest: const LatLng(0, 0),
        northeast: const LatLng(0, 0),
      );
    }

    double minLat = points.first.latitude;
    double maxLat = points.first.latitude;
    double minLon = points.first.longitude;
    double maxLon = points.first.longitude;

    for (final point in points) {
      minLat = math.min(minLat, point.latitude);
      maxLat = math.max(maxLat, point.latitude);
      minLon = math.min(minLon, point.longitude);
      maxLon = math.max(maxLon, point.longitude);
    }

    return LatLngBounds(
      southwest: LatLng(minLat, minLon),
      northeast: LatLng(maxLat, maxLon),
    );
  }

  /// Convert degrees to radians.
  static double _toRadians(double degrees) {
    return degrees * math.pi / 180;
  }

  /// Convert radians to degrees.
  static double _toDegrees(double radians) {
    return radians * 180 / math.pi;
  }

  // ============================================================
  // CIRCLE POLYGON GENERATION
  // ============================================================

  /// Generate polygon coordinates that approximate a circle.
  ///
  /// MapLibre doesn't have a native Circle overlay like Google Maps,
  /// so we generate polygon coordinates to approximate circles.
  ///
  /// [center] - Center coordinate of the circle
  /// [radiusMeters] - Radius in meters
  /// [points] - Number of points to use (higher = smoother, default 64)
  ///
  /// Returns a list of LatLng coordinates forming the circle polygon.
  static List<LatLng> generateCirclePolygon({
    required LatLng center,
    required double radiusMeters,
    int points = 64,
  }) {
    final List<LatLng> coordinates = [];

    // Convert radius to radians (angular distance on sphere)
    final double angularRadius = radiusMeters / earthRadiusMeters;

    // Center in radians
    final double centerLatRad = _toRadians(center.latitude);
    final double centerLngRad = _toRadians(center.longitude);

    for (int i = 0; i < points; i++) {
      // Angle for this point (0 to 2*PI)
      final double angle = (i * 2 * math.pi) / points;

      // Calculate point on circle using spherical geometry
      final double pointLatRad = math.asin(
        math.sin(centerLatRad) * math.cos(angularRadius) +
            math.cos(centerLatRad) * math.sin(angularRadius) * math.cos(angle),
      );

      final double pointLngRad = centerLngRad +
          math.atan2(
            math.sin(angle) * math.sin(angularRadius) * math.cos(centerLatRad),
            math.cos(angularRadius) -
                math.sin(centerLatRad) * math.sin(pointLatRad),
          );

      // Convert back to degrees
      coordinates.add(LatLng(
        _toDegrees(pointLatRad),
        _toDegrees(pointLngRad),
      ));
    }

    // Close the polygon by adding the first point at the end
    if (coordinates.isNotEmpty) {
      coordinates.add(coordinates.first);
    }

    return coordinates;
  }

  /// Generate a simple circle approximation for flat/local areas.
  ///
  /// This is a faster approximation suitable for small areas where
  /// Earth's curvature can be ignored.
  ///
  /// [center] - Center coordinate of the circle
  /// [radiusMeters] - Radius in meters
  /// [points] - Number of points to use (default 32)
  static List<LatLng> generateCirclePolygonFlat({
    required LatLng center,
    required double radiusMeters,
    int points = 32,
  }) {
    final List<LatLng> coordinates = [];

    // Approximate meters per degree at this latitude
    const double metersPerDegreeLat = 111320;
    final double metersPerDegreeLng =
        111320 * math.cos(_toRadians(center.latitude));

    // Convert radius to degrees
    final double radiusLat = radiusMeters / metersPerDegreeLat;
    final double radiusLng = radiusMeters / metersPerDegreeLng;

    for (int i = 0; i < points; i++) {
      final double angle = (i * 2 * math.pi) / points;
      final double lat = center.latitude + radiusLat * math.cos(angle);
      final double lng = center.longitude + radiusLng * math.sin(angle);
      coordinates.add(LatLng(lat, lng));
    }

    // Close the polygon
    if (coordinates.isNotEmpty) {
      coordinates.add(coordinates.first);
    }

    return coordinates;
  }

  /// Generate an uncertainty circle for GPS accuracy display.
  ///
  /// This is specifically designed for showing GPS accuracy circles
  /// that grow over time when a user goes offline.
  ///
  /// [center] - Center coordinate
  /// [baseRadiusMeters] - Base GPS accuracy radius in meters
  /// [elapsedMinutes] - Minutes since last update (for growing radius)
  /// [growthRateMeters] - Meters to add per 5-minute interval (default 538m)
  static List<LatLng> generateUncertaintyCircle({
    required LatLng center,
    double baseRadiusMeters = 538,
    int elapsedMinutes = 0,
    double growthRateMeters = 538,
  }) {
    // Calculate growing radius based on time
    final int intervals = elapsedMinutes ~/ 5;
    final double radius =
        intervals == 0 ? baseRadiusMeters : intervals * growthRateMeters;

    return generateCirclePolygonFlat(
      center: center,
      radiusMeters: radius,
      points: 32,
    );
  }
}
