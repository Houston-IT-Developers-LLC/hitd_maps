#!/usr/bin/env python3
"""Convert MBTiles to PMTiles format."""

import sqlite3
import struct
import gzip
import json
import sys
import os
from pathlib import Path

def convert_mbtiles_to_pmtiles(mbtiles_path, pmtiles_path):
    """Convert MBTiles to PMTiles format using pmtiles library."""
    try:
        from pmtiles.convert import mbtiles_to_pmtiles
        print(f"Converting {mbtiles_path} to {pmtiles_path}...")
        # Get maxzoom from mbtiles metadata
        import sqlite3
        conn = sqlite3.connect(mbtiles_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE name='maxzoom'")
        row = cursor.fetchone()
        maxzoom = int(row[0]) if row else 16
        conn.close()
        print(f"Max zoom: {maxzoom}")
        mbtiles_to_pmtiles(mbtiles_path, pmtiles_path, maxzoom)
        print(f"Done! Output: {pmtiles_path}")
        return True
    except ImportError:
        print("pmtiles library not found, using manual conversion...")
        return manual_convert(mbtiles_path, pmtiles_path)
    except Exception as e:
        print(f"Error: {e}")
        return False

def manual_convert(mbtiles_path, pmtiles_path):
    """Manual conversion fallback."""
    print("Manual conversion not implemented - please install pmtiles:")
    print("  pip3 install pmtiles")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 mbtiles_to_pmtiles.py <input.mbtiles> <output.pmtiles>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    success = convert_mbtiles_to_pmtiles(input_path, output_path)
    sys.exit(0 if success else 1)
