/// Houston IT Developers Maps Package
///
/// A comprehensive Flutter mapping toolkit for outdoor/hunting applications.
///
/// ## Features
///
/// - **MapLibre GL Integration**: Vector tile map rendering with PMTiles support
/// - **Solunar Calculator**: Hunting/fishing activity predictions based on moon position
/// - **Wind Overlay**: Real-time wind data visualization with scent cone calculations
/// - **Public Lands**: PAD-US federal and state land boundary layers
/// - **Parcel Data**: Property boundary visualization with owner info
///
/// ## Quick Start
///
/// ```dart
/// import 'package:hitd_maps/hitd_maps.dart';
///
/// // Initialize services
/// final mapService = HitdMapService();
/// final solunar = SolunarService();
/// final wind = WindService();
///
/// // Use the map widget
/// HitdMap(
///   initialPosition: LatLng(30.2672, -97.7431),
///   layers: [
///     HitdMapLayer.parcels,
///     HitdMapLayer.publicLands,
///   ],
///   onMapCreated: (controller) {
///     // Map is ready
///   },
/// )
/// ```
///
/// ## Documentation
///
/// See the [README](https://github.com/Houston-IT-Developers/hitd_maps) for
/// full documentation and examples.
library hitd_maps;

// Core exports
export 'src/hitd_map.dart';
export 'src/hitd_map_controller.dart';
export 'src/hitd_map_config.dart';

// Layer system
export 'src/layers/layers.dart';

// Services
export 'src/services/services.dart';

// Models
export 'src/models/models.dart';

// Widgets
export 'src/widgets/widgets.dart';

// Utils
export 'src/utils/utils.dart';

// Offline support
export 'src/offline/offline.dart';

// Proprietary data layers (premium features)
export 'src/proprietary/proprietary.dart';
