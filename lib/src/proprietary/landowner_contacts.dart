import 'dart:async';

import 'package:dio/dio.dart';
import 'package:maplibre_gl/maplibre_gl.dart';

import '../hitd_map_config.dart';

/// Contact status for a landowner.
enum LandownerContactStatus {
  /// Not yet contacted.
  notContacted,

  /// Contact attempted but no response.
  noResponse,

  /// Interested in discussion.
  interested,

  /// Not interested in leasing.
  notInterested,

  /// Active lease in place.
  activeAgreement,

  /// Previously had agreement, now expired.
  expired,
}

/// Type of hunting access.
enum HuntingAccessType {
  /// Full season lease.
  fullLease,

  /// Day hunting only.
  dayHunt,

  /// Weekend access.
  weekend,

  /// Guided hunts only.
  guided,

  /// Trade/barter arrangement.
  trade,

  /// Free access (rare).
  free,
}

/// Information about a landowner and their property.
class LandownerContact {
  /// Unique identifier.
  final String id;

  /// Parcel ID(s) associated with this landowner.
  final List<String> parcelIds;

  /// Owner name (from public records).
  final String ownerName;

  /// Property location.
  final LatLng location;

  /// Total acreage owned.
  final double? totalAcres;

  /// County.
  final String county;

  /// State code.
  final String state;

  /// Mailing address (from public records).
  final String? mailingAddress;

  /// Contact status.
  final LandownerContactStatus status;

  /// Types of access they may offer.
  final List<HuntingAccessType> accessTypes;

  /// Game types on property.
  final List<String> gameTypes;

  /// Estimated lease price per acre (if known).
  final double? pricePerAcre;

  /// Additional notes (private to user).
  final String? notes;

  /// Last contact attempt date.
  final DateTime? lastContactDate;

  /// When this record was last updated.
  final DateTime updatedAt;

  /// User ID who added this contact.
  final String? addedByUserId;

  /// Whether this is verified information.
  final bool isVerified;

  const LandownerContact({
    required this.id,
    required this.parcelIds,
    required this.ownerName,
    required this.location,
    this.totalAcres,
    required this.county,
    required this.state,
    this.mailingAddress,
    this.status = LandownerContactStatus.notContacted,
    this.accessTypes = const [],
    this.gameTypes = const [],
    this.pricePerAcre,
    this.notes,
    this.lastContactDate,
    required this.updatedAt,
    this.addedByUserId,
    this.isVerified = false,
  });

  factory LandownerContact.fromJson(Map<String, dynamic> json) {
    return LandownerContact(
      id: json['id'] as String,
      parcelIds: (json['parcelIds'] as List).cast<String>(),
      ownerName: json['ownerName'] as String,
      location: LatLng(
        (json['lat'] as num).toDouble(),
        (json['lng'] as num).toDouble(),
      ),
      totalAcres: (json['totalAcres'] as num?)?.toDouble(),
      county: json['county'] as String,
      state: json['state'] as String,
      mailingAddress: json['mailingAddress'] as String?,
      status: LandownerContactStatus.values.byName(
        json['status'] as String? ?? 'notContacted',
      ),
      accessTypes: (json['accessTypes'] as List?)
          ?.map((e) => HuntingAccessType.values.byName(e as String))
          .toList() ?? [],
      gameTypes: (json['gameTypes'] as List?)?.cast<String>() ?? [],
      pricePerAcre: (json['pricePerAcre'] as num?)?.toDouble(),
      notes: json['notes'] as String?,
      lastContactDate: json['lastContactDate'] != null
          ? DateTime.parse(json['lastContactDate'] as String)
          : null,
      updatedAt: DateTime.parse(json['updatedAt'] as String),
      addedByUserId: json['addedByUserId'] as String?,
      isVerified: json['isVerified'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'parcelIds': parcelIds,
    'ownerName': ownerName,
    'lat': location.latitude,
    'lng': location.longitude,
    'totalAcres': totalAcres,
    'county': county,
    'state': state,
    'mailingAddress': mailingAddress,
    'status': status.name,
    'accessTypes': accessTypes.map((e) => e.name).toList(),
    'gameTypes': gameTypes,
    'pricePerAcre': pricePerAcre,
    'notes': notes,
    'lastContactDate': lastContactDate?.toIso8601String(),
    'updatedAt': updatedAt.toIso8601String(),
    'addedByUserId': addedByUserId,
    'isVerified': isVerified,
  };

  /// Create a copy with updated fields.
  LandownerContact copyWith({
    LandownerContactStatus? status,
    List<HuntingAccessType>? accessTypes,
    List<String>? gameTypes,
    double? pricePerAcre,
    String? notes,
    DateTime? lastContactDate,
  }) {
    return LandownerContact(
      id: id,
      parcelIds: parcelIds,
      ownerName: ownerName,
      location: location,
      totalAcres: totalAcres,
      county: county,
      state: state,
      mailingAddress: mailingAddress,
      status: status ?? this.status,
      accessTypes: accessTypes ?? this.accessTypes,
      gameTypes: gameTypes ?? this.gameTypes,
      pricePerAcre: pricePerAcre ?? this.pricePerAcre,
      notes: notes ?? this.notes,
      lastContactDate: lastContactDate ?? this.lastContactDate,
      updatedAt: DateTime.now(),
      addedByUserId: addedByUserId,
      isVerified: isVerified,
    );
  }

  /// Get display color based on status.
  int get statusColor {
    switch (status) {
      case LandownerContactStatus.notContacted:
        return 0xFF9E9E9E; // Grey
      case LandownerContactStatus.noResponse:
        return 0xFFFFEB3B; // Yellow
      case LandownerContactStatus.interested:
        return 0xFF4CAF50; // Green
      case LandownerContactStatus.notInterested:
        return 0xFFF44336; // Red
      case LandownerContactStatus.activeAgreement:
        return 0xFF2196F3; // Blue
      case LandownerContactStatus.expired:
        return 0xFFFF9800; // Orange
    }
  }
}

/// Service for managing landowner contact information.
///
/// This is the premium differentiator - helps hunters find and
/// manage relationships with landowners for hunting access.
///
/// ## Privacy Note
///
/// All landowner information comes from public property records.
/// Contact information is derived from tax records which are
/// public data in most US states.
///
/// ## Usage
///
/// ```dart
/// final service = LandownerContactService();
///
/// // Search for landowners in an area
/// final contacts = await service.searchLandowners(
///   bounds: myBounds,
///   minAcres: 100,
/// );
///
/// // Update contact status
/// await service.updateContactStatus(
///   contactId: 'abc123',
///   status: LandownerContactStatus.interested,
///   notes: 'Spoke with owner, interested in day hunting',
/// );
/// ```
class LandownerContactService {
  static LandownerContactService? _instance;

  /// Get singleton instance.
  static LandownerContactService get instance {
    _instance ??= LandownerContactService._();
    return _instance!;
  }

  LandownerContactService._();

  final Dio _dio = Dio();

  /// Base URL for landowner API.
  String apiBaseUrl = 'https://api.gspotoutdoors.com/v1/landowners';

  /// Search for landowners within bounds.
  ///
  /// Filters by minimum acreage, status, and other criteria.
  Future<List<LandownerContact>> searchLandowners({
    required LatLngBounds bounds,
    double? minAcres,
    double? maxAcres,
    LandownerContactStatus? status,
    List<String>? gameTypes,
    int limit = 100,
  }) async {
    try {
      final response = await _dio.get(
        '$apiBaseUrl/search',
        queryParameters: {
          'minLat': bounds.southwest.latitude,
          'minLng': bounds.southwest.longitude,
          'maxLat': bounds.northeast.latitude,
          'maxLng': bounds.northeast.longitude,
          if (minAcres != null) 'minAcres': minAcres,
          if (maxAcres != null) 'maxAcres': maxAcres,
          if (status != null) 'status': status.name,
          if (gameTypes != null) 'gameTypes': gameTypes.join(','),
          'limit': limit,
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data['contacts'];
        return data
            .map((json) => LandownerContact.fromJson(json as Map<String, dynamic>))
            .toList();
      }
      return [];
    } catch (e) {
      _log('Error searching landowners: $e');
      return [];
    }
  }

  /// Get landowner info for a specific parcel.
  Future<LandownerContact?> getByParcelId(String parcelId) async {
    try {
      final response = await _dio.get('$apiBaseUrl/parcel/$parcelId');

      if (response.statusCode == 200 && response.data != null) {
        return LandownerContact.fromJson(response.data as Map<String, dynamic>);
      }
      return null;
    } catch (e) {
      _log('Error getting landowner by parcel: $e');
      return null;
    }
  }

  /// Update contact status and notes.
  ///
  /// This is user-specific - each user maintains their own
  /// contact status with landowners.
  Future<bool> updateContactStatus({
    required String contactId,
    LandownerContactStatus? status,
    String? notes,
    List<HuntingAccessType>? accessTypes,
    double? pricePerAcre,
  }) async {
    try {
      final response = await _dio.patch(
        '$apiBaseUrl/$contactId',
        data: {
          if (status != null) 'status': status.name,
          if (notes != null) 'notes': notes,
          if (accessTypes != null) 'accessTypes': accessTypes.map((e) => e.name).toList(),
          if (pricePerAcre != null) 'pricePerAcre': pricePerAcre,
          'lastContactDate': DateTime.now().toIso8601String(),
        },
      );

      return response.statusCode == 200;
    } catch (e) {
      _log('Error updating contact: $e');
      return false;
    }
  }

  /// Log a contact attempt.
  Future<bool> logContactAttempt({
    required String contactId,
    required String method, // 'phone', 'mail', 'inPerson', 'email'
    required String outcome,
    String? notes,
  }) async {
    try {
      final response = await _dio.post(
        '$apiBaseUrl/$contactId/attempts',
        data: {
          'method': method,
          'outcome': outcome,
          'notes': notes,
          'timestamp': DateTime.now().toIso8601String(),
        },
      );

      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      _log('Error logging contact attempt: $e');
      return false;
    }
  }

  /// Get user's saved contacts (bookmarked landowners).
  Future<List<LandownerContact>> getSavedContacts() async {
    try {
      final response = await _dio.get('$apiBaseUrl/saved');

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data['contacts'];
        return data
            .map((json) => LandownerContact.fromJson(json as Map<String, dynamic>))
            .toList();
      }
      return [];
    } catch (e) {
      _log('Error getting saved contacts: $e');
      return [];
    }
  }

  /// Save a contact to user's list.
  Future<bool> saveContact(String contactId) async {
    try {
      final response = await _dio.post('$apiBaseUrl/$contactId/save');
      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      _log('Error saving contact: $e');
      return false;
    }
  }

  /// Remove a contact from user's saved list.
  Future<bool> unsaveContact(String contactId) async {
    try {
      final response = await _dio.delete('$apiBaseUrl/$contactId/save');
      return response.statusCode == 200 || response.statusCode == 204;
    } catch (e) {
      _log('Error unsaving contact: $e');
      return false;
    }
  }

  /// Generate letter template for contacting landowner.
  String generateContactLetter({
    required LandownerContact contact,
    required String senderName,
    required String senderAddress,
    required String senderPhone,
    bool includePriceOffer = false,
    double? priceOffer,
  }) {
    final date = DateTime.now();
    final dateStr = '${date.month}/${date.day}/${date.year}';

    return '''
$senderName
$senderAddress
$senderPhone

$dateStr

${contact.ownerName}
${contact.mailingAddress ?? '[Address from Tax Records]'}

Dear ${contact.ownerName.split(' ').first},

I am writing to inquire about the possibility of obtaining hunting access to your property in ${contact.county} County, ${contact.state}. I am an experienced hunter who respects both the land and private property rights.

${contact.totalAcres != null ? 'I understand you own approximately ${contact.totalAcres!.toStringAsFixed(0)} acres in the area. ' : ''}I would be interested in discussing a hunting lease arrangement for the upcoming season.

I am a responsible, ethical hunter with ${includePriceOffer && priceOffer != null ? 'a budget of approximately \$${priceOffer.toStringAsFixed(0)} per acre annually' : 'flexible lease terms'}. I carry full liability insurance, always follow game laws, and treat properties with the utmost respect.

If you might be interested in discussing hunting access on any of your land, I would welcome the opportunity to meet in person or speak by phone at your convenience.

Thank you for your time and consideration.

Sincerely,

$senderName
$senderPhone
''';
  }

  void _log(String message) {
    if (HitdMapConfig.isInitialized && HitdMapConfig.instance.debugMode) {
      // ignore: avoid_print
      print('[LandownerContactService] $message');
    }
  }
}
