#!/bin/bash

# Script to properly mount secondary drive and make it visible in Nautilus
# This will move the mount point from /mnt/storage to /media/ygg/storage

set -e  # Exit on error

echo "============================================"
echo "Secondary Drive Setup Script"
echo "============================================"
echo ""
echo "This script will:"
echo "  1. Create /media/ygg/storage directory"
echo "  2. Backup /etc/fstab"
echo "  3. Add drive to /etc/fstab with Nautilus-friendly options"
echo "  4. Unmount from /mnt/storage"
echo "  5. Mount at /media/ygg/storage"
echo "  6. Fix ownership permissions"
echo ""
echo "Drive UUID: c84e71ba-f6a3-4163-be6f-d50b22974ce4"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Step 1: Create mount point
echo ""
echo "[1/6] Creating mount point at /media/ygg/storage..."
sudo mkdir -p /media/ygg/storage

# Step 2: Backup fstab
echo ""
echo "[2/6] Backing up /etc/fstab..."
BACKUP_FILE="/etc/fstab.backup-$(date +%Y%m%d-%H%M%S)"
sudo cp /etc/fstab "$BACKUP_FILE"
echo "Backup created: $BACKUP_FILE"

# Step 3: Add to fstab
echo ""
echo "[3/6] Adding drive to /etc/fstab..."
# Check if entry already exists
if grep -q "c84e71ba-f6a3-4163-be6f-d50b22974ce4" /etc/fstab; then
    echo "WARNING: UUID already exists in /etc/fstab"
    echo "Please check $BACKUP_FILE and edit /etc/fstab manually if needed"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
else
    echo 'UUID=c84e71ba-f6a3-4163-be6f-d50b22974ce4 /media/ygg/storage ext4 defaults,nofail,x-gvfs-show 0 2' | sudo tee -a /etc/fstab
    echo "Entry added to /etc/fstab"
fi

# Step 4: Unmount from old location
echo ""
echo "[4/6] Unmounting from /mnt/storage..."
if mountpoint -q /mnt/storage; then
    sudo umount /mnt/storage
    echo "Unmounted successfully"
else
    echo "Already unmounted or not a mount point"
fi

# Step 5: Mount at new location
echo ""
echo "[5/6] Mounting at /media/ygg/storage..."
sudo mount /media/ygg/storage
echo "Mounted successfully"

# Step 6: Fix ownership
echo ""
echo "[6/6] Fixing ownership permissions..."
sudo chown -R ygg:ygg /media/ygg/storage
echo "Ownership set to ygg:ygg"

# Verify
echo ""
echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo ""
echo "Mount status:"
df -h /media/ygg/storage
echo ""
echo "Permissions:"
ls -la /media/ygg/storage | head -5
echo ""
echo "The drive should now be visible in Nautilus."
echo "You may need to restart Nautilus or press F5 to refresh."
echo ""
echo "To restart Nautilus: nautilus -q && nautilus &"
