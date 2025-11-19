#!/bin/bash

echo "============================================"
echo "RAM Configuration Report"
echo "============================================"
echo ""

echo "=== Current Memory Usage ==="
free -h
echo ""

echo "=== Memory Array Information ==="
sudo dmidecode -t 16
echo ""

echo "=== Installed Memory Modules ==="
sudo dmidecode -t memory | grep -A 20 "Memory Device"
echo ""

echo "=== Memory Speed and Type ==="
sudo dmidecode -t memory | grep -E "Type:|Speed:|Manufacturer:|Part Number:|Size:|Locator:"
