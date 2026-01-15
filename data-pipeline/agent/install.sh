#!/bin/bash
# Install the Data Agent as a systemd service
# Run with: sudo bash install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/data-agent.service"

echo "=== MyGSpot Data Agent Installer ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo: sudo bash $0"
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install aiohttp requests

# Create log directory
mkdir -p "$SCRIPT_DIR"
touch "$SCRIPT_DIR/agent.log"
touch "$SCRIPT_DIR/agent_error.log"
chown exx:exx "$SCRIPT_DIR"/*.log

# Copy service file
echo "Installing systemd service..."
cp "$SERVICE_FILE" /etc/systemd/system/data-agent.service

# Reload systemd
systemctl daemon-reload

# Enable and start
echo "Enabling service..."
systemctl enable data-agent.service

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Commands:"
echo "  Start:   sudo systemctl start data-agent"
echo "  Stop:    sudo systemctl stop data-agent"
echo "  Status:  sudo systemctl status data-agent"
echo "  Logs:    tail -f $SCRIPT_DIR/agent.log"
echo ""
echo "Run once (test): python3 $SCRIPT_DIR/data_agent.py --once"
echo ""
