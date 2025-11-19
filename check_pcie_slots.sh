#!/bin/bash

echo "============================================"
echo "PCIe Slot Capabilities Report"
echo "============================================"
echo ""

echo "=== System Information ==="
echo "CPU: $(cat /proc/cpuinfo | grep "model name" | head -1 | cut -d: -f2 | xargs)"
echo "Motherboard: $(cat /sys/devices/virtual/dmi/id/board_vendor) $(cat /sys/devices/virtual/dmi/id/board_name)"
echo ""

echo "=== Current NVMe Drives ==="
lsblk -d -o NAME,SIZE,MODEL,TYPE | grep nvme
echo ""

echo "=== Detailed PCIe Link Capabilities for NVMe Devices ==="
echo ""

for device in /sys/class/nvme/nvme*/device; do
    if [ -e "$device" ]; then
        nvme_name=$(basename $(dirname $device))
        echo "--- $nvme_name ---"

        # Get the PCI address
        pci_addr=$(basename $(readlink -f $device))
        echo "PCI Address: $pci_addr"

        # Get model from block device
        if [ -e "/sys/block/${nvme_name}n1/device/model" ]; then
            model=$(cat /sys/block/${nvme_name}n1/device/model 2>/dev/null | xargs)
            echo "Model: $model"
        fi

        # Get current link speed and width
        if [ -e "$device/current_link_speed" ]; then
            echo "Current Link Speed: $(cat $device/current_link_speed 2>/dev/null)"
        fi

        if [ -e "$device/current_link_width" ]; then
            echo "Current Link Width: x$(cat $device/current_link_width 2>/dev/null)"
        fi

        # Get max link speed and width
        if [ -e "$device/max_link_speed" ]; then
            echo "Max Link Speed: $(cat $device/max_link_speed 2>/dev/null)"
        fi

        if [ -e "$device/max_link_width" ]; then
            echo "Max Link Width: x$(cat $device/max_link_width 2>/dev/null)"
        fi

        echo ""
    fi
done

echo "=== Detailed lspci Output for NVMe Controllers ==="
echo ""
sudo lspci -vvv 2>/dev/null | grep -B 3 -A 25 "Non-Volatile memory controller" | grep -E "^[0-9]|LnkCap:|LnkSta:|Speed|Width"

echo ""
echo "=== PCIe Generation Interpretation ==="
echo "2.5 GT/s = PCIe Gen 1.0"
echo "5 GT/s   = PCIe Gen 2.0"
echo "8 GT/s   = PCIe Gen 3.0"
echo "16 GT/s  = PCIe Gen 4.0"
echo "32 GT/s  = PCIe Gen 5.0"
echo ""

echo "=== Available M.2 Slots Analysis ==="
echo ""
echo "Currently installed NVMe drives: $(lsblk -d -o NAME | grep nvme | wc -l)"
echo ""
echo "Note: Most consumer motherboards have 2-3 M.2 slots."
echo "Check your motherboard documentation for exact slot count and individual PCIe gen support."
echo ""

echo "=== Motherboard Slot Information (requires sudo) ==="
echo ""
sudo dmidecode -t slot 2>/dev/null | grep -A 10 "M.2" || echo "M.2 slot information not available via dmidecode"
