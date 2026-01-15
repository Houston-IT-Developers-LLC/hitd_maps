#!/bin/bash
# Setup autonomous AI agent environment
# This gives you Claude Code-like capabilities with your local Ollama

set -e

echo "=== Setting up Autonomous AI Agent Environment ==="
echo ""

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

echo ""
echo "Choose your setup:"
echo ""
echo "1) Open WebUI      - Web interface with agents, RAG, scheduled tasks"
echo "2) AnythingLLM     - Desktop app with autonomous agents"
echo "3) n8n + Ollama    - Workflow automation (cron-like triggers)"
echo "4) All of the above"
echo ""
read -p "Enter choice [1-4]: " choice

OLLAMA_HOST="http://10.8.0.1:11434"

case $choice in
    1|4)
        echo ""
        echo "=== Installing Open WebUI ==="
        docker pull ghcr.io/open-webui/open-webui:main
        docker run -d \
            --name open-webui \
            --network host \
            -e OLLAMA_BASE_URL=$OLLAMA_HOST \
            -e WEBUI_AUTH=false \
            -v open-webui:/app/backend/data \
            --restart always \
            ghcr.io/open-webui/open-webui:main
        echo "Open WebUI: http://localhost:3000"
        ;;&
    2|4)
        echo ""
        echo "=== Installing AnythingLLM ==="
        # AppImage for Linux
        wget -q https://s3.us-west-1.amazonaws.com/public.useanything.com/latest/AnythingLLMDesktop.AppImage -O ~/AnythingLLM.AppImage
        chmod +x ~/AnythingLLM.AppImage
        echo "AnythingLLM: ~/AnythingLLM.AppImage"
        ;;&
    3|4)
        echo ""
        echo "=== Installing n8n ==="
        docker pull n8nio/n8n
        docker run -d \
            --name n8n \
            -p 5678:5678 \
            -v n8n_data:/home/node/.n8n \
            -v /home/exx/Documents/C/hitd_maps:/data/project:ro \
            --restart always \
            n8nio/n8n
        echo "n8n: http://localhost:5678"
        ;;
esac

echo ""
echo "=== Setting up Cron-based Agent ==="
echo ""

# Create cron job for the data agent
CRON_CMD="0 */6 * * * cd /home/exx/Documents/C/hitd_maps/data-pipeline && /usr/bin/python3 agent/data_agent.py --once >> agent/cron.log 2>&1"

# Check if cron job already exists
if ! crontab -l 2>/dev/null | grep -q "data_agent.py"; then
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "Added cron job: runs every 6 hours"
else
    echo "Cron job already exists"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Access points:"
echo "  Open WebUI:  http://localhost:3000"
echo "  n8n:         http://localhost:5678"
echo "  Ollama API:  $OLLAMA_HOST"
echo ""
echo "The data agent will run automatically every 6 hours."
echo "To run manually: python3 agent/data_agent.py --once"
echo ""
