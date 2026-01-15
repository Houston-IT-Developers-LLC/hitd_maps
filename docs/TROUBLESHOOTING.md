# Troubleshooting Guide

Common issues and solutions for the HITD Maps data pipeline and package.

## Table of Contents

1. [Tile Generation Issues](#tile-generation-issues)
2. [Map Display Issues](#map-display-issues)
3. [Data Quality Issues](#data-quality-issues)
4. [Upload/CDN Issues](#uploadcdn-issues)
5. [Mobile App Issues](#mobile-app-issues)
6. [Performance Issues](#performance-issues)

---

## Tile Generation Issues

### Problem: Tippecanoe runs out of memory

**Symptoms:**
```
Killed
```
or
```
std::bad_alloc
```

**Solution:**
1. Use `--drop-densest-as-needed` to auto-simplify
2. Process in smaller chunks (by county)
3. Increase swap space:
   ```bash
   sudo fallocate -l 16G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```
4. Use a larger server (512GB recommended for all 50 states)

### Problem: Tippecanoe produces empty tiles

**Symptoms:**
- PMTiles file is very small (<1KB)
- No features visible on map

**Cause:** Input GeoJSON has no features or wrong projection

**Solution:**
```bash
# Check if GeoJSON has features
ogrinfo -al -so input.geojson | grep "Feature Count"

# Check projection
ogrinfo -al -so input.geojson | grep "EPSG"

# Reproject if needed
ogr2ogr -f GeoJSON -t_srs EPSG:4326 output.geojson input.geojson
```

### Problem: "Invalid GeoJSON" error

**Symptoms:**
```
Error: Invalid GeoJSON
```

**Solution:**
1. Validate JSON syntax:
   ```bash
   python3 -m json.tool input.geojson > /dev/null
   ```

2. Check for geometry errors:
   ```bash
   ogrinfo -al input.geojson 2>&1 | grep -i error
   ```

3. Fix invalid geometries:
   ```bash
   ogr2ogr -f GeoJSON -makevalid output.geojson input.geojson
   ```

### Problem: Tiles take too long to generate

**Solution:**
1. Use parallel processing:
   ```bash
   ./scripts/parallel_pmtiles.sh
   ```

2. Reduce max zoom level:
   ```bash
   tippecanoe -z14 ...  # Instead of -z16
   ```

3. Simplify input geometry:
   ```bash
   ogr2ogr -f GeoJSON -simplify 0.0001 simplified.geojson input.geojson
   ```

---

## Map Display Issues

### Problem: Tiles not loading in app

**Symptoms:**
- Map shows but no parcel/layer data
- Console shows 404 errors

**Possible Causes & Solutions:**

1. **Wrong URL:**
   ```dart
   // Check HitdMapConfig
   print(HitdMapConfig.instance.pmtilesBaseUrl);

   // Verify URL is accessible
   // curl -I https://your-url/parcels/parcels_tx.pmtiles
   ```

2. **PMTiles protocol not supported:**
   - Ensure MapLibre version >= 6.14 (iOS) or >= 11.9 (Android)
   - Check that `usePmtilesProtocol` is set correctly

3. **CORS issues (web only):**
   - Configure R2 bucket CORS settings
   - Add allowed origins

### Problem: Layers appear at wrong zoom levels

**Symptoms:**
- Parcels visible at zoom 5 (too zoomed out)
- Or parcels not visible until zoom 16 (too zoomed in)

**Solution:**
Check minzoom/maxzoom in layer configuration:
```dart
HitdMapLayer.parcels(
  // These should match tippecanoe settings
)
```

And in tippecanoe:
```bash
tippecanoe --minimum-zoom=10 --maximum-zoom=16 ...
```

### Problem: Features not selectable/tappable

**Symptoms:**
- Tapping on parcel doesn't trigger `onFeatureTap`

**Solution:**
1. Check layer is in queryable list:
   ```dart
   print(controller.rawController.style.layers);
   ```

2. Ensure fill layer exists (not just outline):
   ```dart
   // Layer should have both parcels-fill and parcels-outline
   ```

3. Check touch target size

### Problem: Wrong colors displayed

**Symptoms:**
- Parcels showing as black or wrong color

**Solution:**
Color format must be hex string in MapLibre:
```dart
// Correct
fillColor: '#E53935'

// Wrong
fillColor: 'E53935'  // Missing #
fillColor: 0xFFE53935  // Int format doesn't work in expressions
```

---

## Data Quality Issues

### Problem: Missing parcels in certain areas

**Symptoms:**
- Gaps in parcel coverage
- Certain counties have no data

**Possible Causes:**

1. **Source data incomplete:**
   - Check if county publishes data
   - Some rural counties don't have digital records

2. **Scraping failed for some files:**
   ```bash
   # Check logs for errors
   grep -i error data-pipeline/logs/
   ```

3. **Tiles dropped features:**
   - Re-generate with `--no-feature-limit`
   - Or increase `--maximum-tile-features`

### Problem: Incorrect property boundaries

**Symptoms:**
- Parcels don't align with aerial imagery
- Boundaries are offset

**Cause:** Projection issue

**Solution:**
```bash
# Verify source projection
ogrinfo -al -so input.shp | grep -i "proj\|srs\|epsg"

# If not WGS84, reproject
ogr2ogr -f GeoJSON -s_srs "EPSG:XXXX" -t_srs EPSG:4326 output.geojson input.shp
```

### Problem: Garbled/wrong attribute data

**Symptoms:**
- Owner names show as numbers
- Addresses are truncated

**Solution:**
1. Check source encoding:
   ```bash
   file -i input.dbf
   ```

2. Convert encoding if needed:
   ```bash
   ogr2ogr -f GeoJSON output.geojson input.shp \
     -lco ENCODING=UTF-8 \
     -oo ENCODING=LATIN1
   ```

---

## Upload/CDN Issues

### Problem: Upload fails with "Access Denied"

**Symptoms:**
```
botocore.exceptions.ClientError: An error occurred (AccessDenied)
```

**Solution:**
1. Check credentials:
   ```bash
   echo $R2_ACCESS_KEY
   echo $R2_SECRET_KEY
   ```

2. Verify bucket permissions in Cloudflare dashboard

3. Check bucket name matches exactly

### Problem: Files upload but not accessible

**Symptoms:**
- Upload succeeds
- 404 when accessing via public URL

**Solution:**
1. Ensure bucket has public access enabled
2. Check the public URL format:
   ```
   https://pub-{hash}.r2.dev/{key}
   ```
3. Verify Content-Type header:
   ```python
   ExtraArgs={'ContentType': 'application/x-protobuf'}
   ```

### Problem: Old tiles still showing (caching)

**Symptoms:**
- Updated tiles but app shows old data

**Solution:**
1. **Client-side:** Clear app cache
   ```dart
   // Force reload in app
   await controller.removeLayer('parcels');
   await controller.addLayer(HitdMapLayer.parcels());
   ```

2. **CDN-side:** Purge cache in Cloudflare dashboard

3. **Use versioning:** Add version to filename
   ```
   parcels_tx_v2.pmtiles
   ```

---

## Mobile App Issues

### Problem: Map not initializing

**Symptoms:**
```
StateError: HitdMapConfig has not been initialized
```

**Solution:**
Initialize before runApp:
```dart
void main() {
  HitdMapConfig.initialize(
    pmtilesBaseUrl: 'https://...',
    basemapStyleUrl: 'assets/map/basemap_style.json',
  );
  runApp(MyApp());
}
```

### Problem: Style file not found

**Symptoms:**
```
Unable to load style
```

**Solution:**
1. Check asset is declared in pubspec.yaml:
   ```yaml
   flutter:
     assets:
       - assets/map/
   ```

2. Verify file exists at path

3. Use URL instead of asset for debugging:
   ```dart
   styleUrl: 'https://demotiles.maplibre.org/style.json'
   ```

### Problem: Location permission denied

**Symptoms:**
- User location not showing
- Permission error in logs

**Solution:**
1. Check AndroidManifest.xml:
   ```xml
   <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
   ```

2. Check Info.plist (iOS):
   ```xml
   <key>NSLocationWhenInUseUsageDescription</key>
   <string>We need your location to show nearby hunting areas</string>
   ```

3. Request permission in app:
   ```dart
   await Geolocator.requestPermission();
   ```

---

## Performance Issues

### Problem: Map is laggy/slow

**Symptoms:**
- Choppy pan/zoom
- High memory usage

**Solutions:**

1. **Reduce tile detail:**
   ```bash
   tippecanoe -z14 ...  # Lower max zoom
   ```

2. **Limit visible layers:**
   ```dart
   // Only show layers at appropriate zoom
   HitdMapLayer.parcels().copyWith(minZoom: 12)
   ```

3. **Use lower zoom cutoff:**
   ```dart
   if (zoom < 10) {
     controller.setLayerVisibility('parcels', false);
   }
   ```

### Problem: App crashes with large datasets

**Symptoms:**
- Out of memory crash
- App becomes unresponsive

**Solution:**
1. PMTiles handles this automatically (streams data)
2. Check you're not loading entire GeoJSON client-side
3. Reduce `maximum-tile-features` in tippecanoe

### Problem: Initial load is slow

**Symptoms:**
- Long delay before tiles appear

**Solutions:**

1. **Enable tile caching:**
   ```dart
   // MapLibre caches automatically, but ensure:
   // - Adequate cache size in app settings
   // - Not clearing cache on every launch
   ```

2. **Pre-cache visible area:**
   ```dart
   // Load tiles for user's saved locations on app start
   ```

3. **Use lower zoom tiles first:**
   - Tippecanoe generates overview tiles automatically
   - Ensure minzoom is set appropriately

---

## Getting Help

If you can't resolve an issue:

1. **Check logs:**
   ```bash
   # Data pipeline logs
   cat data-pipeline/logs/*.log

   # Flutter logs
   flutter logs
   ```

2. **Reproduce minimally:**
   - Create minimal test case
   - Isolate the problem

3. **File an issue:**
   - GitHub: https://github.com/RORHITD/hitd_maps/issues
   - Include: version, steps to reproduce, logs

4. **Contact:**
   - Houston IT Developers LLC
   - [Your contact info]
