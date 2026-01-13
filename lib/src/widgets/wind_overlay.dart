import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:maplibre_gl/maplibre_gl.dart';
import '../services/wind_service.dart';
import '../utils/colors.dart';

/// Wind overlay widget for displaying wind direction and scent cone on map
/// Designed to be positioned as a floating overlay on the map
class WindOverlay extends StatelessWidget {
  /// Current wind data to display
  final WindData? currentWind;

  /// Optional stand location to show scent cone from
  final LatLng? standLocation;

  /// Whether to show the scent cone visualization
  final bool showScentCone;

  /// Callback when wind badge is tapped
  final VoidCallback? onTap;

  /// Size of the wind indicator
  final double size;

  const WindOverlay({
    super.key,
    this.currentWind,
    this.standLocation,
    this.showScentCone = false,
    this.onTap,
    this.size = 60,
  });

  @override
  Widget build(BuildContext context) {
    if (currentWind == null) {
      return const SizedBox.shrink();
    }

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.15),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Wind arrow indicator
            _WindArrowIndicator(
              windData: currentWind!,
              size: size,
            ),
            const SizedBox(height: 4),
            // Wind speed badge
            _WindSpeedBadge(windData: currentWind!),
          ],
        ),
      ),
    );
  }
}

/// Wind arrow indicator showing direction
class _WindArrowIndicator extends StatelessWidget {
  final WindData windData;
  final double size;

  const _WindArrowIndicator({
    required this.windData,
    required this.size,
  });

  @override
  Widget build(BuildContext context) {
    final quality = _getHuntingQuality(windData.speed);
    final color = _getQualityColor(quality);

    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Compass background
          Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: color.withOpacity(0.1),
              border: Border.all(
                color: color.withOpacity(0.3),
                width: 2,
              ),
            ),
          ),
          // Cardinal directions
          ..._buildCardinalLabels(size),
          // Wind arrow
          Transform.rotate(
            angle: (windData.direction * math.pi / 180),
            child: CustomPaint(
              size: Size(size * 0.6, size * 0.6),
              painter: WindArrowPainter(
                color: color,
                quality: quality,
              ),
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildCardinalLabels(double size) {
    const labels = ['N', 'E', 'S', 'W'];
    const angles = [0.0, 90.0, 180.0, 270.0];

    return List.generate(4, (index) {
      final angle = angles[index] * math.pi / 180;
      final radius = size / 2 - 8;
      final x = radius * math.sin(angle);
      final y = -radius * math.cos(angle);

      return Positioned(
        left: size / 2 + x - 6,
        top: size / 2 + y - 6,
        child: Text(
          labels[index],
          style: const TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w600,
            color: Colors.grey,
            fontFamily: 'Montserrat',
          ),
        ),
      );
    });
  }

  HuntingWindQuality _getHuntingQuality(double speed) {
    if (speed < 5) return HuntingWindQuality.excellent;
    if (speed < 10) return HuntingWindQuality.good;
    if (speed < 15) return HuntingWindQuality.fair;
    return HuntingWindQuality.poor;
  }

  Color _getQualityColor(HuntingWindQuality quality) {
    switch (quality) {
      case HuntingWindQuality.excellent:
        return HitdColors.green;
      case HuntingWindQuality.good:
        return const Color(0xFF8BC34A); // Light green
      case HuntingWindQuality.fair:
        return const Color(0xFFFFC107); // Amber/Yellow
      case HuntingWindQuality.poor:
        return HitdColors.red;
    }
  }
}

/// Wind speed badge with quality indicator
class _WindSpeedBadge extends StatelessWidget {
  final WindData windData;

  const _WindSpeedBadge({required this.windData});

  @override
  Widget build(BuildContext context) {
    final quality = _getHuntingQuality(windData.speed);
    final color = _getQualityColor(quality);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Speed
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                windData.speed.toStringAsFixed(0),
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: color,
                  fontFamily: 'Montserrat',
                ),
              ),
              const SizedBox(width: 2),
              Text(
                'mph',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w500,
                  color: color.withOpacity(0.8),
                  fontFamily: 'Montserrat',
                ),
              ),
            ],
          ),
          // Direction
          Text(
            windData.simpleCardinal,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: color.withOpacity(0.8),
              fontFamily: 'Montserrat',
            ),
          ),
        ],
      ),
    );
  }

  HuntingWindQuality _getHuntingQuality(double speed) {
    if (speed < 5) return HuntingWindQuality.excellent;
    if (speed < 10) return HuntingWindQuality.good;
    if (speed < 15) return HuntingWindQuality.fair;
    return HuntingWindQuality.poor;
  }

  Color _getQualityColor(HuntingWindQuality quality) {
    switch (quality) {
      case HuntingWindQuality.excellent:
        return HitdColors.green;
      case HuntingWindQuality.good:
        return const Color(0xFF8BC34A);
      case HuntingWindQuality.fair:
        return const Color(0xFFFFC107);
      case HuntingWindQuality.poor:
        return HitdColors.red;
    }
  }
}

/// Custom painter for drawing wind direction arrow
class WindArrowPainter extends CustomPainter {
  final Color color;
  final HuntingWindQuality quality;

  WindArrowPainter({
    required this.color,
    required this.quality,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill
      ..strokeCap = StrokeCap.round;

    final centerX = size.width / 2;
    final centerY = size.height / 2;
    final arrowLength = size.height * 0.8;
    final arrowWidth = size.width * 0.3;

    // Arrow points upward (0 degrees = North)
    // The transform.rotate in parent handles direction
    final path = Path();

    // Arrow head (pointing up)
    path.moveTo(centerX, centerY - arrowLength / 2);
    path.lineTo(centerX - arrowWidth / 2, centerY - arrowLength / 6);
    path.lineTo(centerX - arrowWidth / 4, centerY - arrowLength / 6);

    // Arrow shaft
    path.lineTo(centerX - arrowWidth / 4, centerY + arrowLength / 3);
    path.lineTo(centerX + arrowWidth / 4, centerY + arrowLength / 3);
    path.lineTo(centerX + arrowWidth / 4, centerY - arrowLength / 6);

    // Complete arrow head
    path.lineTo(centerX + arrowWidth / 2, centerY - arrowLength / 6);
    path.close();

    canvas.drawPath(path, paint);

    // Draw tail feathers for wind indication
    final tailPaint = Paint()
      ..color = color.withOpacity(0.5)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;

    // Tail lines indicating wind flow
    final tailY = centerY + arrowLength / 3;
    canvas.drawLine(
      Offset(centerX - arrowWidth / 3, tailY + 4),
      Offset(centerX - arrowWidth / 3, tailY + 10),
      tailPaint,
    );
    canvas.drawLine(
      Offset(centerX, tailY + 4),
      Offset(centerX, tailY + 12),
      tailPaint,
    );
    canvas.drawLine(
      Offset(centerX + arrowWidth / 3, tailY + 4),
      Offset(centerX + arrowWidth / 3, tailY + 10),
      tailPaint,
    );
  }

  @override
  bool shouldRepaint(WindArrowPainter oldDelegate) {
    return oldDelegate.color != color || oldDelegate.quality != quality;
  }
}

/// Scent cone painter for visualizing scent dispersal from a stand
/// The scent cone shows the direction scent travels (opposite of wind)
class ScentConePainter extends CustomPainter {
  /// Wind direction in degrees (0 = N, 90 = E, etc.)
  final double windDirection;

  /// Wind speed in mph - affects cone spread
  final double windSpeed;

  /// Color of the scent cone
  final Color color;

  /// Length of the cone in pixels
  final double coneLength;

  ScentConePainter({
    required this.windDirection,
    required this.windSpeed,
    this.color = const Color(0xFF4CAF50),
    this.coneLength = 100,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final centerX = size.width / 2;
    final centerY = size.height / 2;

    // Scent travels opposite to wind direction
    final scentDirection = (windDirection + 180) % 360;
    final radians = scentDirection * math.pi / 180;

    // Cone spread angle increases with wind speed
    // Calm wind = narrow cone, strong wind = wide cone
    final spreadAngle = _calculateSpreadAngle(windSpeed);

    final paint = Paint()
      ..shader = RadialGradient(
        colors: [
          color.withOpacity(0.4),
          color.withOpacity(0.1),
          color.withOpacity(0.0),
        ],
        stops: const [0.0, 0.6, 1.0],
      ).createShader(Rect.fromCircle(
        center: Offset(centerX, centerY),
        radius: coneLength,
      ))
      ..style = PaintingStyle.fill;

    // Draw cone path
    final path = Path();
    path.moveTo(centerX, centerY);

    // Calculate cone edges
    final leftAngle = radians - spreadAngle / 2;
    final rightAngle = radians + spreadAngle / 2;

    // Arc from left edge to right edge
    path.lineTo(
      centerX + coneLength * math.sin(leftAngle),
      centerY - coneLength * math.cos(leftAngle),
    );

    // Draw arc
    path.arcTo(
      Rect.fromCircle(center: Offset(centerX, centerY), radius: coneLength),
      leftAngle - math.pi / 2,
      spreadAngle,
      false,
    );

    path.close();
    canvas.drawPath(path, paint);

    // Draw cone outline
    final outlinePaint = Paint()
      ..color = color.withOpacity(0.5)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;

    canvas.drawPath(path, outlinePaint);

    // Draw center line
    final centerLinePaint = Paint()
      ..color = color.withOpacity(0.6)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1
      ..strokeCap = StrokeCap.round;

    canvas.drawLine(
      Offset(centerX, centerY),
      Offset(
        centerX + coneLength * 0.8 * math.sin(radians),
        centerY - coneLength * 0.8 * math.cos(radians),
      ),
      centerLinePaint,
    );
  }

  /// Calculate spread angle based on wind speed
  /// Calm: ~30 degrees, Strong: ~60 degrees
  double _calculateSpreadAngle(double speed) {
    // Base angle is 30 degrees (pi/6)
    // Increases up to 60 degrees (pi/3) at 15+ mph
    final baseAngle = math.pi / 6;
    final maxAngle = math.pi / 3;
    final speedFactor = (speed / 15).clamp(0.0, 1.0);
    return baseAngle + (maxAngle - baseAngle) * speedFactor;
  }

  @override
  bool shouldRepaint(ScentConePainter oldDelegate) {
    return oldDelegate.windDirection != windDirection ||
        oldDelegate.windSpeed != windSpeed ||
        oldDelegate.color != color ||
        oldDelegate.coneLength != coneLength;
  }
}

/// Expanded wind detail panel showing forecast and hunting conditions
class WindDetailPanel extends StatelessWidget {
  final WindData currentWind;
  final List<WindData>? hourlyForecast;
  final VoidCallback? onClose;

  const WindDetailPanel({
    super.key,
    required this.currentWind,
    this.hourlyForecast,
    this.onClose,
  });

  @override
  Widget build(BuildContext context) {
    final quality = _getHuntingQuality(currentWind.speed);
    final color = _getQualityColor(quality);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Wind Conditions',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  fontFamily: 'Montserrat',
                ),
              ),
              if (onClose != null)
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: onClose,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
            ],
          ),
          const SizedBox(height: 16),

          // Current conditions
          Row(
            children: [
              // Wind indicator
              _WindArrowIndicator(
                windData: currentWind,
                size: 80,
              ),
              const SizedBox(width: 16),

              // Details
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Speed and direction
                    Row(
                      children: [
                        Text(
                          '${currentWind.speed.toStringAsFixed(0)} mph',
                          style: TextStyle(
                            fontSize: 28,
                            fontWeight: FontWeight.w700,
                            color: color,
                            fontFamily: 'Montserrat',
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'from ${currentWind.cardinalDirection}',
                          style: const TextStyle(
                            fontSize: 14,
                            color: Colors.grey,
                            fontFamily: 'Montserrat',
                          ),
                        ),
                      ],
                    ),

                    // Gusts
                    if (currentWind.gusts != null)
                      Text(
                        'Gusts up to ${currentWind.gusts!.toStringAsFixed(0)} mph',
                        style: const TextStyle(
                          fontSize: 12,
                          color: Colors.grey,
                          fontFamily: 'Montserrat',
                        ),
                      ),

                    const SizedBox(height: 8),

                    // Hunting quality badge
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: color.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            _getQualityIcon(quality),
                            size: 16,
                            color: color,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            '${quality.label} for Hunting',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: color,
                              fontFamily: 'Montserrat',
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          // Hunting tip
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: HitdColors.camolight2,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.tips_and_updates_outlined,
                  size: 20,
                  color: HitdColors.camoGreen,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _getHuntingTip(quality, currentWind),
                    style: TextStyle(
                      fontSize: 12,
                      color: HitdColors.camoGreen,
                      fontFamily: 'Montserrat',
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Hourly forecast
          if (hourlyForecast != null && hourlyForecast!.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text(
              'Hourly Forecast',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                fontFamily: 'Montserrat',
              ),
            ),
            const SizedBox(height: 8),
            SizedBox(
              height: 80,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: hourlyForecast!.length.clamp(0, 12),
                itemBuilder: (context, index) {
                  final data = hourlyForecast![index];
                  return _HourlyWindCard(windData: data);
                },
              ),
            ),
          ],
        ],
      ),
    );
  }

  HuntingWindQuality _getHuntingQuality(double speed) {
    if (speed < 5) return HuntingWindQuality.excellent;
    if (speed < 10) return HuntingWindQuality.good;
    if (speed < 15) return HuntingWindQuality.fair;
    return HuntingWindQuality.poor;
  }

  Color _getQualityColor(HuntingWindQuality quality) {
    switch (quality) {
      case HuntingWindQuality.excellent:
        return HitdColors.green;
      case HuntingWindQuality.good:
        return const Color(0xFF8BC34A);
      case HuntingWindQuality.fair:
        return const Color(0xFFFFC107);
      case HuntingWindQuality.poor:
        return HitdColors.red;
    }
  }

  IconData _getQualityIcon(HuntingWindQuality quality) {
    switch (quality) {
      case HuntingWindQuality.excellent:
        return Icons.check_circle;
      case HuntingWindQuality.good:
        return Icons.thumb_up;
      case HuntingWindQuality.fair:
        return Icons.warning_amber;
      case HuntingWindQuality.poor:
        return Icons.cancel;
    }
  }

  String _getHuntingTip(HuntingWindQuality quality, WindData wind) {
    switch (quality) {
      case HuntingWindQuality.excellent:
        return 'Perfect conditions! Position yourself downwind of game trails.';
      case HuntingWindQuality.good:
        return 'Good hunting wind. Scent will travel ${wind.simpleCardinal} - plan your approach accordingly.';
      case HuntingWindQuality.fair:
        return 'Moderate wind may disperse scent quickly. Consider using scent control.';
      case HuntingWindQuality.poor:
        return 'Strong winds make scent management difficult. Consider waiting for calmer conditions.';
    }
  }
}

/// Hourly wind forecast card
class _HourlyWindCard extends StatelessWidget {
  final WindData windData;

  const _HourlyWindCard({required this.windData});

  @override
  Widget build(BuildContext context) {
    final quality = _getHuntingQuality(windData.speed);
    final color = _getQualityColor(quality);

    return Container(
      width: 60,
      margin: const EdgeInsets.only(right: 8),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Time
          Text(
            _formatHour(windData.time),
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w500,
              fontFamily: 'Montserrat',
            ),
          ),
          const SizedBox(height: 4),
          // Direction arrow
          Transform.rotate(
            angle: windData.direction * math.pi / 180,
            child: Icon(
              Icons.navigation,
              size: 18,
              color: color,
            ),
          ),
          const SizedBox(height: 4),
          // Speed
          Text(
            '${windData.speed.toStringAsFixed(0)}',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w700,
              color: color,
              fontFamily: 'Montserrat',
            ),
          ),
        ],
      ),
    );
  }

  String _formatHour(DateTime time) {
    final hour = time.hour;
    if (hour == 0) return '12am';
    if (hour == 12) return '12pm';
    if (hour > 12) return '${hour - 12}pm';
    return '${hour}am';
  }

  HuntingWindQuality _getHuntingQuality(double speed) {
    if (speed < 5) return HuntingWindQuality.excellent;
    if (speed < 10) return HuntingWindQuality.good;
    if (speed < 15) return HuntingWindQuality.fair;
    return HuntingWindQuality.poor;
  }

  Color _getQualityColor(HuntingWindQuality quality) {
    switch (quality) {
      case HuntingWindQuality.excellent:
        return HitdColors.green;
      case HuntingWindQuality.good:
        return const Color(0xFF8BC34A);
      case HuntingWindQuality.fair:
        return const Color(0xFFFFC107);
      case HuntingWindQuality.poor:
        return HitdColors.red;
    }
  }
}

/// Positioned wind overlay for map integration
/// Place this widget in a Stack with the map
class MapWindOverlay extends StatelessWidget {
  final WindData? currentWind;
  final List<WindData>? hourlyForecast;
  final VoidCallback? onTap;
  final Alignment alignment;
  final EdgeInsets padding;

  const MapWindOverlay({
    super.key,
    this.currentWind,
    this.hourlyForecast,
    this.onTap,
    this.alignment = Alignment.topRight,
    this.padding = const EdgeInsets.all(16),
  });

  @override
  Widget build(BuildContext context) {
    return Positioned.fill(
      child: Align(
        alignment: alignment,
        child: Padding(
          padding: padding,
          child: WindOverlay(
            currentWind: currentWind,
            onTap: onTap,
          ),
        ),
      ),
    );
  }
}
