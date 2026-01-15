import 'package:flutter/material.dart';

/// Types of public land.
enum PublicLandType {
  blm,
  nationalForest,
  nationalPark,
  fishAndWildlife,
  state,
  local,
  other;

  /// Human-readable display name.
  String get displayName {
    switch (this) {
      case PublicLandType.blm:
        return 'BLM Land';
      case PublicLandType.nationalForest:
        return 'National Forest';
      case PublicLandType.nationalPark:
        return 'National Park';
      case PublicLandType.fishAndWildlife:
        return 'Fish & Wildlife';
      case PublicLandType.state:
        return 'State Land';
      case PublicLandType.local:
        return 'Local/County';
      case PublicLandType.other:
        return 'Other Public';
    }
  }

  /// Color for this land type.
  Color get color {
    switch (this) {
      case PublicLandType.blm:
        return const Color(0xFFFF9800); // Orange
      case PublicLandType.nationalForest:
        return const Color(0xFF4CAF50); // Green
      case PublicLandType.nationalPark:
        return const Color(0xFF8BC34A); // Light green
      case PublicLandType.fishAndWildlife:
        return const Color(0xFF00BCD4); // Cyan
      case PublicLandType.state:
        return const Color(0xFF2196F3); // Blue
      case PublicLandType.local:
        return const Color(0xFF9C27B0); // Purple
      case PublicLandType.other:
        return const Color(0xFF9E9E9E); // Grey
    }
  }
}

/// Information about a public land area.
class PublicLandInfo {
  /// Name of the protected area
  final String? name;

  /// Type of designation (National Forest, BLM, State Park, etc.)
  final String? designation;

  /// Managing agency (USFS, BLM, NPS, State, etc.)
  final String? manager;

  /// Manager type (FED, STAT, LOC, etc.)
  final String? managerType;

  /// GAP Status Code (1-4, indicates protection level)
  final String? gapStatus;

  /// Access level (Open, Restricted, Closed)
  final String? accessLevel;

  /// State code
  final String? state;

  /// Acreage
  final double? acres;

  /// Owner type (Federal, State, Local, Private Conservation)
  final String? ownerType;

  /// Unit name (Ranger District, etc.)
  final String? unitName;

  /// Raw properties from feature
  final Map<String, dynamic> properties;

  PublicLandInfo({
    this.name,
    this.designation,
    this.manager,
    this.managerType,
    this.gapStatus,
    this.accessLevel,
    this.state,
    this.acres,
    this.ownerType,
    this.unitName,
    this.properties = const {},
  });

  /// Create from PAD-US feature properties.
  factory PublicLandInfo.fromProperties(Map<String, dynamic> props) {
    return PublicLandInfo(
      name: _getString(props, ['Unit_Nm', 'UNIT_NM', 'name', 'NAME', 'Loc_Nm']),
      designation: _getString(props, ['Des_Tp', 'DES_TP', 'designation', 'DESIGNATION']),
      manager: _getString(props, ['Mang_Name', 'MANG_NAME', 'manager', 'MANAGER', 'AGENCY']),
      managerType: _getString(props, ['Mang_Type', 'MANG_TYPE', 'TYPE']),
      gapStatus: _getString(props, ['GAP_Sts', 'GAP_STS', 'gap_status']),
      accessLevel: _getString(props, ['Access', 'ACCESS', 'Pub_Access', 'PUB_ACCESS']),
      state: _getString(props, ['State_Nm', 'STATE_NM', 'state', 'STATE']),
      acres: _getDouble(props, ['GIS_Acres', 'GIS_ACRES', 'acres', 'ACRES']),
      ownerType: _getString(props, ['Own_Type', 'OWN_TYPE', 'owner_type']),
      unitName: _getString(props, ['Unit_Nm', 'UNIT_NM']),
      properties: props,
    );
  }

  /// Create from JSON map.
  factory PublicLandInfo.fromJson(Map<String, dynamic> json) {
    return PublicLandInfo(
      name: json['name'] as String?,
      designation: json['designation'] as String?,
      manager: json['manager'] as String?,
      managerType: json['managerType'] as String?,
      gapStatus: json['gapStatus'] as String?,
      accessLevel: json['accessLevel'] as String?,
      state: json['state'] as String?,
      acres: (json['acres'] as num?)?.toDouble(),
      ownerType: json['ownerType'] as String?,
      unitName: json['unitName'] as String?,
      properties: json['properties'] as Map<String, dynamic>? ?? {},
    );
  }

  static String? _getString(Map<String, dynamic> props, List<String> keys) {
    for (final key in keys) {
      final value = props[key];
      if (value != null && value.toString().isNotEmpty) {
        return value.toString();
      }
    }
    return null;
  }

  static double? _getDouble(Map<String, dynamic> props, List<String> keys) {
    for (final key in keys) {
      final value = props[key];
      if (value != null) {
        if (value is num) return value.toDouble();
        final parsed = double.tryParse(value.toString());
        if (parsed != null) return parsed;
      }
    }
    return null;
  }

  /// Get the land type based on manager and designation.
  PublicLandType get landType {
    final mgr = manager?.toUpperCase() ?? '';
    final mgrType = managerType?.toUpperCase() ?? '';

    if (mgr.contains('BLM') || mgr == 'BUREAU OF LAND MANAGEMENT') {
      return PublicLandType.blm;
    } else if (mgr.contains('USFS') || mgr.contains('FOREST SERVICE')) {
      return PublicLandType.nationalForest;
    } else if (mgr.contains('NPS') || mgr.contains('NATIONAL PARK')) {
      return PublicLandType.nationalPark;
    } else if (mgr.contains('FWS') || mgr.contains('FISH') || mgr.contains('WILDLIFE')) {
      return PublicLandType.fishAndWildlife;
    } else if (mgrType.contains('STAT') || mgrType == 'STATE') {
      return PublicLandType.state;
    } else if (mgrType.contains('LOC') || mgrType == 'LOCAL') {
      return PublicLandType.local;
    }
    return PublicLandType.other;
  }

  /// Whether hunting is typically allowed on this land type.
  bool get isHuntingAllowed {
    switch (landType) {
      case PublicLandType.blm:
      case PublicLandType.nationalForest:
      case PublicLandType.fishAndWildlife:
      case PublicLandType.state:
        return true;
      case PublicLandType.nationalPark:
        return false;
      case PublicLandType.local:
      case PublicLandType.other:
        return false; // Usually not, but varies
    }
  }

  /// Whether this land is publicly accessible.
  bool get isPubliclyAccessible {
    if (accessLevel == null) return true;
    final lower = accessLevel!.toLowerCase();
    return !lower.contains('closed') && !lower.contains('restricted');
  }

  /// Human-readable description of GAP status.
  String? get gapStatusDescription {
    if (gapStatus == null) return null;
    switch (gapStatus) {
      case '1':
        return 'Permanent protection, natural state';
      case '2':
        return 'Permanent protection, some use allowed';
      case '3':
        return 'Multiple use, some protection';
      case '4':
        return 'No known mandate for protection';
      default:
        return 'Unknown';
    }
  }

  /// Format acres for display.
  String? get formattedAcres {
    if (acres == null) return null;
    if (acres! >= 1000) {
      return '${(acres! / 1000).toStringAsFixed(1)}K acres';
    }
    return '${acres!.toStringAsFixed(0)} acres';
  }

  /// Get a color for this land type (as int).
  int get colorValue {
    return landType.color.value;
  }

  /// Convert to JSON map.
  Map<String, dynamic> toJson() => {
    'name': name,
    'designation': designation,
    'manager': manager,
    'managerType': managerType,
    'gapStatus': gapStatus,
    'accessLevel': accessLevel,
    'state': state,
    'acres': acres,
    'ownerType': ownerType,
    'unitName': unitName,
    'properties': properties,
  };

  @override
  String toString() {
    return 'PublicLandInfo(name: $name, manager: $manager, acres: $acres)';
  }
}
