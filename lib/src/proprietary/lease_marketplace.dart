import 'dart:async';

import 'package:dio/dio.dart';
import 'package:maplibre_gl/maplibre_gl.dart';

import '../hitd_map_config.dart';

/// Type of hunting lease listing.
enum LeaseType {
  /// Full season lease (exclusive or shared).
  fullSeason,

  /// Day hunting passes.
  dayHunt,

  /// Weekend packages.
  weekend,

  /// Guided hunts with outfitter.
  guided,

  /// Short-term (week/2-week).
  shortTerm,

  /// Multi-year lease.
  multiYear,
}

/// Listing status.
enum LeaseListingStatus {
  /// Active and available.
  available,

  /// Under negotiation.
  pending,

  /// Fully booked/leased.
  leased,

  /// Temporarily unavailable.
  paused,

  /// Listing expired.
  expired,

  /// Draft (not yet published).
  draft,
}

/// Game types available on a property.
class GameAvailability {
  final String gameType;
  final String? population; // 'abundant', 'moderate', 'limited'
  final bool? trophy; // Trophy quality available
  final int? typicalHarvest; // Typical harvest per season
  final String? notes;

  const GameAvailability({
    required this.gameType,
    this.population,
    this.trophy,
    this.typicalHarvest,
    this.notes,
  });

  factory GameAvailability.fromJson(Map<String, dynamic> json) {
    return GameAvailability(
      gameType: json['gameType'] as String,
      population: json['population'] as String?,
      trophy: json['trophy'] as bool?,
      typicalHarvest: json['typicalHarvest'] as int?,
      notes: json['notes'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'gameType': gameType,
    'population': population,
    'trophy': trophy,
    'typicalHarvest': typicalHarvest,
    'notes': notes,
  };
}

/// Property amenities.
enum PropertyAmenity {
  /// Cabin or lodge on property.
  cabin,

  /// RV hookups available.
  rvHookup,

  /// Camping allowed.
  camping,

  /// Electricity available.
  electricity,

  /// Running water.
  water,

  /// Shower facilities.
  shower,

  /// Blinds/stands included.
  blindsStands,

  /// Feeders included.
  feeders,

  /// ATV trails.
  atvTrails,

  /// Pond or lake.
  waterFeature,

  /// Food plots.
  foodPlots,

  /// Butchering/processing area.
  processing,

  /// Walk-in cooler.
  cooler,
}

/// A hunting lease listing.
class LeaseListing {
  /// Unique listing ID.
  final String id;

  /// Listing title.
  final String title;

  /// Detailed description.
  final String description;

  /// Property location (center point).
  final LatLng location;

  /// Property bounds (if available).
  final LatLngBounds? bounds;

  /// County.
  final String county;

  /// State code.
  final String state;

  /// Total acreage.
  final double acreage;

  /// Type of lease.
  final LeaseType leaseType;

  /// Current status.
  final LeaseListingStatus status;

  /// Price.
  final double price;

  /// Price unit ('total', 'perAcre', 'perDay', 'perPerson').
  final String priceUnit;

  /// Maximum number of hunters allowed.
  final int? maxHunters;

  /// Game available on property.
  final List<GameAvailability> gameAvailable;

  /// Property amenities.
  final List<PropertyAmenity> amenities;

  /// Season dates (start).
  final DateTime? seasonStart;

  /// Season dates (end).
  final DateTime? seasonEnd;

  /// Photo URLs.
  final List<String> photos;

  /// Contact name.
  final String? contactName;

  /// Whether contact info is revealed (premium).
  final bool contactRevealed;

  /// Listing owner user ID.
  final String ownerId;

  /// When listing was created.
  final DateTime createdAt;

  /// When listing was last updated.
  final DateTime updatedAt;

  /// Number of views.
  final int viewCount;

  /// Number of inquiries.
  final int inquiryCount;

  /// Rating (1-5 average).
  final double? rating;

  /// Number of reviews.
  final int reviewCount;

  /// Whether this is a verified listing.
  final bool isVerified;

  /// Whether this is a featured/promoted listing.
  final bool isFeatured;

  const LeaseListing({
    required this.id,
    required this.title,
    required this.description,
    required this.location,
    this.bounds,
    required this.county,
    required this.state,
    required this.acreage,
    required this.leaseType,
    required this.status,
    required this.price,
    required this.priceUnit,
    this.maxHunters,
    this.gameAvailable = const [],
    this.amenities = const [],
    this.seasonStart,
    this.seasonEnd,
    this.photos = const [],
    this.contactName,
    this.contactRevealed = false,
    required this.ownerId,
    required this.createdAt,
    required this.updatedAt,
    this.viewCount = 0,
    this.inquiryCount = 0,
    this.rating,
    this.reviewCount = 0,
    this.isVerified = false,
    this.isFeatured = false,
  });

  factory LeaseListing.fromJson(Map<String, dynamic> json) {
    return LeaseListing(
      id: json['id'] as String,
      title: json['title'] as String,
      description: json['description'] as String,
      location: LatLng(
        (json['lat'] as num).toDouble(),
        (json['lng'] as num).toDouble(),
      ),
      bounds: json['bounds'] != null
          ? LatLngBounds(
              southwest: LatLng(
                (json['bounds']['swLat'] as num).toDouble(),
                (json['bounds']['swLng'] as num).toDouble(),
              ),
              northeast: LatLng(
                (json['bounds']['neLat'] as num).toDouble(),
                (json['bounds']['neLng'] as num).toDouble(),
              ),
            )
          : null,
      county: json['county'] as String,
      state: json['state'] as String,
      acreage: (json['acreage'] as num).toDouble(),
      leaseType: LeaseType.values.byName(json['leaseType'] as String),
      status: LeaseListingStatus.values.byName(json['status'] as String),
      price: (json['price'] as num).toDouble(),
      priceUnit: json['priceUnit'] as String,
      maxHunters: json['maxHunters'] as int?,
      gameAvailable: (json['gameAvailable'] as List?)
          ?.map((e) => GameAvailability.fromJson(e as Map<String, dynamic>))
          .toList() ?? [],
      amenities: (json['amenities'] as List?)
          ?.map((e) => PropertyAmenity.values.byName(e as String))
          .toList() ?? [],
      seasonStart: json['seasonStart'] != null
          ? DateTime.parse(json['seasonStart'] as String)
          : null,
      seasonEnd: json['seasonEnd'] != null
          ? DateTime.parse(json['seasonEnd'] as String)
          : null,
      photos: (json['photos'] as List?)?.cast<String>() ?? [],
      contactName: json['contactName'] as String?,
      contactRevealed: json['contactRevealed'] as bool? ?? false,
      ownerId: json['ownerId'] as String,
      createdAt: DateTime.parse(json['createdAt'] as String),
      updatedAt: DateTime.parse(json['updatedAt'] as String),
      viewCount: json['viewCount'] as int? ?? 0,
      inquiryCount: json['inquiryCount'] as int? ?? 0,
      rating: (json['rating'] as num?)?.toDouble(),
      reviewCount: json['reviewCount'] as int? ?? 0,
      isVerified: json['isVerified'] as bool? ?? false,
      isFeatured: json['isFeatured'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'description': description,
    'lat': location.latitude,
    'lng': location.longitude,
    'bounds': bounds != null
        ? {
            'swLat': bounds!.southwest.latitude,
            'swLng': bounds!.southwest.longitude,
            'neLat': bounds!.northeast.latitude,
            'neLng': bounds!.northeast.longitude,
          }
        : null,
    'county': county,
    'state': state,
    'acreage': acreage,
    'leaseType': leaseType.name,
    'status': status.name,
    'price': price,
    'priceUnit': priceUnit,
    'maxHunters': maxHunters,
    'gameAvailable': gameAvailable.map((e) => e.toJson()).toList(),
    'amenities': amenities.map((e) => e.name).toList(),
    'seasonStart': seasonStart?.toIso8601String(),
    'seasonEnd': seasonEnd?.toIso8601String(),
    'photos': photos,
    'contactName': contactName,
    'contactRevealed': contactRevealed,
    'ownerId': ownerId,
    'createdAt': createdAt.toIso8601String(),
    'updatedAt': updatedAt.toIso8601String(),
    'viewCount': viewCount,
    'inquiryCount': inquiryCount,
    'rating': rating,
    'reviewCount': reviewCount,
    'isVerified': isVerified,
    'isFeatured': isFeatured,
  };

  /// Get formatted price string.
  String get formattedPrice {
    final priceStr = price >= 1000
        ? '\$${(price / 1000).toStringAsFixed(1)}K'
        : '\$${price.toStringAsFixed(0)}';

    switch (priceUnit) {
      case 'perAcre':
        return '$priceStr/acre';
      case 'perDay':
        return '$priceStr/day';
      case 'perPerson':
        return '$priceStr/person';
      default:
        return priceStr;
    }
  }

  /// Get game types as comma-separated string.
  String get gameTypesString {
    return gameAvailable.map((g) => g.gameType).join(', ');
  }
}

/// Search filters for lease listings.
class LeaseSearchFilters {
  final double? minAcres;
  final double? maxAcres;
  final double? minPrice;
  final double? maxPrice;
  final List<LeaseType>? leaseTypes;
  final List<String>? gameTypes;
  final List<PropertyAmenity>? requiredAmenities;
  final bool? verifiedOnly;
  final String? sortBy; // 'price', 'acreage', 'rating', 'newest'
  final bool? sortDescending;

  const LeaseSearchFilters({
    this.minAcres,
    this.maxAcres,
    this.minPrice,
    this.maxPrice,
    this.leaseTypes,
    this.gameTypes,
    this.requiredAmenities,
    this.verifiedOnly,
    this.sortBy,
    this.sortDescending,
  });

  Map<String, dynamic> toQueryParams() => {
    if (minAcres != null) 'minAcres': minAcres,
    if (maxAcres != null) 'maxAcres': maxAcres,
    if (minPrice != null) 'minPrice': minPrice,
    if (maxPrice != null) 'maxPrice': maxPrice,
    if (leaseTypes != null) 'leaseTypes': leaseTypes!.map((e) => e.name).join(','),
    if (gameTypes != null) 'gameTypes': gameTypes!.join(','),
    if (requiredAmenities != null)
      'amenities': requiredAmenities!.map((e) => e.name).join(','),
    if (verifiedOnly != null) 'verifiedOnly': verifiedOnly,
    if (sortBy != null) 'sortBy': sortBy,
    if (sortDescending != null) 'sortDesc': sortDescending,
  };
}

/// Service for the hunting lease marketplace.
///
/// Connects hunters with landowners offering hunting access.
///
/// ## Revenue Model
///
/// - Free to browse listings
/// - Contact info requires premium subscription
/// - Listing owners can promote for visibility
/// - Transaction fees on completed leases (optional)
///
/// ## Usage
///
/// ```dart
/// final marketplace = LeaseMarketplaceService();
///
/// // Search for leases
/// final listings = await marketplace.searchListings(
///   bounds: myBounds,
///   filters: LeaseSearchFilters(
///     minAcres: 100,
///     gameTypes: ['Whitetail Deer'],
///   ),
/// );
///
/// // Get listing details
/// final details = await marketplace.getListingDetails('listing123');
///
/// // Send inquiry (requires premium)
/// await marketplace.sendInquiry(
///   listingId: 'listing123',
///   message: 'Interested in your property...',
/// );
/// ```
class LeaseMarketplaceService {
  static LeaseMarketplaceService? _instance;

  /// Get singleton instance.
  static LeaseMarketplaceService get instance {
    _instance ??= LeaseMarketplaceService._();
    return _instance!;
  }

  LeaseMarketplaceService._();

  final Dio _dio = Dio();

  /// Base URL for marketplace API.
  String apiBaseUrl = 'https://api.gspotoutdoors.com/v1/marketplace';

  /// Search for lease listings.
  Future<List<LeaseListing>> searchListings({
    required LatLngBounds bounds,
    LeaseSearchFilters? filters,
    int page = 1,
    int limit = 20,
  }) async {
    try {
      final queryParams = {
        'minLat': bounds.southwest.latitude,
        'minLng': bounds.southwest.longitude,
        'maxLat': bounds.northeast.latitude,
        'maxLng': bounds.northeast.longitude,
        'page': page,
        'limit': limit,
        ...?filters?.toQueryParams(),
      };

      final response = await _dio.get(
        '$apiBaseUrl/listings',
        queryParameters: queryParams,
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data['listings'];
        return data
            .map((json) => LeaseListing.fromJson(json as Map<String, dynamic>))
            .toList();
      }
      return [];
    } catch (e) {
      _log('Error searching listings: $e');
      return [];
    }
  }

  /// Get featured/promoted listings.
  Future<List<LeaseListing>> getFeaturedListings({
    String? state,
    int limit = 10,
  }) async {
    try {
      final response = await _dio.get(
        '$apiBaseUrl/featured',
        queryParameters: {
          if (state != null) 'state': state,
          'limit': limit,
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data['listings'];
        return data
            .map((json) => LeaseListing.fromJson(json as Map<String, dynamic>))
            .toList();
      }
      return [];
    } catch (e) {
      _log('Error getting featured listings: $e');
      return [];
    }
  }

  /// Get detailed listing information.
  ///
  /// Increments view count.
  Future<LeaseListing?> getListingDetails(String listingId) async {
    try {
      final response = await _dio.get('$apiBaseUrl/listings/$listingId');

      if (response.statusCode == 200) {
        return LeaseListing.fromJson(response.data as Map<String, dynamic>);
      }
      return null;
    } catch (e) {
      _log('Error getting listing details: $e');
      return null;
    }
  }

  /// Reveal contact info (requires premium subscription).
  ///
  /// Returns contact details if user has access.
  Future<Map<String, String>?> revealContactInfo(String listingId) async {
    try {
      final response = await _dio.post('$apiBaseUrl/listings/$listingId/reveal');

      if (response.statusCode == 200) {
        return (response.data['contact'] as Map<String, dynamic>)
            .cast<String, String>();
      }
      return null;
    } catch (e) {
      _log('Error revealing contact: $e');
      return null;
    }
  }

  /// Send inquiry to listing owner.
  ///
  /// Requires premium subscription.
  Future<bool> sendInquiry({
    required String listingId,
    required String message,
    String? phone,
    String? email,
  }) async {
    try {
      final response = await _dio.post(
        '$apiBaseUrl/listings/$listingId/inquire',
        data: {
          'message': message,
          if (phone != null) 'phone': phone,
          if (email != null) 'email': email,
        },
      );

      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      _log('Error sending inquiry: $e');
      return false;
    }
  }

  /// Save a listing to favorites.
  Future<bool> saveListing(String listingId) async {
    try {
      final response = await _dio.post('$apiBaseUrl/listings/$listingId/save');
      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      _log('Error saving listing: $e');
      return false;
    }
  }

  /// Get user's saved listings.
  Future<List<LeaseListing>> getSavedListings() async {
    try {
      final response = await _dio.get('$apiBaseUrl/saved');

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data['listings'];
        return data
            .map((json) => LeaseListing.fromJson(json as Map<String, dynamic>))
            .toList();
      }
      return [];
    } catch (e) {
      _log('Error getting saved listings: $e');
      return [];
    }
  }

  /// Create a new listing (for landowners).
  Future<String?> createListing(LeaseListing listing) async {
    try {
      final response = await _dio.post(
        '$apiBaseUrl/listings',
        data: listing.toJson(),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return response.data['id'] as String;
      }
      return null;
    } catch (e) {
      _log('Error creating listing: $e');
      return null;
    }
  }

  /// Update an existing listing.
  Future<bool> updateListing(String listingId, Map<String, dynamic> updates) async {
    try {
      final response = await _dio.patch(
        '$apiBaseUrl/listings/$listingId',
        data: updates,
      );

      return response.statusCode == 200;
    } catch (e) {
      _log('Error updating listing: $e');
      return false;
    }
  }

  /// Get listings created by current user.
  Future<List<LeaseListing>> getMyListings() async {
    try {
      final response = await _dio.get('$apiBaseUrl/my-listings');

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data['listings'];
        return data
            .map((json) => LeaseListing.fromJson(json as Map<String, dynamic>))
            .toList();
      }
      return [];
    } catch (e) {
      _log('Error getting my listings: $e');
      return [];
    }
  }

  /// Get marketplace statistics.
  Future<Map<String, dynamic>?> getMarketplaceStats({String? state}) async {
    try {
      final response = await _dio.get(
        '$apiBaseUrl/stats',
        queryParameters: {
          if (state != null) 'state': state,
        },
      );

      if (response.statusCode == 200) {
        return response.data as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      _log('Error getting marketplace stats: $e');
      return null;
    }
  }

  void _log(String message) {
    if (HitdMapConfig.isInitialized && HitdMapConfig.instance.debugMode) {
      // ignore: avoid_print
      print('[LeaseMarketplaceService] $message');
    }
  }
}
