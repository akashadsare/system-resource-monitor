#!/bin/bash
# System optimization script

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root"
    exit 1
fi

echo "Running kernel parameter optimizations..."

# Kernel parameter tuning
echo "1. Adjusting kernel parameters..."

# Virtual memory settings
sysctl -w vm.swappiness=10
sysctl -w vm.vfs_cache_pressure=50
sysctl -w vm.dirty_ratio=10
sysctl -w vm.dirty_background_ratio=5

# File handle limits
echo "2. Increasing file handle limits..."
sysctl -w fs.file-max=2097152
ulimit -n 65536

# Network optimizations
echo "3. Optimizing network settings..."
sysctl -w net.core.rmem_max=16777216
sysctl -w net.core.wmem_max=16777216
sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"
sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216"
sysctl -w net.ipv4.tcp_congestion_control=cubic

# I/O scheduler optimization
echo "4. Setting I/O scheduler..."
for DISK in /sys/block/sd*/queue/scheduler; do
    if [ -f "$DISK" ]; then
        echo deadline > "$DISK"
        echo "Set deadline scheduler for ${DISK}"
    fi
done

# Clear filesystem buffers and caches
echo "5. Flushing filesystem buffers..."
sync

echo "6. Clearing caches..."
echo 3 > /proc/sys/vm/drop_caches

# Apply changes permanently
echo "7. Making changes persistent..."
cat > /etc/sysctl.d/99-performance.conf << EOF
# Virtual Memory
vm.swappiness = 10
vm.vfs_cache_pressure = 50
vm.dirty_ratio = 10
vm.dirty_background_ratio = 5

# File handles
fs.file-max = 2097152

# Network
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_congestion_control = cubic
EOF

# Reload sysctl settings
sysctl --system

echo "System optimization completed successfully!"
echo "Note: Some changes require a system restart to take full effect."