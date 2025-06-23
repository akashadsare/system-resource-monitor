#!/bin/bash
# System optimization script
echo "Running kernel parameter optimizations..."
# Adjust swappiness
sysctl vm.swappiness=10

# Increase file handles
sysctl fs.file-max=2097152
ulimit -n 65536

# Disk scheduler tuning
echo deadline > /sys/block/sda/queue/scheduler