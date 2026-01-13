import 'dart:math' as math;

import 'package:maplibre_gl/maplibre_gl.dart';

/// Geographic utility functions.
class GeoUtils {
  GeoUtils._();

  /// Earth's radius in meters.
  static const double earthRadiusMeters = 6371000;

  /// Earth's radius in miles.
  static const double earthRadiusMiles = 3959;

  /// Calculate distance between two points in meters.
  static double distanceMeters(LatLng point1, LatLng point2) {
    return _haversineDistance(point1, point2, earthRadiusMeters);
  }

  /// Calculate distance between two points in miles.
  static double distanceMiles(LatLng point1, LatLng point2) {
    return _haversineDistance(point1, point2, earthRadiusMiles);
  }

  /// Calculate distance between two points in feet.
  static double distanceFeet(LatLng point1, LatLng point2) {
    return distanceMiles(point1, point2) * 5280;
  }

  /// Haversine formula for calculating distance.
  static double _haversineDistance(LatLng point1, LatLng point2, double radius) {
    final lat1 = point1.latitude * math.pi / 180;
    final lat2 = point2.latitude * math.pi / 180;
    final dLat = (point2.latitude - point1.latitude) * math.pi / 180;
    final dLon = (point2.longitude - point1.longitude) * math.pi / 180;

    final a = math.sin(dLat / 2) * math.sin(dLat / 2) +
        math.cos(lat1) * math.cos(lat2) * math.sin(dLon / 2) * math.sin(dLon / 2);
    final c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));

    return radius * c;
  }

  /// Calculate bearing from point1 to point2 in degrees (0-360).
  static double bearing(LatLng point1, LatLng point2) {
    final lat1 = point1.latitude * math.pi / 180;
    final lat2 = point2.latitude * math.pi / 180;
    final dLon = (point2.longitude - point1.longitude) * math.pi / 180;

    final y = math.sin(dLon) * math.cos(lat2);
    final x = math.cos(lat1) * math.sin(lat2) -
        math.sin(lat1) * math.cos(lat2) * math.cos(dLon);

    final bearing = math.atan2(y, x) * 180 / math.pi;
    return (bearing + 360) % 360;
  }

  /// Calculate a destination point given start, bearing, and distance.
  static LatLng destinationPoint(LatLng start, double bearingDeg, double distanceMeters) {
    final bearing = bearingDeg * math.pi / 180;
    final lat1 = start.latitude * math.pi / 180;
    final lon1 = start.longitude * math.pi / 180;
    final angularDistance = distanceMeters / earthRadiusMeters;

    final lat2 = math.asin(
      math.sin(lat1) * math.cos(angularDistance) +
          math.cos(lat1) * math.sin(angularDistance) * math.cos(bearing),
    );
    final lon2 = lon1 +
        math.atan2(
          math.sin(bearing) * math.sin(angularDistance) * math.cos(lat1),
          math.cos(angularDistance) - math.sin(lat1) * math.sin(lat2),
        );

    return LatLng(
      lat2 * 180 / math.pi,
      lon2 * 180 / math.pi,
    );
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

  /// Convert degrees to cardinal direction (16-point).
  static String degreesToCardinal(double degrees) {
    const directions = [
      'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
      'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW',
    ];
    final normalized = degrees % 360;
    final index = ((normalized + 11.25) / 22.5).floor() % 16;
    return directions[index];
  }

  /// Convert degrees to simple cardinal direction (8-point).
  static String degreesToSimpleCardinal(double degrees) {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    final normalized = degrees % 360;
    final index = ((normalized + 22.5) / 45).floor() % 8;
    return directions[index];
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

  /// Check if a point is inside a polygon.
  static bool pointInPolygon(LatLng point, List<LatLng> polygon) {
    if (polygon.length < 3) return false;

    bool inside = false;
    int j = polygon.length - 1;

    for (int i = 0; i < polygon.length; i++) {
      if ((polygon[i].latitude > point.latitude) != (polygon[j].latitude > point.latitude) &&
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

  /// Format distance for display (auto-selects units).
  static String formatDistance(double meters) {
    if (meters < 1000) {
      return '${meters.toStringAsFixed(0)} m';
    } else if (meters < 10000) {
      return '${(meters / 1000).toStringAsFixed(1)} km';
    } else {
      return '${(meters / 1000).toStringAsFixed(0)} km';
    }
  }

  /// Format distance for display in imperial units.
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
}
