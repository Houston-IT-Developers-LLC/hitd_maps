import 'package:flutter/material.dart';

/// Default colors for HITD Maps widgets.
///
/// These can be overridden by passing custom colors to widgets.
class HitdColors {
  HitdColors._();

  // Primary colors
  static const Color primary = Color(0xFF4CAF50);
  static const Color primaryDark = Color(0xFF2E7D32);

  // Status colors
  static const Color success = Color(0xFF4CAF50);
  static const Color warning = Color(0xFFFFC107);
  static const Color error = Color(0xFFE53935);
  static const Color info = Color(0xFF2196F3);

  // Hunting-specific colors
  static const Color green = Color(0xFF4CAF50);
  static const Color red = Color(0xFFE53935);
  static const Color orange = Color(0xFFFF9800);
  static const Color blue = Color(0xFF2196F3);

  // Camo theme colors
  static const Color camoGreen = Color(0xFF556B2F);
  static const Color camoLight = Color(0xFF8FBC8F);
  static const Color camoLight2 = Color(0xFFE8F5E9);
  static const Color camoBrown = Color(0xFF8B4513);

  // Layer colors
  static const Color parcels = Color(0xFFE53935);
  static const Color parcelsOutline = Color(0xFFB71C1C);
  static const Color publicLands = Color(0xFF4CAF50);
  static const Color blmLands = Color(0xFFFF9800);
  static const Color usfsLands = Color(0xFF4CAF50);
  static const Color stateLands = Color(0xFF2196F3);
  static const Color wetlands = Color(0xFF2196F3);
  static const Color wma = Color(0xFF8BC34A);

  // Wind quality colors
  static const Color windExcellent = Color(0xFF4CAF50);
  static const Color windGood = Color(0xFF8BC34A);
  static const Color windFair = Color(0xFFFFC107);
  static const Color windPoor = Color(0xFFE53935);
}
