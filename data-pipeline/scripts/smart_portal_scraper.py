#!/usr/bin/env python3
"""
Smart Portal Scraper: Download real GIS portals, save HTML, extract endpoints with AI
======================================================================================
"""

import requests
import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

OLLAMA_HOST = "http://10.8.0.1:11434"
MODEL = "llama3.3:70b"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Known working GIS portal patterns
PORTAL_PATTERNS = [
    "https://{county}.maps.arcgis.com",
    "https://gis.{county}.gov",
    "https://maps.{county}.gov",
    "https://{county}gis.com",
    "https://gis.{county}county{state}.gov",
    "https://maps.{county}county{state}.gov",
]

PRIORITY_COUNTIES = {
    "NE": [("douglas", "Douglas County (Omaha)"), ("lancaster", "Lancaster County (Lincoln)")],
    "KS": [("johnson", "Johnson County (KC metro)"), ("sedgwick", "Sedgwick County (Wichita)")],
    "AL": [("jefferson", "Jefferson County (Birmingham)"), ("mobile", "Mobile County")],
    "MS": [("hinds", "Hinds County (Jackson)"), ("harrison", "Harrison County (Gulfport)")],
}

def download_portal_page(url):
    """Download a GIS portal page"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text, resp.url
    except:
        pass
    return None, None

def save_portal_html(county_name, state, html_content):
    """Save portal HTML for AI analysis"""
    output_dir = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/data/portal_html")
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / f"{state}_{county_name}.html"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return filepath

def ask_ai_to_extract_endpoints(html_content, county_name, state):
    """Have AI extract REST endpoints from actual HTML"""

    # Limit HTML to first 50K chars to avoid token limits
    html_sample = html_content[:50000]

    prompt = f"""Analyze this HTML from {county_name} County, {state} GIS portal.

Find ArcGIS REST API endpoints for parcel data. Look for:
1. Links containing "/arcgis/rest/services/"
2. FeatureServer or MapServer URLs
3. Layer numbers (e.g., /0, /1, /2)
4. Parcel-related service names

HTML Content:
{html_sample}

Return ONLY JSON (no markdown):
{{
  "endpoints": [
    {{"url": "full_url_here", "type": "FeatureServer/MapServer", "notes": "brief description"}},
    ...
  ]
}}

If no endpoints found, return {{"endpoints": []}}"""

    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 1000}
            },
            timeout=120
        )

        if resp.status_code == 200:
            response_text = resp.json().get('response', '').strip()

            # Extract JSON
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            elif "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
            else:
                return []

            result = json.loads(json_str)
            return result.get("endpoints", [])
    except Exception as e:
        print(f"    AI extraction error: {e}")

    return []

def verify_endpoint(url):
    """Test if endpoint works"""
    try:
        resp = requests.get(
            f"{url}/query",
            params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
            headers=HEADERS,
            timeout=20
        )
        if resp.status_code == 200:
            data = resp.json()
            if 'count' in data and data['count'] > 0:
                return True, data['count']
            elif 'error' in data:
                return False, f"Error: {data['error'].get('message', 'Unknown')}"
        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)[:100]

def find_portal_and_extract(county_slug, county_name, state):
    """Find portal, download it, extract endpoints"""

    print(f"\n{'='*60}")
    print(f"{county_name}, {state}")
    print(f"{'='*60}")

    # Try different portal patterns
    for pattern in PORTAL_PATTERNS:
        url = pattern.format(county=county_slug, state=state.lower())

        print(f"  Trying: {url}")
        html, final_url = download_portal_page(url)

        if html:
            print(f"  ✓ Downloaded {len(html):,} bytes")

            # Save HTML
            saved_path = save_portal_html(county_slug, state, html)
            print(f"  💾 Saved to: {saved_path}")

            # Extract endpoints with AI
            print(f"  🤖 AI extracting endpoints...")
            endpoints = ask_ai_to_extract_endpoints(html, county_name, state)

            if endpoints:
                print(f"  📍 Found {len(endpoints)} potential endpoints")

                verified = []
                for ep in endpoints:
                    url = ep.get('url')
                    if not url:
                        continue

                    print(f"    Testing: {url}")
                    works, result = verify_endpoint(url)

                    if works:
                        print(f"      ✓ VERIFIED: {result:,} features")
                        verified.append({
                            **ep,
                            "feature_count": result,
                            "verified": True
                        })
                    else:
                        print(f"      ✗ Failed: {result}")

                if verified:
                    return verified
            else:
                print(f"  ⚠️  No endpoints found in HTML")

        time.sleep(0.5)  # Rate limit

    return []

def main():
    all_results = {}

    for state, counties in PRIORITY_COUNTIES.items():
        all_results[state] = {}

        for county_slug, county_name in counties:
            endpoints = find_portal_and_extract(county_slug, county_name, state)
            if endpoints:
                all_results[state][county_name] = endpoints

    # Save results
    output_file = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/data/verified_endpoints.json")
    with open(output_file, 'w') as f:
        json.dump({
            "generated_at": "2026-01-24",
            "method": "smart_portal_scraper",
            "total_endpoints": sum(len(v) for state_data in all_results.values() for v in state_data.values()),
            "sources": all_results
        }, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Results saved to: {output_file}")
    print(f"Total verified endpoints: {sum(len(v) for state_data in all_results.values() for v in state_data.values())}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
