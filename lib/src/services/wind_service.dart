import 'dart:developer';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:get/get.dart';

/// Wind data model representing current or forecasted wind conditions
class WindData {
  final DateTime time;
  final double speed; // mph
  final double direction; // degrees (0 = N, 90 = E, 180 = S, 270 = W)
  final double? gusts; // mph
  final String cardinalDirection; // "N", "NE", "E", etc.

  const WindData({
    required this.time,
    required this.speed,
    required this.direction,
    this.gusts,
    required this.cardinalDirection,
  });

  /// Create WindData from Open-Meteo API response values
  factory WindData.fromOpenMeteo({
    required String timeStr,
    required double speedKmh,
    required double direction,
    double? gustsKmh,
  }) {
    // Convert km/h to mph (1 km/h = 0.621371 mph)
    final speedMph = speedKmh * 0.621371;
    final gustsMph = gustsKmh != null ? gustsKmh * 0.621371 : null;

    return WindData(
      time: DateTime.parse(timeStr),
      speed: speedMph,
      direction: direction,
      gusts: gustsMph,
      cardinalDirection: _degreesToCardinal(direction),
    );
  }

  /// Convert degrees to cardinal direction
  static String _degreesToCardinal(double degrees) {
    // Normalize degrees to 0-360
    final normalized = degrees % 360;

    // 16-point compass rose
    const directions = [
      'N', 'NNE', 'NE', 'ENE',
      'E', 'ESE', 'SE', 'SSE',
      'S', 'SSW', 'SW', 'WSW',
      'W', 'WNW', 'NW', 'NNW'
    ];

    // Each direction covers 22.5 degrees, offset by 11.25 to center
    final index = ((normalized + 11.25) / 22.5).floor() % 16;
    return directions[index];
  }

  /// Get simplified 8-point cardinal direction
  String get simpleCardinal {
    const simple = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    final index = ((direction + 22.5) / 45).floor() % 8;
    return simple[index];
  }

  @override
  String toString() {
    return 'WindData(time: $time, speed: ${speed.toStringAsFixed(1)} mph, '
        'direction: ${direction.toStringAsFixed(0)}° $cardinalDirection, '
        'gusts: ${gusts?.toStringAsFixed(1) ?? "N/A"} mph)';
  }

  /// Copy with modifications
  WindData copyWith({
    DateTime? time,
    double? speed,
    double? direction,
    double? gusts,
    String? cardinalDirection,
  }) {
    return WindData(
      time: time ?? this.time,
      speed: speed ?? this.speed,
      direction: direction ?? this.direction,
      gusts: gusts ?? this.gusts,
      cardinalDirection: cardinalDirection ?? this.cardinalDirection,
    );
  }
}

/// Hunting wind quality rating
enum HuntingWindQuality {
  /// Less than 5 mph - ideal for hunting, scent doesn't travel far
  excellent,

  /// 5-10 mph - good conditions, predictable scent cone
  good,

  /// 10-15 mph - fair conditions, scent disperses quickly
  fair,

  /// Greater than 15 mph - poor conditions, unpredictable scent movement
  poor,
}

/// Extension for HuntingWindQuality display properties
extension HuntingWindQualityExtension on HuntingWindQuality {
  String get label {
    switch (this) {
      case HuntingWindQuality.excellent:
        return 'Excellent';
      case HuntingWindQuality.good:
        return 'Good';
      case HuntingWindQuality.fair:
        return 'Fair';
      case HuntingWindQuality.poor:
        return 'Poor';
    }
  }

  String get description {
    switch (this) {
      case HuntingWindQuality.excellent:
        return 'Calm winds, ideal hunting conditions';
      case HuntingWindQuality.good:
        return 'Light breeze, predictable scent cone';
      case HuntingWindQuality.fair:
        return 'Moderate wind, scent disperses quickly';
      case HuntingWindQuality.poor:
        return 'Strong winds, unpredictable scent';
    }
  }

  /// Speed range in mph
  String get speedRange {
    switch (this) {
      case HuntingWindQuality.excellent:
        return '< 5 mph';
      case HuntingWindQuality.good:
        return '5-10 mph';
      case HuntingWindQuality.fair:
        return '10-15 mph';
      case HuntingWindQuality.poor:
        return '> 15 mph';
    }
  }
}

/// Cache entry for wind data
class _WindCacheEntry {
  final List<WindData> hourlyData;
  final DateTime fetchedAt;
  final double lat;
  final double lng;

  _WindCacheEntry({
    required this.hourlyData,
    required this.fetchedAt,
    required this.lat,
    required this.lng,
  });

  /// Check if cache is still valid (30 minutes)
  bool get isValid {
    return DateTime.now().difference(fetchedAt).inMinutes < 30;
  }

  /// Check if location matches (within ~1km tolerance)
  bool matchesLocation(double latitude, double longitude) {
    const tolerance = 0.01; // ~1km
    return (lat - latitude).abs() < tolerance &&
        (lng - longitude).abs() < tolerance;
  }
}

/// Wind service for fetching weather data from Open-Meteo API
/// Uses GetX service pattern for dependency injection
class WindService extends GetxService {
  static const String _baseUrl = 'https://api.open-meteo.com/v1/forecast';
  static const Duration _cacheValidity = Duration(minutes: 30);

  late final Dio _dio;
  _WindCacheEntry? _cache;

  // Observable for reactive UI updates
  final Rx<WindData?> currentWind = Rx<WindData?>(null);
  final RxList<WindData> hourlyForecast = <WindData>[].obs;
  final RxBool isLoading = false.obs;
  final RxString error = ''.obs;

  @override
  void onInit() {
    super.onInit();
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
    ));

    if (kDebugMode) {
      _dio.interceptors.add(LogInterceptor(
        requestBody: true,
        responseBody: true,
        logPrint: (obj) => log(obj.toString()),
      ));
    }
  }

  /// Get current wind conditions for a location
  /// Returns cached data if available and valid
  Future<WindData> getCurrentWind(double lat, double lng) async {
    final hourlyData = await _fetchHourlyData(lat, lng);

    // Find the current hour's data
    final now = DateTime.now();
    final currentData = hourlyData.firstWhere(
      (data) => data.time.hour == now.hour && data.time.day == now.day,
      orElse: () => hourlyData.first,
    );

    currentWind.value = currentData;
    return currentData;
  }

  /// Get hourly forecast for a location
  /// [hours] - number of hours to return (default 24, max 72)
  Future<List<WindData>> getHourlyForecast(
    double lat,
    double lng, {
    int hours = 24,
  }) async {
    final allData = await _fetchHourlyData(lat, lng);
    final now = DateTime.now();

    // Filter to future hours only, limit to requested count
    final futureData = allData
        .where((data) => data.time.isAfter(now.subtract(const Duration(hours: 1))))
        .take(hours.clamp(1, 72))
        .toList();

    hourlyForecast.assignAll(futureData);
    return futureData;
  }

  /// Calculate scent cone direction (opposite of wind direction)
  /// Wind blowing FROM the north (0°) means scent travels SOUTH (180°)
  double getScentConeDirection(double windDirection) {
    return (windDirection + 180) % 360;
  }

  /// Get hunting quality rating based on wind speed
  HuntingWindQuality getHuntingQuality(double windSpeed) {
    if (windSpeed < 5) {
      return HuntingWindQuality.excellent;
    } else if (windSpeed < 10) {
      return HuntingWindQuality.good;
    } else if (windSpeed < 15) {
      return HuntingWindQuality.fair;
    } else {
      return HuntingWindQuality.poor;
    }
  }

  /// Get best hunting hours from forecast based on wind conditions
  /// Returns hours sorted by hunting quality (best first)
  List<WindData> getBestHuntingHours(List<WindData> forecast, {int limit = 5}) {
    final sorted = List<WindData>.from(forecast);
    sorted.sort((a, b) => a.speed.compareTo(b.speed));
    return sorted.take(limit).toList();
  }

  /// Fetch hourly data from API or cache
  Future<List<WindData>> _fetchHourlyData(double lat, double lng) async {
    // Check cache first
    if (_cache != null && _cache!.isValid && _cache!.matchesLocation(lat, lng)) {
      if (kDebugMode) {
        log('WindService: Using cached data');
      }
      return _cache!.hourlyData;
    }

    isLoading.value = true;
    error.value = '';

    try {
      final response = await _dio.get(
        '',
        queryParameters: {
          'latitude': lat,
          'longitude': lng,
          'hourly': 'windspeed_10m,winddirection_10m,windgusts_10m',
          'forecast_days': 3,
          'timezone': 'auto',
        },
      );

      final data = response.data as Map<String, dynamic>;
      final hourly = data['hourly'] as Map<String, dynamic>;

      final times = (hourly['time'] as List).cast<String>();
      final speeds = (hourly['windspeed_10m'] as List).cast<num>();
      final directions = (hourly['winddirection_10m'] as List).cast<num>();
      final gusts = hourly['windgusts_10m'] as List?;

      final hourlyData = <WindData>[];
      for (var i = 0; i < times.length; i++) {
        hourlyData.add(WindData.fromOpenMeteo(
          timeStr: times[i],
          speedKmh: speeds[i].toDouble(),
          direction: directions[i].toDouble(),
          gustsKmh: gusts != null ? gusts[i]?.toDouble() : null,
        ));
      }

      // Update cache
      _cache = _WindCacheEntry(
        hourlyData: hourlyData,
        fetchedAt: DateTime.now(),
        lat: lat,
        lng: lng,
      );

      if (kDebugMode) {
        log('WindService: Fetched ${hourlyData.length} hours of data');
      }

      return hourlyData;
    } on DioException catch (e) {
      final errorMsg = _handleDioError(e);
      error.value = errorMsg;
      if (kDebugMode) {
        log('WindService Error: $errorMsg');
      }
      rethrow;
    } finally {
      isLoading.value = false;
    }
  }

  /// Handle Dio errors with user-friendly messages
  String _handleDioError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return 'Connection timed out. Please check your internet.';
      case DioExceptionType.connectionError:
        return 'No internet connection.';
      case DioExceptionType.badResponse:
        final statusCode = e.response?.statusCode;
        if (statusCode == 429) {
          return 'Too many requests. Please wait a moment.';
        }
        return 'Server error ($statusCode). Please try again.';
      case DioExceptionType.cancel:
        return 'Request cancelled.';
      default:
        return 'Failed to fetch wind data.';
    }
  }

  /// Clear cached data
  void clearCache() {
    _cache = null;
    currentWind.value = null;
    hourlyForecast.clear();
  }

  /// Check if we have valid cached data for a location
  bool hasCachedData(double lat, double lng) {
    return _cache != null && _cache!.isValid && _cache!.matchesLocation(lat, lng);
  }

  @override
  void onClose() {
    _dio.close();
    super.onClose();
  }
}
