# Samsung 990 PRO 4TB Migration Guide

## Overview

This guide will help you migrate data from your Kingston SNV2S 500GB to the new Samsung 990 PRO 4TB and physically swap the drives.

**Current Setup:**
- **nvme1n1 (Slot 1):** SK Hynix 1TB - System Drive (/) - Keep as-is
- **nvme0n1 (Slot 2):** Kingston 500GB - Storage (/media/ygg/storage) - Replace with Samsung

**Goal:**
- Replace Kingston 500GB with Samsung 990 PRO 4TB
- Migrate all data from old drive to new drive
- Maintain same mount point and permissions

---

## Pre-Migration Checklist

### 1. Check Current Storage Usage

```bash
df -h /media/ygg/storage
```

**Current data on Kingston:** ~430GB used of 458GB

### 2. Verify What's on the Drive

```bash
ls -lah /media/ygg/storage
du -sh /media/ygg/storage/*
```

**Current contents:**
- `poetry-cache/` - Poetry package cache
- `poetry-virtualenvs/` - Poetry virtual environments (currently owned by root)
- `screencasts/` - Your screencasts
- `lost+found/` - System recovery folder

### 3. Backup Important Data (Optional but Recommended)

If you have critical screencasts or data, consider backing up to external storage or cloud before proceeding.

---

## Migration Methods

Choose **ONE** of these methods:

---

## Method 1: Direct Copy (Recommended - Simplest)

This method copies data while both drives are installed, then swaps them physically.

### Step 1: Install Samsung 990 PRO Temporarily

1. **Shut down** your computer completely
2. **Open case** and locate your M.2 slots
3. **Install Samsung 990 PRO** in an available slot (if you have a 3rd slot) OR temporarily use a PCIe adapter card
4. **Boot up** and verify drive is detected:

```bash
lsblk | grep nvme
```

You should see a new `nvme2n1` (or similar) device.

### Step 2: Format the New Samsung Drive

```bash
# Identify the new drive (it will be the one without partitions)
lsblk

# Create partition (replace nvme2n1 with actual device name)
sudo parted /dev/nvme2n1 mklabel gpt
sudo parted /dev/nvme2n1 mkpart primary ext4 0% 100%

# Format the partition
sudo mkfs.ext4 -L "samsung-storage" /dev/nvme2n1p1

# Create temporary mount point
sudo mkdir -p /mnt/samsung-temp

# Mount it
sudo mount /dev/nvme2n1p1 /mnt/samsung-temp

# Set ownership
sudo chown -R ygg:ygg /mnt/samsung-temp
```

### Step 3: Copy All Data

```bash
# Copy everything from Kingston to Samsung
# This will take 30-60 minutes depending on data size
sudo rsync -avxHAX --progress /media/ygg/storage/ /mnt/samsung-temp/

# Verify the copy
du -sh /media/ygg/storage
du -sh /mnt/samsung-temp

# Compare checksums (optional but recommended)
cd /media/ygg/storage && find . -type f -exec md5sum {} \; | sort > /tmp/kingston_checksums.txt
cd /mnt/samsung-temp && find . -type f -exec md5sum {} \; | sort > /tmp/samsung_checksums.txt
diff /tmp/kingston_checksums.txt /tmp/samsung_checksums.txt
```

If `diff` returns nothing, the copy is perfect.

### Step 4: Update fstab with New Drive UUID

```bash
# Get the UUID of the new Samsung drive
sudo blkid /dev/nvme2n1p1

# Note the UUID (something like: a1b2c3d4-e5f6-7890-abcd-ef1234567890)

# Backup fstab
sudo cp /etc/fstab /etc/fstab.backup-$(date +%Y%m%d-%H%M%S)

# Edit fstab - replace the old Kingston UUID with Samsung UUID
sudo nano /etc/fstab

# Find this line:
# UUID=c84e71ba-f6a3-4163-be6f-d50b22974ce4 /media/ygg/storage ext4 defaults,nofail,x-gvfs-show 0 2

# Replace with new UUID:
# UUID=<NEW-SAMSUNG-UUID> /media/ygg/storage ext4 defaults,nofail,x-gvfs-show 0 2

# Save and exit (Ctrl+O, Enter, Ctrl+X)
```

### Step 5: Test the Configuration

```bash
# Unmount both drives
sudo umount /media/ygg/storage
sudo umount /mnt/samsung-temp

# Test mount with new fstab
sudo mount /media/ygg/storage

# Verify it mounted the Samsung drive
df -h /media/ygg/storage
lsblk -f | grep samsung

# Check data is accessible
ls -lah /media/ygg/storage
```

### Step 6: Physical Swap

1. **Shut down** completely
2. **Remove Kingston drive** from Slot 2
3. **Move Samsung drive** to Slot 2 (where Kingston was)
4. **Boot up**

The system should automatically mount the Samsung at `/media/ygg/storage`.

### Step 7: Verify Everything Works

```bash
# Check mount
df -h /media/ygg/storage

# Verify device
lsblk | grep nvme

# Test access
ls -lah /media/ygg/storage

# Check permissions
touch /media/ygg/storage/test.txt && rm /media/ygg/storage/test.txt
```

---

## Method 2: Clone Drive (Alternative)

If you prefer to clone the entire drive byte-for-byte:

### Using Clonezilla (Bootable USB)

1. Download **Clonezilla Live** ISO
2. Create bootable USB
3. Boot from USB
4. Select **device-device** clone
5. Choose Kingston as source, Samsung as destination
6. Start clone process
7. After completion, swap drives physically

### Using dd (Advanced - Use with Caution)

```bash
# THIS WILL OVERWRITE THE ENTIRE SAMSUNG DRIVE
# Make absolutely sure you have the right source/destination

sudo dd if=/dev/nvme0n1 of=/dev/nvme2n1 bs=64K status=progress conv=noerror,sync
```

⚠️ **Warning:** `dd` is dangerous. One typo can destroy your system drive. Only use if you're comfortable with it.

---

## Method 3: Fresh Start (Cleanest)

If your data is mostly caches and virtualenvs that can be regenerated:

### Step 1: List What You Actually Need to Keep

```bash
# Check screencasts size
du -sh /media/ygg/storage/screencasts

# Poetry stuff can be regenerated, so you might only need screencasts
```

### Step 2: Copy Only Essential Data

```bash
# Mount new Samsung (as in Method 1, Steps 1-2)
# Then copy only what you need:

cp -a /media/ygg/storage/screencasts /mnt/samsung-temp/
```

### Step 3: Reinstall/Recache Poetry Later

Poetry will rebuild caches and virtualenvs as needed when you use them.

---

## Post-Migration Tasks

### 1. Verify Performance

```bash
# Install fio if not present
sudo apt install fio

# Test read speed
fio --name=read_test --ioengine=libaio --iodepth=32 --rw=read --bs=1m --direct=1 --size=4g --numjobs=1 --runtime=30 --group_reporting --filename=/media/ygg/storage/test_file

# Test write speed
fio --name=write_test --ioengine=libaio --iodepth=32 --rw=write --bs=1m --direct=1 --size=4g --numjobs=1 --runtime=30 --group_reporting --filename=/media/ygg/storage/test_file

# Clean up test file
rm /media/ygg/storage/test_file
```

You should see ~7,000+ MB/s reads and ~6,500+ MB/s writes.

### 2. Update Poetry Cache Locations (if needed)

If Poetry was configured to use the old drive, verify paths:

```bash
poetry config cache-dir
poetry config virtualenvs.path
```

### 3. Re-enable TRIM (SSD optimization)

```bash
# Check if TRIM is enabled
sudo systemctl status fstrim.timer

# Enable weekly TRIM
sudo systemctl enable fstrim.timer
sudo systemctl start fstrim.timer
```

### 4. Monitor Drive Health

```bash
# Install nvme-cli if not present
sudo apt install nvme-cli

# Check Samsung drive health
sudo nvme smart-log /dev/nvme0n1
```

---

## What to Do with Old Kingston Drive

### Option 1: Keep as External Backup Drive
- Buy USB-to-M.2 enclosure (~$20-30)
- Use Kingston as portable backup storage

### Option 2: Sell It
- Securely wipe first:
  ```bash
  sudo nvme format /dev/nvmeXn1 --ses=1
  ```
- Sell on Kijiji/Facebook Marketplace

### Option 3: Repurpose
- Install in another PC
- Use as boot drive for secondary system

### Option 4: Keep as Emergency Spare
- Store safely in anti-static bag

---

## Troubleshooting

### Drive Not Detected After Install

```bash
# Reseat the drive (remove and reinstall)
# Check BIOS/UEFI settings
# Verify M.2 slot isn't disabled
```

### Permission Errors

```bash
sudo chown -R ygg:ygg /media/ygg/storage
sudo chmod -R u+rwX,go+rX /media/ygg/storage
```

### Mount Fails on Boot

```bash
# Check fstab syntax
sudo mount -a

# View errors
journalctl -xe | grep mount
```

### System Boots to Emergency Mode

1. Boot from live USB
2. Check/fix fstab:
   ```bash
   sudo mount /dev/nvme1n1p3 /mnt  # Your root partition
   sudo nano /mnt/etc/fstab
   # Fix the UUID or comment out the problematic line
   ```

---

## Migration Checklist

- [ ] Backup critical data (screencasts, important files)
- [ ] Verify current storage usage (should be ~430GB)
- [ ] Install Samsung 990 PRO drive
- [ ] Format and partition new drive
- [ ] Copy data using rsync or preferred method
- [ ] Verify copy integrity (checksums match)
- [ ] Get UUID of new Samsung drive
- [ ] Update /etc/fstab with new UUID
- [ ] Test mount before physical swap
- [ ] Shut down and physically move Samsung to Slot 2
- [ ] Remove Kingston drive
- [ ] Boot up and verify auto-mount
- [ ] Test read/write permissions
- [ ] Run performance benchmarks
- [ ] Enable TRIM timer
- [ ] Decide what to do with old Kingston drive

---

## Expected Timeline

- **Data copy:** 30-60 minutes (for 430GB)
- **Verification:** 10-15 minutes
- **Physical swap:** 10-15 minutes
- **Total:** ~1.5-2 hours

---

## Need Help?

If you run into issues during migration:

1. **Don't panic** - your data is still on the Kingston until you wipe it
2. Check the troubleshooting section above
3. Boot from live USB if system won't boot
4. Your original system drive (SK Hynix) is untouched throughout this process

---

## Performance Expectations

After migration, you should see:

**Before (Kingston NV2):**
- Sequential Read: ~3,500 MB/s
- Sequential Write: ~2,100 MB/s
- Random 4K: ~300K IOPS

**After (Samsung 990 PRO):**
- Sequential Read: ~7,450 MB/s (**2.1x faster**)
- Sequential Write: ~6,900 MB/s (**3.3x faster**)
- Random 4K: ~1,400K IOPS (**4.7x faster**)

You'll notice significantly faster:
- Large file transfers
- Video editing workflows
- Virtual environment loading
- Application launches from storage drive

---

Good luck with the migration! 🚀
