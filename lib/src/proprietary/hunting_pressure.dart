import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:maplibre_gl/maplibre_gl.dart';

import '../hitd_map_config.dart';

/// Hunting pressure levels.
enum HuntingPressureLevel {
  /// Very low hunting activity.
  veryLow(1, 'Very Low', 0xFF4CAF50),

  /// Low hunting activity.
  low(2, 'Low', 0xFF8BC34A),

  /// Moderate hunting activity.
  moderate(3, 'Moderate', 0xFFFFEB3B),

  /// High hunting activity.
  high(4, 'High', 0xFFFF9800),

  /// Very high hunting activity - crowded.
  veryHigh(5, 'Very High', 0xFFF44336);

  final int value;
  final String label;
  final int color;

  const HuntingPressureLevel(this.value, this.label, this.color);

  /// Get pressure level from numeric value.
  static HuntingPressureLevel fromValue(int value) {
    return HuntingPressureLevel.values.firstWhere(
      (l) => l.value == value,
      orElse: () => HuntingPressureLevel.moderate,
    );
  }
}

/// Data point for hunting pressure.
class HuntingPressurePoint {
  /// Location coordinates.
  final LatLng location;

  /// Computed pressure level.
  final HuntingPressureLevel pressure;

  /// Number of user reports in this area.
  final int reportCount;

  /// Average rating from user reports (1-5).
  final double averageRating;

  /// Time period for this data.
  final HuntingPressureTimePeriod period;

  /// Last updated timestamp.
  final DateTime updatedAt;

  /// County or region name.
  final String? county;

  /// Property ID if associated with a specific property.
  final String? propertyId;

  const HuntingPressurePoint({
    required this.location,
    required this.pressure,
    required this.reportCount,
    required this.averageRating,
    required this.period,
    required this.updatedAt,
    this.county,
    this.propertyId,
  });

  factory HuntingPressurePoint.fromJson(Map<String, dynamic> json) {
    return HuntingPressurePoint(
      location: LatLng(
        (json['lat'] as num).toDouble(),
        (json['lng'] as num).toDouble(),
      ),
      pressure: HuntingPressureLevel.fromValue(json['pressure'] as int),
      reportCount: json['reportCount'] as int? ?? 0,
      averageRating: (json['avgRating'] as num?)?.toDouble() ?? 3.0,
      period: HuntingPressureTimePeriod.values.byName(
        json['period'] as String? ?? 'allSeason',
      ),
      updatedAt: DateTime.parse(json['updatedAt'] as String),
      county: json['county'] as String?,
      propertyId: json['propertyId'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'lat': location.latitude,
    'lng': location.longitude,
    'pressure': pressure.value,
    'reportCount': reportCount,
    'avgRating': averageRating,
    'period': period.name,
    'updatedAt': updatedAt.toIso8601String(),
    'county': county,
    'propertyId': propertyId,
  };
}

/// Time periods for hunting pressure data.
enum HuntingPressureTimePeriod {
  /// Opening weekend (typically highest pressure).
  openingWeekend,

  /// First two weeks of season.
  earlySeeason,

  /// Middle of season.
  midSeason,

  /// Late season.
  lateSeason,

  /// Aggregated across all season.
  allSeason,

  /// Rut period (deer).
  rut,
}

/// User report for hunting pressure.
class HuntingPressureReport {
  /// Unique report ID.
  final String? id;

  /// Location where report was made.
  final LatLng location;

  /// Pressure rating (1-5).
  final int pressureRating;

  /// Number of other hunters seen.
  final int huntersSeen;

  /// Date of the hunt.
  final DateTime huntDate;

  /// Optional notes.
  final String? notes;

  /// User ID (anonymous hash).
  final String? userId;

  const HuntingPressureReport({
    this.id,
    required this.location,
    required this.pressureRating,
    required this.huntersSeen,
    required this.huntDate,
    this.notes,
    this.userId,
  });

  Map<String, dynamic> toJson() => {
    'id': id,
    'lat': location.latitude,
    'lng': location.longitude,
    'pressureRating': pressureRating,
    'huntersSeen': huntersSeen,
    'huntDate': huntDate.toIso8601String(),
    'notes': notes,
    'userId': userId,
  };
}

/// Service for managing hunting pressure data.
///
/// Provides crowdsourced hunting pressure information based on
/// user reports and aggregated data.
///
/// ## Usage
///
/// ```dart
/// final service = HuntingPressureService();
///
/// // Get pressure data for an area
/// final data = await service.getPressureData(
///   bounds: LatLngBounds(
///     southwest: LatLng(29.5, -99.5),
///     northeast: LatLng(30.5, -98.5),
///   ),
/// );
///
/// // Submit a report
/// await service.submitReport(
///   HuntingPressureReport(
///     location: LatLng(30.0, -99.0),
///     pressureRating: 4,
///     huntersSeen: 12,
///     huntDate: DateTime.now(),
///   ),
/// );
/// ```
class HuntingPressureService {
  static HuntingPressureService? _instance;

  /// Get singleton instance.
  static HuntingPressureService get instance {
    _instance ??= HuntingPressureService._();
    return _instance!;
  }

  HuntingPressureService._();

  final Dio _dio = Dio();

  /// Base URL for hunting pressure API.
  /// Override this to point to your backend.
  String apiBaseUrl = 'https://api.gspotoutdoors.com/v1/pressure';

  /// Get hunting pressure data for a bounding box.
  ///
  /// Returns a list of pressure points within the specified bounds.
  Future<List<HuntingPressurePoint>> getPressureData({
    required LatLngBounds bounds,
    HuntingPressureTimePeriod? period,
    int? year,
  }) async {
    try {
      final response = await _dio.get(
        '$apiBaseUrl/data',
        queryParameters: {
          'minLat': bounds.southwest.latitude,
          'minLng': bounds.southwest.longitude,
          'maxLat': bounds.northeast.latitude,
          'maxLng': bounds.northeast.longitude,
          if (period != null) 'period': period.name,
          if (year != null) 'year': year,
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data['points'];
        return data
            .map((json) => HuntingPressurePoint.fromJson(json as Map<String, dynamic>))
            .toList();
      }
      return [];
    } catch (e) {
      _log('Error fetching pressure data: $e');
      return [];
    }
  }

  /// Get pressure heatmap data as GeoJSON.
  ///
  /// Returns GeoJSON FeatureCollection suitable for MapLibre heatmap layer.
  Future<Map<String, dynamic>?> getPressureHeatmapGeoJson({
    required LatLngBounds bounds,
    HuntingPressureTimePeriod? period,
  }) async {
    try {
      final response = await _dio.get(
        '$apiBaseUrl/heatmap',
        queryParameters: {
          'minLat': bounds.southwest.latitude,
          'minLng': bounds.southwest.longitude,
          'maxLat': bounds.northeast.latitude,
          'maxLng': bounds.northeast.longitude,
          if (period != null) 'period': period.name,
          'format': 'geojson',
        },
      );

      if (response.statusCode == 200) {
        return response.data as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      _log('Error fetching heatmap data: $e');
      return null;
    }
  }

  /// Submit a hunting pressure report.
  ///
  /// Reports are anonymized and aggregated to build pressure data.
  Future<bool> submitReport(HuntingPressureReport report) async {
    try {
      final response = await _dio.post(
        '$apiBaseUrl/report',
        data: report.toJson(),
      );

      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      _log('Error submitting report: $e');
      return false;
    }
  }

  /// Get pressure statistics for a county.
  Future<Map<String, dynamic>?> getCountyStats(String county, String state) async {
    try {
      final response = await _dio.get(
        '$apiBaseUrl/stats/county',
        queryParameters: {
          'county': county,
          'state': state,
        },
      );

      if (response.statusCode == 200) {
        return response.data as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      _log('Error fetching county stats: $e');
      return null;
    }
  }

  /// Generate local mock data for testing/demo.
  ///
  /// Creates synthetic pressure data within the given bounds.
  List<HuntingPressurePoint> generateMockData({
    required LatLngBounds bounds,
    int count = 50,
  }) {
    final points = <HuntingPressurePoint>[];
    final random = DateTime.now().millisecondsSinceEpoch;

    final latRange = bounds.northeast.latitude - bounds.southwest.latitude;
    final lngRange = bounds.northeast.longitude - bounds.southwest.longitude;

    for (var i = 0; i < count; i++) {
      final lat = bounds.southwest.latitude + (((random * (i + 1)) % 1000) / 1000 * latRange);
      final lng = bounds.southwest.longitude + (((random * (i + 2)) % 1000) / 1000 * lngRange);
      final pressure = HuntingPressureLevel.fromValue(((random * i) % 5) + 1);

      points.add(HuntingPressurePoint(
        location: LatLng(lat, lng),
        pressure: pressure,
        reportCount: ((random * i) % 20) + 1,
        averageRating: 1.0 + ((random * i) % 400) / 100,
        period: HuntingPressureTimePeriod.allSeason,
        updatedAt: DateTime.now().subtract(Duration(days: (random * i) % 30)),
      ));
    }

    return points;
  }

  void _log(String message) {
    if (HitdMapConfig.isInitialized && HitdMapConfig.instance.debugMode) {
      // ignore: avoid_print
      print('[HuntingPressureService] $message');
    }
  }
}

/// MapLibre layer style for hunting pressure heatmap.
class HuntingPressureLayerStyle {
  HuntingPressureLayerStyle._();

  /// Get the heatmap layer paint properties.
  static Map<String, dynamic> getHeatmapPaint() {
    return {
      'heatmap-weight': [
        'interpolate',
        ['linear'],
        ['get', 'pressure'],
        1, 0.2,
        3, 0.5,
        5, 1.0,
      ],
      'heatmap-intensity': [
        'interpolate',
        ['linear'],
        ['zoom'],
        0, 1,
        9, 3,
      ],
      'heatmap-color': [
        'interpolate',
        ['linear'],
        ['heatmap-density'],
        0, 'rgba(0, 0, 0, 0)',
        0.2, 'rgba(76, 175, 80, 0.5)',
        0.4, 'rgba(139, 195, 74, 0.6)',
        0.6, 'rgba(255, 235, 59, 0.7)',
        0.8, 'rgba(255, 152, 0, 0.8)',
        1, 'rgba(244, 67, 54, 0.9)',
      ],
      'heatmap-radius': [
        'interpolate',
        ['linear'],
        ['zoom'],
        0, 2,
        9, 20,
        14, 40,
      ],
      'heatmap-opacity': [
        'interpolate',
        ['linear'],
        ['zoom'],
        7, 0.8,
        14, 0.4,
      ],
    };
  }

  /// Get circle layer for individual pressure points.
  static Map<String, dynamic> getPointPaint() {
    return {
      'circle-radius': [
        'interpolate',
        ['linear'],
        ['zoom'],
        8, 4,
        12, 8,
        16, 12,
      ],
      'circle-color': [
        'match',
        ['get', 'pressure'],
        1, '#4CAF50',
        2, '#8BC34A',
        3, '#FFEB3B',
        4, '#FF9800',
        5, '#F44336',
        '#757575',
      ],
      'circle-opacity': 0.8,
      'circle-stroke-width': 1,
      'circle-stroke-color': '#ffffff',
    };
  }
}
