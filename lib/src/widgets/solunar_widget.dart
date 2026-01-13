import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../services/solunar_service.dart';
import '../utils/colors.dart';

/// Widget displaying solunar information for hunting/fishing.
///
/// Shows moon phase, major/minor periods, and activity rating.
class SolunarCard extends StatelessWidget {
  /// The solunar data to display.
  final SolunarDay solunarDay;

  /// Whether to show detailed period information.
  final bool showDetails;

  /// Callback when the card is tapped.
  final VoidCallback? onTap;

  const SolunarCard({
    super.key,
    required this.solunarDay,
    this.showDetails = true,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            // Header with moon phase and rating
            Row(
              children: [
                _MoonPhaseIndicator(phase: solunarDay.moonPhase),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        solunarDay.moonPhase.phase.displayName,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Text(
                        '${solunarDay.moonPhase.illumination.toStringAsFixed(0)}% illumination',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                ),
                _RatingBadge(rating: solunarDay.dayRating),
              ],
            ),

            if (showDetails) ...[
              const SizedBox(height: 16),
              const Divider(height: 1),
              const SizedBox(height: 16),

              // Periods
              _PeriodsList(
                majorPeriods: solunarDay.majorPeriods,
                minorPeriods: solunarDay.minorPeriods,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Compact solunar indicator for map overlay.
class SolunarOverlay extends StatelessWidget {
  /// Current activity rating (0-100).
  final int rating;

  /// Current moon phase.
  final MoonPhase moonPhase;

  /// Current active period, if any.
  final SolunarPeriod? activePeriod;

  /// Callback when tapped.
  final VoidCallback? onTap;

  const SolunarOverlay({
    super.key,
    required this.rating,
    required this.moonPhase,
    this.activePeriod,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isActive = activePeriod != null;

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
          border: isActive
              ? Border.all(color: HitdColors.green, width: 2)
              : null,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Moon emoji
            Text(
              moonPhase.phase.emoji,
              style: const TextStyle(fontSize: 24),
            ),
            const SizedBox(height: 4),
            // Rating
            Text(
              '$rating',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: _getRatingColor(rating),
              ),
            ),
            // Active period indicator
            if (isActive)
              Container(
                margin: const EdgeInsets.only(top: 4),
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: HitdColors.green.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  activePeriod!.type == SolunarPeriodType.major ? 'MAJOR' : 'MINOR',
                  style: const TextStyle(
                    fontSize: 8,
                    fontWeight: FontWeight.w700,
                    color: HitdColors.green,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Color _getRatingColor(int rating) {
    if (rating >= 80) return HitdColors.green;
    if (rating >= 60) return const Color(0xFF8BC34A);
    if (rating >= 40) return HitdColors.warning;
    return HitdColors.red;
  }
}

/// Moon phase visual indicator.
class _MoonPhaseIndicator extends StatelessWidget {
  final MoonPhase phase;

  const _MoonPhaseIndicator({required this.phase});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 50,
      height: 50,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Colors.grey[900],
      ),
      child: Center(
        child: Text(
          phase.phase.emoji,
          style: const TextStyle(fontSize: 32),
        ),
      ),
    );
  }
}

/// Rating badge with color coding.
class _RatingBadge extends StatelessWidget {
  final int rating;

  const _RatingBadge({required this.rating});

  @override
  Widget build(BuildContext context) {
    final color = _getRatingColor(rating);
    final label = _getRatingLabel(rating);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Text(
            '$rating',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w700,
              color: color,
            ),
          ),
          Text(
            label,
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w500,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Color _getRatingColor(int rating) {
    if (rating >= 80) return HitdColors.green;
    if (rating >= 60) return const Color(0xFF8BC34A);
    if (rating >= 40) return HitdColors.warning;
    return HitdColors.red;
  }

  String _getRatingLabel(int rating) {
    if (rating >= 80) return 'Excellent';
    if (rating >= 60) return 'Good';
    if (rating >= 40) return 'Fair';
    return 'Poor';
  }
}

/// List of solunar periods.
class _PeriodsList extends StatelessWidget {
  final List<SolunarPeriod> majorPeriods;
  final List<SolunarPeriod> minorPeriods;

  const _PeriodsList({
    required this.majorPeriods,
    required this.minorPeriods,
  });

  @override
  Widget build(BuildContext context) {
    final timeFormat = DateFormat('h:mm a');
    final now = DateTime.now();

    // Combine and sort all periods
    final allPeriods = [...majorPeriods, ...minorPeriods]
      ..sort((a, b) => a.start.compareTo(b.start));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Activity Periods',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: Colors.grey,
          ),
        ),
        const SizedBox(height: 8),
        ...allPeriods.map((period) {
          final isActive = now.isAfter(period.start) && now.isBefore(period.end);
          final isPast = now.isAfter(period.end);
          final isMajor = period.type == SolunarPeriodType.major;

          return Container(
            margin: const EdgeInsets.only(bottom: 8),
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: isActive
                  ? HitdColors.green.withOpacity(0.1)
                  : isPast
                      ? Colors.grey.withOpacity(0.05)
                      : Colors.grey.withOpacity(0.05),
              borderRadius: BorderRadius.circular(8),
              border: isActive
                  ? Border.all(color: HitdColors.green, width: 1.5)
                  : null,
            ),
            child: Row(
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isActive
                        ? HitdColors.green
                        : isPast
                            ? Colors.grey
                            : isMajor
                                ? HitdColors.orange
                                : HitdColors.blue,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        period.description,
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: isPast ? Colors.grey : Colors.black87,
                        ),
                      ),
                      Text(
                        '${timeFormat.format(period.start)} - ${timeFormat.format(period.end)}',
                        style: TextStyle(
                          fontSize: 11,
                          color: isPast ? Colors.grey : Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: isMajor
                        ? HitdColors.orange.withOpacity(0.2)
                        : HitdColors.blue.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    isMajor ? 'MAJOR' : 'MINOR',
                    style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                      color: isMajor ? HitdColors.orange : HitdColors.blue,
                    ),
                  ),
                ),
              ],
            ),
          );
        }),
      ],
    );
  }
}

/// Positioned solunar overlay for map integration.
class MapSolunarOverlay extends StatelessWidget {
  final int rating;
  final MoonPhase moonPhase;
  final SolunarPeriod? activePeriod;
  final VoidCallback? onTap;
  final Alignment alignment;
  final EdgeInsets padding;

  const MapSolunarOverlay({
    super.key,
    required this.rating,
    required this.moonPhase,
    this.activePeriod,
    this.onTap,
    this.alignment = Alignment.topLeft,
    this.padding = const EdgeInsets.all(16),
  });

  @override
  Widget build(BuildContext context) {
    return Positioned.fill(
      child: Align(
        alignment: alignment,
        child: Padding(
          padding: padding,
          child: SolunarOverlay(
            rating: rating,
            moonPhase: moonPhase,
            activePeriod: activePeriod,
            onTap: onTap,
          ),
        ),
      ),
    );
  }
}
