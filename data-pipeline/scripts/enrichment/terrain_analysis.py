#!/usr/bin/env python3
"""
Terrain Analysis for Hunting-Relevant Features

Priority: 9
Source: USGS 3DEP DEM data
URL: https://www.usgs.gov/3d-elevation-program

Analyzes Digital Elevation Model (DEM) data to identify terrain features
important for deer hunting:

1. SADDLES - Low points between ridges (deer travel corridors)
   - Deer use saddles to cross between drainages
   - Natural pinch points for stand placement

2. BENCHES - Flat areas on hillsides (feeding/bedding areas)
   - Deer bed on benches with good visibility
   - Often overlooked by hunters

3. FUNNELS - Terrain pinch points (natural deer highways)
   - Narrow corridors of easy travel between obstacles
   - Where terrain forces deer into concentrated paths

4. SLOPE ANALYSIS - Identify ideal bedding slopes (10-30 degrees)
   - Steep enough for visibility, gentle enough for comfort

Input: USGS DEM GeoTIFF files (10m or 30m resolution)
Output: GeoJSON point/polygon features for each terrain type

Update Frequency: Static terrain data
Date Added: 2026-01-13
"""

import os
import sys
import json
import argparse
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = SCRIPT_DIR.parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output" / "enrichment"
TERRAIN_DIR = OUTPUT_DIR / "terrain"
LOG_DIR = DATA_PIPELINE_DIR / "logs" / "enrichment"

# R2 Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

# Terrain Feature Parameters
TERRAIN_PARAMS = {
    "saddles": {
        "name": "Saddles",
        "description": "Low points between ridges - deer crossing corridors",
        "tpi_range": (-5, 5),      # Near neutral TPI (not ridge, not valley)
        "curvature_min": 0.001,    # Positive plan curvature (convex across slope)
        "min_prominence": 10,      # Minimum meters below surrounding ridges
        "color": "#FF6B6B"
    },
    "benches": {
        "name": "Benches",
        "description": "Flat areas on hillsides - bedding/feeding zones",
        "slope_range": (5, 15),    # Degrees - gentle slopes
        "tpi_range": (-10, 10),    # Mid-slope position
        "min_area_sqm": 500,       # Minimum 500 sq meters
        "context_slope_min": 20,  # Surrounding terrain steeper than 20 degrees
        "color": "#4ECDC4"
    },
    "funnels": {
        "name": "Funnels",
        "description": "Terrain pinch points - natural deer highways",
        "width_max": 100,          # Maximum funnel width in meters
        "slope_max": 25,           # Maximum traversable slope
        "min_length": 50,          # Minimum funnel length
        "color": "#45B7D1"
    },
    "bedding_slopes": {
        "name": "Bedding Slopes",
        "description": "Ideal bedding areas - 10-30 degree slopes",
        "slope_range": (10, 30),   # Degrees
        "aspect_preferred": [(135, 225), (315, 45)],  # South and North facing
        "min_area_sqm": 200,
        "color": "#96CEB4"
    }
}


def log(message: str, level: str = "INFO") -> None:
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories() -> None:
    """Create necessary directories"""
    for dir_path in [TERRAIN_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def check_dependencies() -> Dict[str, bool]:
    """Check if required libraries are available"""
    deps = {}

    try:
        from osgeo import gdal, ogr, osr
        deps['gdal'] = True
        log(f"GDAL version: {gdal.__version__}")
    except ImportError:
        deps['gdal'] = False
        log("GDAL not available - required for terrain analysis", "ERROR")

    try:
        import numpy as np
        deps['numpy'] = True
    except ImportError:
        deps['numpy'] = False
        log("NumPy not available - required for terrain analysis", "ERROR")

    try:
        from scipy import ndimage
        deps['scipy'] = True
    except ImportError:
        deps['scipy'] = False
        log("SciPy not available - will use pure NumPy for filters", "WARNING")

    try:
        from shapely.geometry import Point, Polygon, MultiPolygon, mapping
        from shapely.ops import unary_union
        deps['shapely'] = True
    except ImportError:
        deps['shapely'] = False
        log("Shapely not available - required for geometry creation", "ERROR")

    return deps


class TerrainAnalyzer:
    """
    Analyze DEM data to extract hunting-relevant terrain features
    """

    def __init__(self, dem_path: str, output_dir: Optional[Path] = None):
        """
        Initialize terrain analyzer

        Args:
            dem_path: Path to input DEM GeoTIFF
            output_dir: Output directory for results
        """
        from osgeo import gdal
        import numpy as np

        self.dem_path = dem_path
        self.output_dir = output_dir or TERRAIN_DIR

        # Load DEM
        log(f"Loading DEM: {dem_path}")
        self.ds = gdal.Open(dem_path)
        if self.ds is None:
            raise ValueError(f"Could not open DEM: {dem_path}")

        # Get DEM info
        self.gt = self.ds.GetGeoTransform()
        self.projection = self.ds.GetProjection()
        self.cols = self.ds.RasterXSize
        self.rows = self.ds.RasterYSize

        # Calculate cell size in meters (approximate if in degrees)
        self.cell_size_x = abs(self.gt[1])
        self.cell_size_y = abs(self.gt[5])

        # If in degrees, convert to approximate meters
        if abs(self.cell_size_x) < 1:
            # Approximate conversion at mid-latitude
            self.cell_size_m = self.cell_size_x * 111000  # degrees to meters
        else:
            self.cell_size_m = self.cell_size_x

        log(f"  Dimensions: {self.cols} x {self.rows}")
        log(f"  Cell size: {self.cell_size_m:.2f}m")
        log(f"  Bounds: ({self.gt[0]:.4f}, {self.gt[3] + self.rows * self.gt[5]:.4f}) to "
            f"({self.gt[0] + self.cols * self.gt[1]:.4f}, {self.gt[3]:.4f})")

        # Read elevation data
        band = self.ds.GetRasterBand(1)
        self.nodata = band.GetNoDataValue()
        self.elevation = band.ReadAsArray().astype(np.float32)

        # Mask nodata values
        if self.nodata is not None:
            self.elevation = np.ma.masked_equal(self.elevation, self.nodata)

        log(f"  Elevation range: {np.nanmin(self.elevation):.1f}m to {np.nanmax(self.elevation):.1f}m")

        # Pre-computed derived rasters
        self._slope = None
        self._aspect = None
        self._tpi = None
        self._curvature = None

    def _get_filter_func(self):
        """Get appropriate filter function (scipy or numpy fallback)"""
        try:
            from scipy import ndimage
            return ndimage
        except ImportError:
            return None

    def calculate_slope(self) -> 'np.ndarray':
        """
        Calculate slope in degrees

        Returns:
            Slope array in degrees
        """
        import numpy as np

        if self._slope is not None:
            return self._slope

        log("Calculating slope...")

        # Calculate gradients
        # Using Sobel-like kernel for better results
        dy, dx = np.gradient(self.elevation, self.cell_size_m)

        # Calculate slope in degrees
        slope_radians = np.arctan(np.sqrt(dx**2 + dy**2))
        self._slope = np.degrees(slope_radians)

        log(f"  Slope range: {np.nanmin(self._slope):.1f} to {np.nanmax(self._slope):.1f} degrees")

        return self._slope

    def calculate_aspect(self) -> 'np.ndarray':
        """
        Calculate aspect in degrees (0-360, 0=North, clockwise)

        Returns:
            Aspect array in degrees
        """
        import numpy as np

        if self._aspect is not None:
            return self._aspect

        log("Calculating aspect...")

        # Calculate gradients
        dy, dx = np.gradient(self.elevation, self.cell_size_m)

        # Calculate aspect
        aspect_radians = np.arctan2(-dx, dy)
        self._aspect = np.degrees(aspect_radians)

        # Convert to 0-360 range (0 = North, clockwise)
        self._aspect = (self._aspect + 360) % 360

        return self._aspect

    def calculate_tpi(self, radius_m: float = 100) -> 'np.ndarray':
        """
        Calculate Terrain Position Index

        TPI = elevation - mean(neighborhood elevation)
        Positive = ridges/hilltops
        Negative = valleys/depressions
        Near zero = mid-slope or flat

        Args:
            radius_m: Neighborhood radius in meters

        Returns:
            TPI array
        """
        import numpy as np

        if self._tpi is not None:
            return self._tpi

        log(f"Calculating TPI (radius={radius_m}m)...")

        # Calculate kernel size
        kernel_size = int(radius_m / self.cell_size_m)
        if kernel_size < 3:
            kernel_size = 3
        if kernel_size % 2 == 0:
            kernel_size += 1

        log(f"  Kernel size: {kernel_size} cells")

        ndimage = self._get_filter_func()

        if ndimage:
            # Use scipy for faster computation
            from scipy.ndimage import uniform_filter
            neighborhood_mean = uniform_filter(
                self.elevation.filled(np.nan) if hasattr(self.elevation, 'filled') else self.elevation,
                size=kernel_size,
                mode='nearest'
            )
        else:
            # Pure numpy fallback - moving average using convolution
            kernel = np.ones((kernel_size, kernel_size)) / (kernel_size * kernel_size)
            elev_filled = self.elevation.filled(np.nan) if hasattr(self.elevation, 'filled') else self.elevation

            # Pad array
            pad_size = kernel_size // 2
            padded = np.pad(elev_filled, pad_size, mode='edge')

            # Compute mean using stride tricks for efficiency
            neighborhood_mean = np.zeros_like(elev_filled)
            for i in range(kernel_size):
                for j in range(kernel_size):
                    neighborhood_mean += padded[i:i+self.rows, j:j+self.cols]
            neighborhood_mean /= (kernel_size * kernel_size)

        self._tpi = self.elevation - neighborhood_mean

        log(f"  TPI range: {np.nanmin(self._tpi):.1f} to {np.nanmax(self._tpi):.1f}")

        return self._tpi

    def calculate_curvature(self) -> Tuple['np.ndarray', 'np.ndarray']:
        """
        Calculate profile and plan curvature

        Profile curvature: Rate of change of slope in downslope direction
        Plan curvature: Rate of change of aspect in across-slope direction

        Returns:
            (profile_curvature, plan_curvature)
        """
        import numpy as np

        if self._curvature is not None:
            return self._curvature

        log("Calculating curvature...")

        # Second derivatives
        elev = self.elevation.filled(np.nan) if hasattr(self.elevation, 'filled') else self.elevation

        # First derivatives
        fy, fx = np.gradient(elev, self.cell_size_m)

        # Second derivatives
        fyy, fyx = np.gradient(fy, self.cell_size_m)
        fxy, fxx = np.gradient(fx, self.cell_size_m)

        # Avoid division by zero
        p = fx**2 + fy**2
        p[p == 0] = 1e-10
        q = p + 1

        # Profile curvature (in direction of steepest slope)
        profile = -(fx**2 * fxx + 2*fx*fy*fxy + fy**2 * fyy) / (p * np.sqrt(q**3))

        # Plan curvature (perpendicular to slope)
        plan = -(fy**2 * fxx - 2*fx*fy*fxy + fx**2 * fyy) / (p**1.5)

        self._curvature = (profile, plan)

        return self._curvature

    def _pixel_to_coords(self, row: int, col: int) -> Tuple[float, float]:
        """Convert pixel coordinates to geographic coordinates"""
        x = self.gt[0] + col * self.gt[1] + row * self.gt[2]
        y = self.gt[3] + col * self.gt[4] + row * self.gt[5]
        return (x, y)

    def _coords_to_pixel(self, x: float, y: float) -> Tuple[int, int]:
        """Convert geographic coordinates to pixel coordinates"""
        col = int((x - self.gt[0]) / self.gt[1])
        row = int((y - self.gt[3]) / self.gt[5])
        return (row, col)

    def find_saddles(self, min_prominence: float = 10) -> List[Dict[str, Any]]:
        """
        Find saddle points - low points on ridgelines between higher terrain

        Saddles are identified as points that are:
        1. Local minima along one axis (ridge direction)
        2. Local maxima along perpendicular axis (valley direction)
        3. Have sufficient prominence (drop from surrounding ridges)

        Args:
            min_prominence: Minimum elevation drop from surrounding ridges

        Returns:
            List of saddle features with properties
        """
        import numpy as np
        from shapely.geometry import Point

        log("Finding saddles...")

        slope = self.calculate_slope()
        tpi = self.calculate_tpi()
        profile_curv, plan_curv = self.calculate_curvature()

        ndimage = self._get_filter_func()

        # Find candidate saddle points
        # Saddles have: low TPI (not a ridge top), positive plan curvature (convex across slope)
        params = TERRAIN_PARAMS["saddles"]

        candidates = (
            (tpi >= params["tpi_range"][0]) &
            (tpi <= params["tpi_range"][1]) &
            (plan_curv > params["curvature_min"]) &
            (slope < 30)  # Not on extremely steep terrain
        )

        # Find local minima in elevation among candidates
        if ndimage:
            from scipy.ndimage import minimum_filter, maximum_filter

            # Local minimum in one direction, maximum in perpendicular
            elev_filled = self.elevation.filled(np.inf) if hasattr(self.elevation, 'filled') else self.elevation

            min_elev_3x3 = minimum_filter(elev_filled, size=3)
            max_elev_5x5 = maximum_filter(elev_filled, size=5)

            # Point must be minimum in small window and have higher terrain nearby
            is_local_min = (elev_filled == min_elev_3x3)
            has_prominence = (max_elev_5x5 - elev_filled) >= min_prominence

            saddle_mask = candidates & is_local_min & has_prominence
        else:
            # Pure numpy fallback - simpler detection
            elev_filled = self.elevation.filled(np.inf) if hasattr(self.elevation, 'filled') else self.elevation
            saddle_mask = candidates.copy()

            # Check each candidate for local minimum property
            for i in range(1, self.rows - 1):
                for j in range(1, self.cols - 1):
                    if candidates[i, j]:
                        window = elev_filled[i-1:i+2, j-1:j+2]
                        center = elev_filled[i, j]
                        if center != np.min(window):
                            saddle_mask[i, j] = False
                        elif np.max(window) - center < min_prominence:
                            saddle_mask[i, j] = False

        # Extract saddle points
        saddle_rows, saddle_cols = np.where(saddle_mask)

        log(f"  Found {len(saddle_rows)} potential saddles")

        # Build feature list
        features = []
        for idx, (row, col) in enumerate(zip(saddle_rows, saddle_cols)):
            x, y = self._pixel_to_coords(row, col)
            elev = float(self.elevation[row, col])

            feature = {
                "type": "Feature",
                "geometry": mapping(Point(x, y)),
                "properties": {
                    "feature_type": "saddle",
                    "elevation_m": round(elev, 1),
                    "slope_deg": round(float(slope[row, col]), 1),
                    "tpi": round(float(tpi[row, col]), 2),
                    "prominence_m": round(float(np.max(self.elevation[
                        max(0, row-5):min(self.rows, row+6),
                        max(0, col-5):min(self.cols, col+6)
                    ]) - elev), 1),
                    "hunting_notes": "Deer crossing corridor - good stand location"
                }
            }
            features.append(feature)

        log(f"  Extracted {len(features)} saddle features")
        return features

    def find_benches(self, min_area_sqm: float = 500) -> List[Dict[str, Any]]:
        """
        Find bench features - flat areas on hillsides

        Benches are identified as:
        1. Low slope areas (5-15 degrees)
        2. Surrounded by steeper terrain
        3. On mid-slope positions (not valley bottom or ridge top)

        Args:
            min_area_sqm: Minimum bench area in square meters

        Returns:
            List of bench polygon features
        """
        import numpy as np
        from shapely.geometry import Polygon, MultiPolygon, mapping
        from shapely.ops import unary_union

        log("Finding benches...")

        slope = self.calculate_slope()
        tpi = self.calculate_tpi()

        params = TERRAIN_PARAMS["benches"]
        ndimage = self._get_filter_func()

        # Find low-slope areas
        low_slope = (slope >= params["slope_range"][0]) & (slope <= params["slope_range"][1])

        # Must be mid-slope (not valley or ridge)
        mid_slope = (tpi >= params["tpi_range"][0]) & (tpi <= params["tpi_range"][1])

        # Check for steeper surrounding terrain
        if ndimage:
            from scipy.ndimage import maximum_filter
            surrounding_slope = maximum_filter(slope, size=11)
        else:
            # Pure numpy - approximate with padding
            surrounding_slope = slope.copy()
            for i in range(5, self.rows - 5):
                for j in range(5, self.cols - 5):
                    surrounding_slope[i, j] = np.max(slope[i-5:i+6, j-5:j+6])

        steep_context = surrounding_slope >= params["context_slope_min"]

        # Combine criteria
        bench_mask = low_slope & mid_slope & steep_context

        # Label connected components
        if ndimage:
            from scipy.ndimage import label
            labeled, num_features = label(bench_mask)
        else:
            # Simple connected components without scipy
            labeled = np.zeros_like(bench_mask, dtype=int)
            current_label = 0
            for i in range(self.rows):
                for j in range(self.cols):
                    if bench_mask[i, j] and labeled[i, j] == 0:
                        current_label += 1
                        # Simple flood fill
                        stack = [(i, j)]
                        while stack:
                            r, c = stack.pop()
                            if (0 <= r < self.rows and 0 <= c < self.cols and
                                bench_mask[r, c] and labeled[r, c] == 0):
                                labeled[r, c] = current_label
                                stack.extend([(r-1, c), (r+1, c), (r, c-1), (r, c+1)])
            num_features = current_label

        log(f"  Found {num_features} potential bench areas")

        # Convert to polygons
        min_pixels = int(min_area_sqm / (self.cell_size_m ** 2))
        features = []

        for label_id in range(1, num_features + 1):
            mask = labeled == label_id
            pixel_count = np.sum(mask)

            if pixel_count < min_pixels:
                continue

            # Get bounding box and extract polygon
            rows, cols = np.where(mask)
            if len(rows) == 0:
                continue

            # Create polygon from convex hull of points
            points = []
            for r, c in zip(rows, cols):
                x, y = self._pixel_to_coords(r, c)
                points.append((x, y))

            if len(points) < 3:
                continue

            try:
                from shapely.geometry import MultiPoint
                mp = MultiPoint(points)
                polygon = mp.convex_hull

                if polygon.is_empty or polygon.area < min_area_sqm * 1e-10:  # Rough conversion
                    continue

                # Calculate properties
                center_row = int(np.mean(rows))
                center_col = int(np.mean(cols))

                area_sqm = pixel_count * (self.cell_size_m ** 2)
                avg_slope = float(np.mean(slope[mask]))
                avg_elev = float(np.mean(self.elevation[mask]))

                feature = {
                    "type": "Feature",
                    "geometry": mapping(polygon),
                    "properties": {
                        "feature_type": "bench",
                        "area_sqm": round(area_sqm, 0),
                        "area_acres": round(area_sqm / 4047, 2),
                        "avg_slope_deg": round(avg_slope, 1),
                        "avg_elevation_m": round(avg_elev, 1),
                        "hunting_notes": "Potential bedding/feeding area - approach from downwind"
                    }
                }
                features.append(feature)

            except Exception as e:
                log(f"  Error creating polygon for bench {label_id}: {e}", "WARNING")
                continue

        log(f"  Extracted {len(features)} bench features")
        return features

    def find_funnels(self, max_width: float = 100, min_length: float = 50) -> List[Dict[str, Any]]:
        """
        Find terrain funnels - narrow corridors of easy travel

        Funnels are identified by:
        1. Narrow width between obstacles (steep terrain, water, etc.)
        2. Low enough slope for deer travel (< 25 degrees)
        3. Sufficient length to be a meaningful travel route

        Args:
            max_width: Maximum funnel width in meters
            min_length: Minimum funnel length in meters

        Returns:
            List of funnel features (lines or polygons)
        """
        import numpy as np
        from shapely.geometry import LineString, Polygon, mapping

        log("Finding funnels...")

        slope = self.calculate_slope()
        tpi = self.calculate_tpi()

        params = TERRAIN_PARAMS["funnels"]
        ndimage = self._get_filter_func()

        # Traversable terrain (not too steep)
        traversable = slope < params["slope_max"]

        # Non-traversable terrain (obstacles)
        obstacles = ~traversable

        # Calculate distance to obstacles
        if ndimage:
            from scipy.ndimage import distance_transform_edt
            distance_to_obstacle = distance_transform_edt(traversable) * self.cell_size_m
        else:
            # Simple approximation without scipy
            distance_to_obstacle = np.zeros_like(slope)
            for i in range(self.rows):
                for j in range(self.cols):
                    if traversable[i, j]:
                        # Find nearest obstacle
                        min_dist = float('inf')
                        search_radius = int(max_width / self.cell_size_m) + 1
                        for di in range(-search_radius, search_radius + 1):
                            for dj in range(-search_radius, search_radius + 1):
                                ni, nj = i + di, j + dj
                                if 0 <= ni < self.rows and 0 <= nj < self.cols:
                                    if obstacles[ni, nj]:
                                        dist = np.sqrt(di**2 + dj**2) * self.cell_size_m
                                        min_dist = min(min_dist, dist)
                        distance_to_obstacle[i, j] = min_dist if min_dist != float('inf') else max_width * 2

        # Find narrow corridors (close to obstacles on both sides)
        # A funnel has obstacles nearby but is still traversable
        max_width_pixels = int(max_width / self.cell_size_m / 2)

        funnel_mask = (
            traversable &
            (distance_to_obstacle > 0) &
            (distance_to_obstacle < max_width / 2)
        )

        # Label connected narrow areas
        if ndimage:
            from scipy.ndimage import label
            labeled, num_features = label(funnel_mask)
        else:
            labeled = np.zeros_like(funnel_mask, dtype=int)
            current_label = 0
            for i in range(self.rows):
                for j in range(self.cols):
                    if funnel_mask[i, j] and labeled[i, j] == 0:
                        current_label += 1
                        stack = [(i, j)]
                        while stack:
                            r, c = stack.pop()
                            if (0 <= r < self.rows and 0 <= c < self.cols and
                                funnel_mask[r, c] and labeled[r, c] == 0):
                                labeled[r, c] = current_label
                                stack.extend([(r-1, c), (r+1, c), (r, c-1), (r, c+1)])
            num_features = current_label

        log(f"  Found {num_features} potential funnel areas")

        # Filter by length and convert to features
        min_pixels_length = int(min_length / self.cell_size_m)
        features = []

        for label_id in range(1, num_features + 1):
            mask = labeled == label_id
            rows, cols = np.where(mask)

            if len(rows) < min_pixels_length:
                continue

            # Calculate extent (rough length estimate)
            row_extent = np.max(rows) - np.min(rows)
            col_extent = np.max(cols) - np.min(cols)
            length_pixels = max(row_extent, col_extent)
            length_m = length_pixels * self.cell_size_m

            if length_m < min_length:
                continue

            # Create polygon from points
            points = []
            for r, c in zip(rows, cols):
                x, y = self._pixel_to_coords(r, c)
                points.append((x, y))

            if len(points) < 3:
                continue

            try:
                from shapely.geometry import MultiPoint
                mp = MultiPoint(points)
                polygon = mp.convex_hull

                if polygon.is_empty:
                    continue

                # Calculate width (perpendicular to length)
                if row_extent > col_extent:
                    # Primarily N-S oriented
                    width_m = col_extent * self.cell_size_m
                else:
                    # Primarily E-W oriented
                    width_m = row_extent * self.cell_size_m

                avg_slope = float(np.mean(slope[mask]))
                avg_elev = float(np.mean(self.elevation[mask]))

                feature = {
                    "type": "Feature",
                    "geometry": mapping(polygon),
                    "properties": {
                        "feature_type": "funnel",
                        "length_m": round(length_m, 0),
                        "width_m": round(width_m, 0),
                        "avg_slope_deg": round(avg_slope, 1),
                        "avg_elevation_m": round(avg_elev, 1),
                        "hunting_notes": "Natural deer highway - high traffic area"
                    }
                }
                features.append(feature)

            except Exception as e:
                log(f"  Error creating polygon for funnel {label_id}: {e}", "WARNING")
                continue

        log(f"  Extracted {len(features)} funnel features")
        return features

    def find_bedding_slopes(self, preferred_aspects: List[Tuple[float, float]] = None) -> List[Dict[str, Any]]:
        """
        Find ideal bedding slopes - areas with 10-30 degree slopes

        Args:
            preferred_aspects: List of (min, max) aspect ranges in degrees
                             Default: south-facing (135-225) and north-facing (315-45)

        Returns:
            List of bedding slope polygon features
        """
        import numpy as np
        from shapely.geometry import Polygon, mapping

        log("Finding bedding slopes...")

        slope = self.calculate_slope()
        aspect = self.calculate_aspect()
        tpi = self.calculate_tpi()

        params = TERRAIN_PARAMS["bedding_slopes"]
        ndimage = self._get_filter_func()

        if preferred_aspects is None:
            preferred_aspects = params["aspect_preferred"]

        # Slope criteria
        good_slope = (slope >= params["slope_range"][0]) & (slope <= params["slope_range"][1])

        # Aspect criteria (handle wrap-around at 360/0)
        good_aspect = np.zeros_like(aspect, dtype=bool)
        for asp_min, asp_max in preferred_aspects:
            if asp_min > asp_max:  # Wraps around 0 (e.g., 315 to 45)
                good_aspect |= (aspect >= asp_min) | (aspect <= asp_max)
            else:
                good_aspect |= (aspect >= asp_min) & (aspect <= asp_max)

        # Combine criteria (optionally include all aspects)
        bedding_mask = good_slope  # Can add & good_aspect if aspect filtering desired

        # Label connected components
        if ndimage:
            from scipy.ndimage import label
            labeled, num_features = label(bedding_mask)
        else:
            labeled = np.zeros_like(bedding_mask, dtype=int)
            current_label = 0
            for i in range(self.rows):
                for j in range(self.cols):
                    if bedding_mask[i, j] and labeled[i, j] == 0:
                        current_label += 1
                        stack = [(i, j)]
                        while stack:
                            r, c = stack.pop()
                            if (0 <= r < self.rows and 0 <= c < self.cols and
                                bedding_mask[r, c] and labeled[r, c] == 0):
                                labeled[r, c] = current_label
                                stack.extend([(r-1, c), (r+1, c), (r, c-1), (r, c+1)])
            num_features = current_label

        log(f"  Found {num_features} potential bedding areas")

        # Filter by area and convert to features
        min_pixels = int(params["min_area_sqm"] / (self.cell_size_m ** 2))
        features = []

        for label_id in range(1, num_features + 1):
            mask = labeled == label_id
            pixel_count = np.sum(mask)

            if pixel_count < min_pixels:
                continue

            rows, cols = np.where(mask)
            if len(rows) == 0:
                continue

            # Create polygon
            points = []
            for r, c in zip(rows, cols):
                x, y = self._pixel_to_coords(r, c)
                points.append((x, y))

            if len(points) < 3:
                continue

            try:
                from shapely.geometry import MultiPoint
                mp = MultiPoint(points)
                polygon = mp.convex_hull

                if polygon.is_empty:
                    continue

                area_sqm = pixel_count * (self.cell_size_m ** 2)
                avg_slope = float(np.mean(slope[mask]))
                avg_aspect = float(np.mean(aspect[mask]))
                avg_elev = float(np.mean(self.elevation[mask]))

                # Determine aspect direction
                if 315 <= avg_aspect or avg_aspect < 45:
                    aspect_dir = "North"
                elif 45 <= avg_aspect < 135:
                    aspect_dir = "East"
                elif 135 <= avg_aspect < 225:
                    aspect_dir = "South"
                else:
                    aspect_dir = "West"

                feature = {
                    "type": "Feature",
                    "geometry": mapping(polygon),
                    "properties": {
                        "feature_type": "bedding_slope",
                        "area_sqm": round(area_sqm, 0),
                        "area_acres": round(area_sqm / 4047, 2),
                        "avg_slope_deg": round(avg_slope, 1),
                        "avg_aspect_deg": round(avg_aspect, 0),
                        "aspect_direction": aspect_dir,
                        "avg_elevation_m": round(avg_elev, 1),
                        "hunting_notes": f"{aspect_dir}-facing bedding slope - approach from below"
                    }
                }
                features.append(feature)

            except Exception as e:
                log(f"  Error creating polygon for bedding area {label_id}: {e}", "WARNING")
                continue

        log(f"  Extracted {len(features)} bedding slope features")
        return features

    def export_slope_raster(self, output_path: Optional[str] = None) -> str:
        """Export slope raster as GeoTIFF"""
        from osgeo import gdal, osr
        import numpy as np

        slope = self.calculate_slope()

        if output_path is None:
            output_path = str(self.output_dir / "slope.tif")

        log(f"Exporting slope raster: {output_path}")

        driver = gdal.GetDriverByName('GTiff')
        out_ds = driver.Create(output_path, self.cols, self.rows, 1, gdal.GDT_Float32)
        out_ds.SetGeoTransform(self.gt)
        out_ds.SetProjection(self.projection)

        out_band = out_ds.GetRasterBand(1)
        out_band.WriteArray(slope)
        out_band.SetNoDataValue(-9999)
        out_band.FlushCache()

        out_ds = None

        return output_path

    def export_tpi_raster(self, output_path: Optional[str] = None) -> str:
        """Export TPI raster as GeoTIFF"""
        from osgeo import gdal
        import numpy as np

        tpi = self.calculate_tpi()

        if output_path is None:
            output_path = str(self.output_dir / "tpi.tif")

        log(f"Exporting TPI raster: {output_path}")

        driver = gdal.GetDriverByName('GTiff')
        out_ds = driver.Create(output_path, self.cols, self.rows, 1, gdal.GDT_Float32)
        out_ds.SetGeoTransform(self.gt)
        out_ds.SetProjection(self.projection)

        out_band = out_ds.GetRasterBand(1)
        tpi_filled = tpi.filled(-9999) if hasattr(tpi, 'filled') else tpi
        out_band.WriteArray(tpi_filled)
        out_band.SetNoDataValue(-9999)
        out_band.FlushCache()

        out_ds = None

        return output_path


def export_geojson(features: List[Dict], output_path: str, feature_type: str) -> str:
    """
    Export features to GeoJSON file

    Args:
        features: List of GeoJSON feature dicts
        output_path: Output file path
        feature_type: Type of features for metadata

    Returns:
        Output file path
    """
    log(f"Exporting {len(features)} {feature_type} features to: {output_path}")

    geojson = {
        "type": "FeatureCollection",
        "name": f"terrain_{feature_type}",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": features
    }

    with open(output_path, 'w') as f:
        json.dump(geojson, f)

    return output_path


def convert_to_pmtiles(geojson_path: str, pmtiles_path: str) -> Optional[str]:
    """
    Convert GeoJSON to PMTiles using tippecanoe

    Args:
        geojson_path: Input GeoJSON file
        pmtiles_path: Output PMTiles file

    Returns:
        PMTiles path if successful, None otherwise
    """
    log(f"Converting to PMTiles: {pmtiles_path}")

    # Check for tippecanoe
    try:
        subprocess.run(["tippecanoe", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("tippecanoe not found - skipping PMTiles conversion", "WARNING")
        return None

    cmd = [
        "tippecanoe",
        "-o", pmtiles_path,
        "-z", "14",  # Max zoom
        "-Z", "8",   # Min zoom
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "-l", "terrain",  # Layer name
        "--force",
        geojson_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            log(f"  Created: {pmtiles_path}")
            return pmtiles_path
        else:
            log(f"  tippecanoe error: {result.stderr}", "ERROR")
            return None
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return None


def upload_to_r2(local_path: str, r2_key: str) -> Optional[str]:
    """
    Upload file to Cloudflare R2

    Args:
        local_path: Local file path
        r2_key: R2 object key

    Returns:
        Public URL if successful, None otherwise
    """
    try:
        import boto3
    except ImportError:
        log("boto3 not available - cannot upload to R2", "ERROR")
        return None

    log(f"Uploading to R2: {r2_key}")

    # Determine content type
    if local_path.endswith('.pmtiles'):
        content_type = 'application/octet-stream'
    elif local_path.endswith('.geojson'):
        content_type = 'application/geo+json'
    elif local_path.endswith('.tif') or local_path.endswith('.tiff'):
        content_type = 'image/tiff'
    else:
        content_type = 'application/octet-stream'

    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
        )

        s3_client.upload_file(
            local_path,
            R2_BUCKET,
            r2_key,
            ExtraArgs={'ContentType': content_type}
        )

        public_url = f"{R2_PUBLIC_URL}/{r2_key}"
        log(f"  Uploaded: {public_url}")
        return public_url

    except Exception as e:
        log(f"  Upload error: {e}", "ERROR")
        return None


def analyze_terrain(
    dem_path: str,
    output_dir: Optional[str] = None,
    features: List[str] = None,
    state: str = None,
    generate_pmtiles: bool = False,
    upload: bool = False
) -> Dict[str, Any]:
    """
    Main terrain analysis function

    Args:
        dem_path: Path to input DEM GeoTIFF
        output_dir: Output directory
        features: List of features to extract ['saddles', 'benches', 'funnels', 'bedding_slopes']
        state: State abbreviation for output naming
        generate_pmtiles: Convert to PMTiles
        upload: Upload to R2

    Returns:
        Dictionary with results
    """
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = TERRAIN_DIR

    output_path.mkdir(parents=True, exist_ok=True)

    if features is None:
        features = ['saddles', 'benches', 'funnels', 'bedding_slopes']

    state_suffix = f"_{state}" if state else ""

    # Initialize analyzer
    analyzer = TerrainAnalyzer(dem_path, output_path)

    results = {
        "input_dem": dem_path,
        "features_extracted": {},
        "files_created": [],
        "uploaded": []
    }

    # Extract each feature type
    all_features = []

    if 'saddles' in features:
        saddles = analyzer.find_saddles()
        results["features_extracted"]["saddles"] = len(saddles)
        all_features.extend(saddles)

        if saddles:
            geojson_path = str(output_path / f"saddles{state_suffix}.geojson")
            export_geojson(saddles, geojson_path, "saddles")
            results["files_created"].append(geojson_path)

            if generate_pmtiles:
                pmtiles_path = str(output_path / f"saddles{state_suffix}.pmtiles")
                if convert_to_pmtiles(geojson_path, pmtiles_path):
                    results["files_created"].append(pmtiles_path)
                    if upload:
                        r2_key = f"enrichment/terrain/saddles{state_suffix}.pmtiles"
                        url = upload_to_r2(pmtiles_path, r2_key)
                        if url:
                            results["uploaded"].append(url)

    if 'benches' in features:
        benches = analyzer.find_benches()
        results["features_extracted"]["benches"] = len(benches)
        all_features.extend(benches)

        if benches:
            geojson_path = str(output_path / f"benches{state_suffix}.geojson")
            export_geojson(benches, geojson_path, "benches")
            results["files_created"].append(geojson_path)

            if generate_pmtiles:
                pmtiles_path = str(output_path / f"benches{state_suffix}.pmtiles")
                if convert_to_pmtiles(geojson_path, pmtiles_path):
                    results["files_created"].append(pmtiles_path)
                    if upload:
                        r2_key = f"enrichment/terrain/benches{state_suffix}.pmtiles"
                        url = upload_to_r2(pmtiles_path, r2_key)
                        if url:
                            results["uploaded"].append(url)

    if 'funnels' in features:
        funnels = analyzer.find_funnels()
        results["features_extracted"]["funnels"] = len(funnels)
        all_features.extend(funnels)

        if funnels:
            geojson_path = str(output_path / f"funnels{state_suffix}.geojson")
            export_geojson(funnels, geojson_path, "funnels")
            results["files_created"].append(geojson_path)

            if generate_pmtiles:
                pmtiles_path = str(output_path / f"funnels{state_suffix}.pmtiles")
                if convert_to_pmtiles(geojson_path, pmtiles_path):
                    results["files_created"].append(pmtiles_path)
                    if upload:
                        r2_key = f"enrichment/terrain/funnels{state_suffix}.pmtiles"
                        url = upload_to_r2(pmtiles_path, r2_key)
                        if url:
                            results["uploaded"].append(url)

    if 'bedding_slopes' in features:
        bedding = analyzer.find_bedding_slopes()
        results["features_extracted"]["bedding_slopes"] = len(bedding)
        all_features.extend(bedding)

        if bedding:
            geojson_path = str(output_path / f"bedding_slopes{state_suffix}.geojson")
            export_geojson(bedding, geojson_path, "bedding_slopes")
            results["files_created"].append(geojson_path)

            if generate_pmtiles:
                pmtiles_path = str(output_path / f"bedding_slopes{state_suffix}.pmtiles")
                if convert_to_pmtiles(geojson_path, pmtiles_path):
                    results["files_created"].append(pmtiles_path)
                    if upload:
                        r2_key = f"enrichment/terrain/bedding_slopes{state_suffix}.pmtiles"
                        url = upload_to_r2(pmtiles_path, r2_key)
                        if url:
                            results["uploaded"].append(url)

    # Export combined terrain features
    if all_features:
        combined_path = str(output_path / f"terrain_features{state_suffix}.geojson")
        export_geojson(all_features, combined_path, "all_terrain")
        results["files_created"].append(combined_path)

        if generate_pmtiles:
            pmtiles_path = str(output_path / f"terrain_features{state_suffix}.pmtiles")
            if convert_to_pmtiles(combined_path, pmtiles_path):
                results["files_created"].append(pmtiles_path)
                if upload:
                    r2_key = f"enrichment/terrain/terrain_features{state_suffix}.pmtiles"
                    url = upload_to_r2(pmtiles_path, r2_key)
                    if url:
                        results["uploaded"].append(url)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Terrain Analysis for Hunting-Relevant Features",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze DEM and extract all features
  python3 terrain_analysis.py --input dem.tif

  # Extract specific features only
  python3 terrain_analysis.py --input dem.tif --features saddles,benches

  # Full pipeline with PMTiles and R2 upload
  python3 terrain_analysis.py --input dem.tif --state TX --pmtiles --upload

  # Specify output bounding box
  python3 terrain_analysis.py --input dem.tif --bbox -97.5,30.0,-97.0,30.5

Feature Types:
  saddles       - Low points between ridges (deer crossing corridors)
  benches       - Flat areas on hillsides (feeding/bedding zones)
  funnels       - Terrain pinch points (natural deer highways)
  bedding_slopes - Ideal bedding areas (10-30 degree slopes)

Output Files:
  GeoJSON: saddles_{state}.geojson, benches_{state}.geojson, etc.
  PMTiles: saddles_{state}.pmtiles (with --pmtiles flag)

R2 Upload Paths:
  enrichment/terrain/saddles_{state}.pmtiles
  enrichment/terrain/benches_{state}.pmtiles
  enrichment/terrain/terrain_features_{state}.pmtiles
        """
    )

    parser.add_argument("--input", "-i",
                        help="Input DEM GeoTIFF file")
    parser.add_argument("--output", "-o",
                        help="Output directory (default: output/enrichment/terrain)")
    parser.add_argument("--bbox",
                        help="Bounding box: minx,miny,maxx,maxy (clip input to bbox)")
    parser.add_argument("--features", "-f",
                        help="Features to extract (comma-separated): saddles,benches,funnels,bedding_slopes")
    parser.add_argument("--state", "-s",
                        help="State abbreviation for output naming")
    parser.add_argument("--pmtiles", action="store_true",
                        help="Generate PMTiles output")
    parser.add_argument("--upload", action="store_true",
                        help="Upload PMTiles to Cloudflare R2")
    parser.add_argument("--check-deps", action="store_true",
                        help="Check dependencies and exit")
    parser.add_argument("--export-slope", action="store_true",
                        help="Also export slope raster")
    parser.add_argument("--export-tpi", action="store_true",
                        help="Also export TPI raster")

    args = parser.parse_args()

    ensure_directories()

    # Check dependencies
    deps = check_dependencies()

    if args.check_deps:
        log("Dependency check complete")
        for dep, available in deps.items():
            status = "OK" if available else "MISSING"
            log(f"  {dep}: {status}")
        return

    if not deps['gdal'] or not deps['numpy'] or not deps['shapely']:
        log("Required dependencies not available", "ERROR")
        log("Install with: pip install gdal numpy shapely")
        sys.exit(1)

    # Check for input file
    if not args.input:
        log("Input file required: --input dem.tif", "ERROR")
        parser.print_help()
        sys.exit(1)

    # Validate input file
    if not os.path.exists(args.input):
        log(f"Input file not found: {args.input}", "ERROR")
        sys.exit(1)

    # Parse features
    features = None
    if args.features:
        features = [f.strip().lower() for f in args.features.split(",")]
        valid_features = ['saddles', 'benches', 'funnels', 'bedding_slopes']
        invalid = [f for f in features if f not in valid_features]
        if invalid:
            log(f"Invalid features: {invalid}", "ERROR")
            log(f"Valid features: {valid_features}")
            sys.exit(1)

    # Handle bbox clipping
    dem_path = args.input
    if args.bbox:
        try:
            bbox = [float(x.strip()) for x in args.bbox.split(",")]
            if len(bbox) != 4:
                raise ValueError("Need 4 coordinates")

            # Clip DEM to bbox using GDAL
            from osgeo import gdal

            log(f"Clipping DEM to bbox: {bbox}")
            clipped_path = tempfile.mktemp(suffix=".tif")

            gdal.Translate(
                clipped_path,
                dem_path,
                projWin=[bbox[0], bbox[3], bbox[2], bbox[1]]  # ulx, uly, lrx, lry
            )

            dem_path = clipped_path
            log(f"  Clipped DEM: {clipped_path}")

        except Exception as e:
            log(f"Error clipping to bbox: {e}", "ERROR")
            sys.exit(1)

    # Run analysis
    log("=" * 70)
    log("TERRAIN ANALYSIS")
    log("=" * 70)
    log(f"Input: {args.input}")
    log(f"Features: {features or 'all'}")
    log(f"PMTiles: {args.pmtiles}")
    log(f"Upload: {args.upload}")
    log("=" * 70)

    try:
        results = analyze_terrain(
            dem_path=dem_path,
            output_dir=args.output,
            features=features,
            state=args.state,
            generate_pmtiles=args.pmtiles,
            upload=args.upload
        )

        # Optional raster exports
        if args.export_slope or args.export_tpi:
            analyzer = TerrainAnalyzer(dem_path, Path(args.output) if args.output else TERRAIN_DIR)

            if args.export_slope:
                slope_path = analyzer.export_slope_raster()
                results["files_created"].append(slope_path)

            if args.export_tpi:
                tpi_path = analyzer.export_tpi_raster()
                results["files_created"].append(tpi_path)

        # Summary
        log("")
        log("=" * 70)
        log("ANALYSIS COMPLETE")
        log("=" * 70)
        log(f"Features extracted:")
        for feat_type, count in results["features_extracted"].items():
            log(f"  {feat_type}: {count}")
        log(f"\nFiles created: {len(results['files_created'])}")
        for f in results["files_created"]:
            log(f"  {f}")
        if results["uploaded"]:
            log(f"\nUploaded to R2: {len(results['uploaded'])}")
            for url in results["uploaded"]:
                log(f"  {url}")

    except Exception as e:
        log(f"Analysis failed: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Cleanup temp file if created
        if args.bbox and dem_path != args.input:
            try:
                os.remove(dem_path)
            except:
                pass


if __name__ == "__main__":
    main()
