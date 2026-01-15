/// Information about a property parcel.
class ParcelInfo {
  /// Owner name(s)
  final String? ownerName;

  /// Street address
  final String? address;

  /// County name
  final String? county;

  /// State code
  final String? state;

  /// Acreage
  final double? acreage;

  /// Total market value
  final double? marketValue;

  /// Land use code/description
  final String? landUse;

  /// Parcel ID/APN
  final String? parcelId;

  /// Year built (if structure present)
  final int? yearBuilt;

  /// Raw properties from feature
  final Map<String, dynamic> properties;

  ParcelInfo({
    this.ownerName,
    this.address,
    this.county,
    this.state,
    this.acreage,
    this.marketValue,
    this.landUse,
    this.parcelId,
    this.yearBuilt,
    this.properties = const {},
  });

  /// Create from feature properties.
  ///
  /// Handles various property name conventions from different counties.
  factory ParcelInfo.fromProperties(Map<String, dynamic> props) {
    return ParcelInfo(
      ownerName: _getString(props, ['owner_name', 'OWNER', 'owner', 'OWNER_NAME', 'ownername']),
      address: _getString(props, ['situs_addr', 'ADDRESS', 'address', 'SITUS_ADDRESS', 'situsaddr']),
      county: _getString(props, ['county', 'COUNTY', 'COUNTY_NAME']),
      state: _getString(props, ['state', 'STATE', 'STATE_CODE']),
      acreage: _getDouble(props, ['acreage', 'ACRES', 'acres', 'ACREAGE', 'gis_acres']),
      marketValue: _getDouble(props, ['total_market_val', 'MARKET_VALUE', 'market_value', 'TOTAL_VALUE']),
      landUse: _getString(props, ['land_use', 'LAND_USE', 'use_code', 'USE_CODE']),
      parcelId: _getString(props, ['parcel_id', 'PARCEL_ID', 'apn', 'APN', 'PIN', 'PARCEL_NO']),
      yearBuilt: _getInt(props, ['year_built', 'YEAR_BUILT', 'yearbuilt']),
      properties: props,
    );
  }

  /// Create from JSON map.
  factory ParcelInfo.fromJson(Map<String, dynamic> json) {
    return ParcelInfo(
      ownerName: json['ownerName'] as String?,
      address: json['address'] as String?,
      county: json['county'] as String?,
      state: json['state'] as String?,
      acreage: (json['acreage'] as num?)?.toDouble(),
      marketValue: (json['marketValue'] as num?)?.toDouble(),
      landUse: json['landUse'] as String?,
      parcelId: json['parcelId'] as String?,
      yearBuilt: json['yearBuilt'] as int?,
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

  /// Format market value as currency string.
  String? get formattedMarketValue {
    if (marketValue == null) return null;
    if (marketValue! >= 1000000) {
      return '\$${(marketValue! / 1000000).toStringAsFixed(1)}M';
    } else if (marketValue! >= 1000) {
      return '\$${(marketValue! / 1000).toStringAsFixed(0)}K';
    }
    return '\$${marketValue!.toStringAsFixed(0)}';
  }

  /// Format acreage string.
  String? get formattedAcreage {
    if (acreage == null) return null;
    if (acreage! < 1) {
      return '${(acreage! * 43560).toStringAsFixed(0)} sq ft';
    } else if (acreage! >= 100) {
      return '${acreage!.toStringAsFixed(1)} acres';
    }
    return '${acreage!.toStringAsFixed(2)} acres';
  }

  /// Convert to JSON map.
  Map<String, dynamic> toJson() => {
    'ownerName': ownerName,
    'address': address,
    'county': county,
    'state': state,
    'acreage': acreage,
    'marketValue': marketValue,
    'landUse': landUse,
    'parcelId': parcelId,
    'yearBuilt': yearBuilt,
    'properties': properties,
  };

  @override
  String toString() {
    return 'ParcelInfo(owner: $ownerName, address: $address, acres: $acreage)';
  }
}
