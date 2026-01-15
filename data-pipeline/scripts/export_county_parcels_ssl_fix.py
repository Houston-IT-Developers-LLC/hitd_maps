#!/usr/bin/env python3
"""
County Parcel Exporter with SSL fix
Adds SSL certificate verification bypass for problematic servers
"""
import ssl
import urllib.request
import sys
import os

# Disable SSL verification globally for problematic servers
ssl._create_default_https_context = ssl._create_unverified_context

# Import and run the main script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_county_parcels import main

if __name__ == "__main__":
    main()
