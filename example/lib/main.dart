import 'package:flutter/material.dart';
import 'package:hitd_maps/hitd_maps.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize HITD Maps configuration
  // Option 1: Use preset configuration
  HitdMapPresets.useGSpotOutdoors(debugMode: true);

  // Option 2: Custom configuration
  // HitdMapConfig.initialize(
  //   pmtilesBaseUrl: 'https://your-cdn.com/tiles',
  //   basemapStyleUrl: 'https://demotiles.maplibre.org/style.json',
  //   debugMode: true,
  // );

  runApp(const HitdMapsExampleApp());
}

class HitdMapsExampleApp extends StatelessWidget {
  const HitdMapsExampleApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'HITD Maps Example',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
        useMaterial3: true,
      ),
      home: const MapExampleScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class MapExampleScreen extends StatefulWidget {
  const MapExampleScreen({super.key});

  @override
  State<MapExampleScreen> createState() => _MapExampleScreenState();
}

class _MapExampleScreenState extends State<MapExampleScreen> {
  HitdMapController? _controller;
  final SolunarService _solunarService = SolunarService();

  // Example location: Austin, TX
  static const _austinLocation = LatLng(30.2672, -97.7431);

  // Layer visibility state
  bool _parcelsVisible = true;
  bool _publicLandsVisible = false;

  // Current solunar data
  SolunarDay? _solunarDay;
  int _currentRating = 0;

  @override
  void initState() {
    super.initState();
    _loadSolunarData();
  }

  void _loadSolunarData() {
    _solunarDay = _solunarService.getSolunarDay(
      _austinLocation.latitude,
      _austinLocation.longitude,
      DateTime.now(),
    );
    _currentRating = _solunarService.getCurrentRating(
      _austinLocation.latitude,
      _austinLocation.longitude,
    );
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('HITD Maps Demo'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: _showSolunarInfo,
            tooltip: 'Solunar Info',
          ),
        ],
      ),
      body: Stack(
        children: [
          // Main map
          HitdMap(
            initialPosition: _austinLocation,
            initialZoom: 12.0,
            layers: [
              HitdMapLayer.parcels(visible: _parcelsVisible),
              HitdMapLayer.publicLands(visible: _publicLandsVisible),
            ],
            onMapCreated: (controller) {
              setState(() => _controller = controller);
            },
            onTap: (latLng) {
              _showLocationInfo(latLng);
            },
            onFeatureTap: (latLng, properties) {
              if (properties != null) {
                _showFeatureInfo(latLng, properties);
              }
            },
          ),

          // Solunar rating badge
          Positioned(
            top: 16,
            left: 16,
            child: _buildSolunarBadge(),
          ),

          // Layer controls
          Positioned(
            top: 16,
            right: 16,
            child: _buildLayerControls(),
          ),
        ],
      ),
      floatingActionButton: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          FloatingActionButton.small(
            heroTag: 'zoom_in',
            onPressed: () => _controller?.zoomIn(),
            child: const Icon(Icons.add),
          ),
          const SizedBox(height: 8),
          FloatingActionButton.small(
            heroTag: 'zoom_out',
            onPressed: () => _controller?.zoomOut(),
            child: const Icon(Icons.remove),
          ),
          const SizedBox(height: 8),
          FloatingActionButton(
            heroTag: 'my_location',
            onPressed: _goToAustin,
            child: const Icon(Icons.my_location),
          ),
        ],
      ),
    );
  }

  Widget _buildSolunarBadge() {
    final Color ratingColor;
    if (_currentRating >= 75) {
      ratingColor = Colors.green;
    } else if (_currentRating >= 50) {
      ratingColor = Colors.orange;
    } else {
      ratingColor = Colors.red;
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              _solunarDay?.moonPhase.phase.emoji ?? '',
              style: const TextStyle(fontSize: 24),
            ),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: ratingColor.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '$_currentRating',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: ratingColor,
                ),
              ),
            ),
            const SizedBox(height: 4),
            Text(
              _solunarDay?.ratingDescription ?? '',
              style: const TextStyle(fontSize: 10),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLayerControls() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildLayerToggle(
              'Parcels',
              _parcelsVisible,
              Colors.red,
              (value) {
                setState(() => _parcelsVisible = value);
                _controller?.setLayerVisibility('parcels', value);
              },
            ),
            _buildLayerToggle(
              'Public Lands',
              _publicLandsVisible,
              Colors.green,
              (value) {
                setState(() => _publicLandsVisible = value);
                _controller?.setLayerVisibility('public-lands', value);
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLayerToggle(
    String label,
    bool value,
    Color color,
    ValueChanged<bool> onChanged,
  ) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color.withOpacity(0.3),
            border: Border.all(color: color),
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        const SizedBox(width: 8),
        Text(label, style: const TextStyle(fontSize: 12)),
        Switch(
          value: value,
          onChanged: onChanged,
          materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
        ),
      ],
    );
  }

  void _goToAustin() {
    _controller?.moveCamera(_austinLocation, zoom: 12);
  }

  void _showLocationInfo(LatLng latLng) {
    final solunar = _solunarService.getSolunarDay(
      latLng.latitude,
      latLng.longitude,
      DateTime.now(),
    );

    showModalBottomSheet(
      context: context,
      builder: (context) => Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Location Info',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Text('Latitude: ${latLng.latitude.toStringAsFixed(6)}'),
            Text('Longitude: ${latLng.longitude.toStringAsFixed(6)}'),
            const SizedBox(height: 12),
            Text('Day Rating: ${solunar.dayRating}/100'),
            Text('Moon Phase: ${solunar.moonPhase.phase.displayName}'),
            Text('Illumination: ${solunar.moonPhase.illumination.toStringAsFixed(1)}%'),
          ],
        ),
      ),
    );
  }

  void _showFeatureInfo(LatLng latLng, Map<String, dynamic> properties) {
    // Try to parse as parcel
    final parcel = ParcelInfo.fromProperties(properties);

    showModalBottomSheet(
      context: context,
      builder: (context) => Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: Colors.red,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                const SizedBox(width: 8),
                const Text(
                  'Private Property',
                  style: TextStyle(color: Colors.grey, fontSize: 12),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              parcel.ownerName ?? 'Unknown Owner',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            if (parcel.address != null) ...[
              const SizedBox(height: 4),
              Text(parcel.address!, style: const TextStyle(color: Colors.grey)),
            ],
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: [
                if (parcel.county != null)
                  Chip(label: Text(parcel.county!)),
                if (parcel.formattedAcreage != null)
                  Chip(label: Text(parcel.formattedAcreage!)),
                if (parcel.formattedMarketValue != null)
                  Chip(label: Text(parcel.formattedMarketValue!)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _showSolunarInfo() {
    if (_solunarDay == null) return;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) => SingleChildScrollView(
          controller: scrollController,
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.grey[300],
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Solunar Forecast',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 16),

              // Moon phase card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Text(
                        _solunarDay!.moonPhase.phase.emoji,
                        style: const TextStyle(fontSize: 48),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              _solunarDay!.moonPhase.phase.displayName,
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Text(
                              '${_solunarDay!.moonPhase.illumination.toStringAsFixed(0)}% illuminated',
                            ),
                            Text(
                              'Day ${_solunarDay!.moonPhase.age.toStringAsFixed(1)} of cycle',
                            ),
                          ],
                        ),
                      ),
                      Column(
                        children: [
                          Text(
                            '${_solunarDay!.dayRating}',
                            style: TextStyle(
                              fontSize: 32,
                              fontWeight: FontWeight.bold,
                              color: _getRatingColor(_solunarDay!.dayRating),
                            ),
                          ),
                          Text(
                            _solunarDay!.ratingDescription,
                            style: const TextStyle(fontSize: 12),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),
              const Text(
                'Major Periods',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              ..._solunarDay!.majorPeriods.map((p) => _buildPeriodTile(p)),

              const SizedBox(height: 16),
              const Text(
                'Minor Periods',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              ..._solunarDay!.minorPeriods.map((p) => _buildPeriodTile(p)),

              const SizedBox(height: 16),
              const Text(
                'Sun Times',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              if (_solunarDay!.sunrise != null)
                _buildTimeTile('Sunrise', _solunarDay!.sunrise!, Icons.wb_sunny),
              if (_solunarDay!.sunset != null)
                _buildTimeTile('Sunset', _solunarDay!.sunset!, Icons.nights_stay),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPeriodTile(SolunarPeriod period) {
    final isMajor = period.type == SolunarPeriodType.major;

    return Card(
      color: isMajor ? Colors.orange.shade50 : Colors.blue.shade50,
      child: ListTile(
        leading: Icon(
          isMajor ? Icons.star : Icons.star_border,
          color: isMajor ? Colors.orange : Colors.blue,
        ),
        title: Text(period.description),
        subtitle: Text(
          '${_formatTime(period.start)} - ${_formatTime(period.end)}',
        ),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: _getRatingColor(period.intensity).withOpacity(0.2),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            '${period.intensity}',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: _getRatingColor(period.intensity),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTimeTile(String label, DateTime time, IconData icon) {
    return ListTile(
      leading: Icon(icon),
      title: Text(label),
      trailing: Text(
        _formatTime(time),
        style: const TextStyle(fontWeight: FontWeight.bold),
      ),
    );
  }

  String _formatTime(DateTime time) {
    final hour = time.hour > 12 ? time.hour - 12 : time.hour;
    final period = time.hour >= 12 ? 'PM' : 'AM';
    return '$hour:${time.minute.toString().padLeft(2, '0')} $period';
  }

  Color _getRatingColor(int rating) {
    if (rating >= 75) return Colors.green;
    if (rating >= 50) return Colors.orange;
    return Colors.red;
  }
}
