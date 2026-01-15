/// Proprietary data layers for HITD Maps.
///
/// These features provide unique value that differentiates
/// the hitd_maps package from competitors:
///
/// - **Hunting Pressure**: Crowdsourced hunting pressure data
/// - **Landowner Contacts**: Database of landowners from public records
/// - **Lease Marketplace**: Hunting lease listings and transactions
///
/// ## Business Model
///
/// These features support a freemium model:
///
/// **Free Tier:**
/// - View pressure heatmaps
/// - Browse lease listings
/// - Basic parcel info
///
/// **Premium Tier:**
/// - Detailed pressure analytics
/// - Landowner contact info
/// - Contact reveal on listings
/// - Priority support
///
/// ## Usage
///
/// ```dart
/// import 'package:hitd_maps/hitd_maps.dart';
///
/// // Hunting pressure
/// final pressureService = HuntingPressureService.instance;
/// final pressureData = await pressureService.getPressureData(bounds: myBounds);
///
/// // Landowner contacts
/// final landownerService = LandownerContactService.instance;
/// final contacts = await landownerService.searchLandowners(bounds: myBounds);
///
/// // Lease marketplace
/// final marketplace = LeaseMarketplaceService.instance;
/// final listings = await marketplace.searchListings(bounds: myBounds);
/// ```
library;

export 'hunting_pressure.dart';
export 'landowner_contacts.dart';
export 'lease_marketplace.dart';
