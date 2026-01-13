/// Information about a public land area.
class PublicLandInfo {
  /// Name of the protected area
  final String? name;

  /// Type of designation (National Forest, BLM, State Park, etc.)
  final String? designation;

  /// Managing agency (USFS, BLM, NPS, State, etc.)
  final String? manager;

  /// GAP Status Code (1-4, indicates protection level)
  final int? gapStatus;

  /// Access level (Open, Restricted, Closed)
  final String? accessLevel;

  /// State code
  final String? state;

  /// Acreage
  final double? acreage;

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
    this.gapStatus,
    this.accessLevel,
    this.state,
    this.acreage,
    this.ownerType,
    this.unitName,
    this.properties = const {},
  });

  /// Create from PAD-US feature properties.
  factory PublicLandInfo.fromProperties(Map<String, dynamic> props) {
    return PublicLandInfo(
      name: _getString(props, ['Unit_Nm', 'UNIT_NM', 'name', 'NAME', 'Loc_Nm']),
      designation: _getString(props, ['Des_Tp', 'DES_TP', 'designation', 'DESIGNATION']),
      manager: _getString(props, ['Mang_Name', 'MANG_NAME', 'manager', 'MANAGER']),
      gapStatus: _getInt(props, ['GAP_Sts', 'GAP_STS', 'gap_status']),
      accessLevel: _getString(props, ['Access', 'ACCESS', 'Pub_Access', 'PUB_ACCESS']),
      state: _getString(props, ['State_Nm', 'STATE_NM', 'state', 'STATE']),
      acreage: _getDouble(props, ['GIS_Acres', 'GIS_ACRES', 'acres', 'ACRES']),
      ownerType: _getString(props, ['Own_Type', 'OWN_TYPE', 'owner_type']),
      unitName: _getString(props, ['Unit_Nm', 'UNIT_NM']),
      properties: props,
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

  static int? _getInt(Map<String, dynamic> props, List<String> keys) {
    for (final key in keys) {
      final value = props[key];
      if (value != null) {
        if (value is int) return value;
        final parsed = int.tryParse(value.toString());
        if (parsed != null) return parsed;
      }
    }
    return null;
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
      case 1:
        return 'Permanent protection, natural state';
      case 2:
        return 'Permanent protection, some use allowed';
      case 3:
        return 'Multiple use, some protection';
      case 4:
        return 'No known mandate for protection';
      default:
        return 'Unknown';
    }
  }

  /// Get a color for this land type.
  int get colorValue {
    final type = designation?.toLowerCase() ?? '';
    final owner = ownerType?.toLowerCase() ?? '';

    if (type.contains('wilderness') || gapStatus == 1) {
      return 0xFF1B5E20; // Dark green
    } else if (type.contains('national forest') || owner.contains('usfs')) {
      return 0xFF4CAF50; // Green
    } else if (type.contains('blm') || owner.contains('blm')) {
      return 0xFFFF9800; // Orange
    } else if (type.contains('state') || owner.contains('state')) {
      return 0xFF2196F3; // Blue
    } else if (type.contains('wildlife') || type.contains('refuge')) {
      return 0xFF8BC34A; // Light green
    } else {
      return 0xFF9E9E9E; // Grey
    }
  }
}
