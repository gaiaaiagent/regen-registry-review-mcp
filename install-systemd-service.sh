#!/bin/bash

# Registry Review REST API - Systemd Service Installation
# This script installs and enables the systemd service for automatic restart

set -e

echo "======================================"
echo "Registry Review REST API - Installation"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run with sudo"
    echo "Usage: sudo bash install-systemd-service.sh"
    exit 1
fi

# Create logs directory if it doesn't exist
echo "1. Creating logs directory..."
mkdir -p /opt/projects/registry-eliza/regen-registry-review-mcp/logs
chown -R shawn:shawn /opt/projects/registry-eliza/regen-registry-review-mcp/logs
echo "   ✓ Logs directory ready"

# Copy service file
echo ""
echo "2. Installing systemd service..."
cp /tmp/registry-review-api.service /etc/systemd/system/
chmod 644 /etc/systemd/system/registry-review-api.service
echo "   ✓ Service file installed"

# Reload systemd
echo ""
echo "3. Reloading systemd daemon..."
systemctl daemon-reload
echo "   ✓ Daemon reloaded"

# Enable service to start on boot
echo ""
echo "4. Enabling service to start on boot..."
systemctl enable registry-review-api.service
echo "   ✓ Service enabled"

# Start the service
echo ""
echo "5. Starting Registry Review REST API..."
systemctl start registry-review-api.service

# Wait for startup
sleep 5

# Check status
echo ""
echo "======================================"
echo "Installation Complete!"
echo "======================================"
echo ""

if systemctl is-active --quiet registry-review-api; then
    echo "✅ registry-review-api.service is RUNNING"
    echo ""

    # Test if API is responding
    response=$(curl -s -o /dev/null -w "%{http_code}" -m 5 http://localhost:8003/ 2>/dev/null || echo "timeout")
    if [ "$response" = "200" ]; then
        echo "✅ API responding on port 8003"
    else
        echo "⚠️  API not responding yet (may still be starting)"
    fi
else
    echo "❌ Service failed to start"
    echo ""
    echo "Check logs with:"
    echo "  sudo journalctl -u registry-review-api -n 50"
fi

echo ""
echo "======================================"
echo "Service Details:"
echo "======================================"
echo "  Port:     8003"
echo "  Docs:     http://localhost:8003/docs"
echo "  Logs:     /opt/projects/registry-eliza/regen-registry-review-mcp/logs/rest-api.log"
echo ""
echo "Useful Commands:"
echo "  sudo systemctl status registry-review-api   # Check status"
echo "  sudo systemctl restart registry-review-api  # Restart service"
echo "  sudo systemctl stop registry-review-api     # Stop service"
echo "  sudo journalctl -u registry-review-api -f   # Follow logs"
echo ""
