#!/usr/bin/env python3
"""
Use Local Ollama AI to Find Working FeatureServer Endpoints
============================================================
Focus on FeatureServers (not MapServers) which support GeoJSON export
"""

import requests
import json
from pathlib import Path

OLLAMA_HOST = "http://10.8.0.1:11434"
MODEL = "llama3.3:70b"

# Priority states and their top counties
PRIORITY_TARGETS = {
    "DC": ["District of Columbia"],
    "NE": ["Douglas (Omaha)", "Lancaster (Lincoln)", "Sarpy"],
    "KS": ["Johnson (Overland Park)", "Sedgwick (Wichita)", "Shawnee (Topeka)"],
    "KY": ["Jefferson (Louisville)", "Fayette (Lexington)", "Kenton", "Boone"],
    "AL": ["Jefferson (Birmingham)", "Mobile", "Madison (Huntsville)", "Montgomery"],
    "GA": ["Fulton (Atlanta)", "DeKalb", "Gwinnett", "Cobb", "Clayton"],
    "OK": ["Oklahoma (OKC)", "Tulsa", "Cleveland (Norman)"],
    "IL": ["Kane (Aurora)", "Will", "Winnebago (Rockford)", "St. Clair"],
    "MS": ["Hinds (Jackson)", "Harrison (Gulfport)", "DeSoto (Memphis metro)"],
    "SC": ["Greenville", "Charleston", "Richland (Columbia)", "Spartanburg"],
}

def ask_ai(prompt):
    """Query Ollama AI"""
    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 1000
                }
            },
            timeout=120
        )
        if resp.status_code == 200:
            return resp.json().get('response', '').strip()
    except Exception as e:
        print(f"AI Error: {e}")
    return None

def find_featureserver_for_location(state_code, location_name):
    """Use AI to find FeatureServer endpoints"""

    prompt = f"""Find ArcGIS REST FeatureServer (NOT MapServer) endpoints for {location_name}, {state_code} parcel data.

Requirements:
1. MUST be FeatureServer (ends with /FeatureServer/0 or similar)
2. MUST support GeoJSON export (f=geojson parameter)
3. Prefer official county/city government sources
4. Provide full URL to the service

Return ONLY a JSON object (no markdown, no explanation):
{{
  "found": true/false,
  "url": "https://example.com/.../FeatureServer/0",
  "source": "County Assessor / City GIS / State Portal",
  "confidence": "high/medium/low",
  "notes": "any important details"
}}

If no FeatureServer found, return {{"found": false}}"""

    print(f"\n🤖 AI searching for: {location_name}, {state_code}...")

    response = ask_ai(prompt)
    if not response:
        return None

    # Try to extract JSON from response
    try:
        # Handle markdown code blocks
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        elif "{" in response and "}" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
        else:
            json_str = response

        result = json.loads(json_str)

        if result.get("found"):
            print(f"  ✓ Found: {result.get('url')}")
            print(f"    Confidence: {result.get('confidence')}")
            print(f"    Source: {result.get('source')}")
            return result
        else:
            print(f"  ✗ Not found")
            return None

    except json.JSONDecodeError as e:
        print(f"  ✗ Failed to parse AI response: {e}")
        print(f"    Raw: {response[:200]}")
        return None

def verify_endpoint(url):
    """Verify a FeatureServer endpoint works"""
    try:
        # Test count query
        resp = requests.get(
            f"{url}/query",
            params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            if 'count' in data and data['count'] > 0:
                print(f"  ✓ VERIFIED: {data['count']:,} features")
                return True
            elif 'error' in data:
                print(f"  ✗ API Error: {data['error']}")
                return False
        print(f"  ✗ HTTP {resp.status_code}")
        return False
    except Exception as e:
        print(f"  ✗ Verification failed: {e}")
        return False

def main():
    results = {}

    for state, locations in PRIORITY_TARGETS.items():
        results[state] = {}

        for location in locations:
            ai_result = find_featureserver_for_location(state, location)

            if ai_result and ai_result.get('url'):
                # Verify it
                if verify_endpoint(ai_result['url']):
                    results[state][location] = ai_result
                else:
                    print(f"    ⚠️  Endpoint doesn't work")
            else:
                print(f"    ⚠️  No endpoint found")

    # Save results
    output_file = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/data/ai_featureservers.json")
    with open(output_file, 'w') as f:
        json.dump({
            "generated_at": "2026-01-24",
            "total_found": sum(len(v) for v in results.values()),
            "sources": results
        }, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Results saved to: {output_file}")
    print(f"Total endpoints found: {sum(len(v) for v in results.values())}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
