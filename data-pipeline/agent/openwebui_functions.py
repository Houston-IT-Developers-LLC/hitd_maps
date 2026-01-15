"""
Open WebUI Custom Functions for MyGSpot Data Pipeline
======================================================
Import these in Open WebUI: Settings → Admin → Functions → Import

These give the LLM autonomous capabilities to:
- Check API health
- Run scrapers
- Monitor data pipeline
- Upload to R2
"""

import subprocess
import json
import os
from typing import Optional

# Base path for the data pipeline
PIPELINE_DIR = "/home/exx/Documents/C/hitd_maps/data-pipeline"


class Tools:
    """Tools available to the LLM in Open WebUI"""

    def __init__(self):
        self.valves = self.Valves()

    class Valves:
        """Configuration for the tools"""
        PIPELINE_DIR: str = "/home/exx/Documents/C/hitd_maps/data-pipeline"
        OLLAMA_HOST: str = "http://10.8.0.1:11434"

    def check_api_health(self, api_name: str = "tx_statewide") -> str:
        """
        Check the health of a parcel data API.

        Args:
            api_name: One of: tx_statewide, fl_statewide, ny_statewide, ca_la_county, oh_statewide

        Returns:
            JSON string with API status, record count, and health info
        """
        apis = {
            "tx_statewide": "https://feature.stratmap.tnris.org/arcgis/rest/services/Land_Parcels/Statewide_Land_Parcels/MapServer/0",
            "fl_statewide": "https://ca.dep.state.fl.us/arcgis/rest/services/OpenData/PARCELS/MapServer/0",
            "ny_statewide": "https://services6.arcgis.com/EbVsqZ18sv1kVJ3k/arcgis/rest/services/NYS_Tax_Parcels_Public/FeatureServer/0",
            "ca_la_county": "https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0",
            "oh_statewide": "https://gis.ohiosos.gov/arcgis/rest/services/OpenData/OpenData/MapServer/0",
        }

        if api_name not in apis:
            return json.dumps({"error": f"Unknown API. Available: {list(apis.keys())}"})

        url = apis[api_name]
        try:
            import requests
            # Get record count
            resp = requests.get(f"{url}/query?where=1=1&returnCountOnly=true&f=json", timeout=30)
            data = resp.json()
            count = data.get("count", 0)

            return json.dumps({
                "api": api_name,
                "status": "healthy",
                "record_count": count,
                "url": url
            })
        except Exception as e:
            return json.dumps({
                "api": api_name,
                "status": "error",
                "error": str(e)
            })

    def run_data_agent(self, mode: str = "once") -> str:
        """
        Run the autonomous data agent to check APIs and trigger scraping.

        Args:
            mode: "once" for single cycle, "check" for API check only

        Returns:
            Agent execution output
        """
        try:
            cmd = ["python3", f"{PIPELINE_DIR}/agent/data_agent.py", f"--{mode}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=PIPELINE_DIR)
            return result.stdout or result.stderr or "Agent completed"
        except subprocess.TimeoutExpired:
            return "Agent timed out after 5 minutes"
        except Exception as e:
            return f"Error running agent: {e}"

    def run_scraper(self, state: str, county: Optional[str] = None) -> str:
        """
        Run the parcel scraper for a specific state/county.

        Args:
            state: Two-letter state code (e.g., "TX", "FL", "CA")
            county: Optional county name

        Returns:
            Scraper output
        """
        try:
            cmd = ["python3", f"{PIPELINE_DIR}/scripts/export_county_parcels.py", "--state", state.upper()]
            if county:
                cmd.extend(["--county", county.lower()])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, cwd=PIPELINE_DIR)
            return result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout
        except subprocess.TimeoutExpired:
            return "Scraper still running (backgrounded after 1 hour)"
        except Exception as e:
            return f"Error: {e}"

    def get_pipeline_status(self) -> str:
        """
        Get current status of the data pipeline.

        Returns:
            JSON with disk usage, file counts, recent activity
        """
        try:
            # Get disk usage
            du_result = subprocess.run(
                ["du", "-sh", f"{PIPELINE_DIR}/output"],
                capture_output=True, text=True
            )
            disk_usage = du_result.stdout.strip().split()[0] if du_result.stdout else "unknown"

            # Count files
            geojson_count = subprocess.run(
                ["find", f"{PIPELINE_DIR}/output/geojson", "-name", "*.geojson", "-type", "f"],
                capture_output=True, text=True
            )
            file_count = len(geojson_count.stdout.strip().split("\n")) if geojson_count.stdout.strip() else 0

            # Get recent log
            log_path = f"{PIPELINE_DIR}/agent/agent.log"
            recent_log = ""
            if os.path.exists(log_path):
                with open(log_path) as f:
                    lines = f.readlines()
                    recent_log = "".join(lines[-10:])

            return json.dumps({
                "disk_usage": disk_usage,
                "geojson_files": file_count,
                "recent_activity": recent_log[-500:] if recent_log else "No recent activity"
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def upload_to_r2(self, file_type: str = "pmtiles") -> str:
        """
        Upload files to Cloudflare R2.

        Args:
            file_type: "pmtiles", "geojson", or "all"

        Returns:
            Upload status
        """
        scripts = {
            "pmtiles": "upload_pmtiles_to_r2.py",
            "geojson": "upload_all_to_r2.py",
            "all": "upload_all_to_r2.py"
        }

        if file_type not in scripts:
            return f"Unknown file type. Available: {list(scripts.keys())}"

        try:
            cmd = ["python3", f"{PIPELINE_DIR}/scripts/{scripts[file_type]}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, cwd=PIPELINE_DIR)
            return result.stdout[-1000:] if result.stdout else result.stderr
        except Exception as e:
            return f"Error: {e}"

    def list_available_states(self) -> str:
        """
        List all states with available parcel data configurations.

        Returns:
            JSON list of states and their completion status
        """
        # This would read from your COUNTY_CONFIGS in export_county_parcels.py
        states = {
            "complete": ["AK", "CA", "CO", "CT", "DE", "HI", "IA", "MA", "ND", "NH", "NV", "SC", "TN", "UT", "WV"],
            "partial": ["TX", "FL", "NY", "OH", "PA", "GA", "MI", "WI", "MN", "MO", "AL", "KY", "LA", "MS", "NE", "NM", "OR", "SD", "WY", "AZ", "ID", "KS", "IL"],
            "not_started": ["IN", "MD", "NC", "NJ", "VA", "WA", "MT", "AR", "OK", "ME", "VT", "RI", "DC"]
        }
        return json.dumps(states, indent=2)


# For Open WebUI to discover the tools
def get_tools():
    return Tools()
