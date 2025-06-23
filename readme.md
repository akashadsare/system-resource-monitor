# System Resource Monitor and Optimizer

![System Monitoring Dashboard](https://via.placeholder.com/800x400?text=Resource+Monitoring+Dashboard)

A comprehensive framework for tracking system performance, identifying bottlenecks, and suggesting optimizations across multi-threaded environments.

## Features

- 📊 **Real-time Monitoring** of CPU, memory, disk, and network usage
- ⚠️ **Bottleneck Detection** with severity classification
- 🚀 **Optimization Suggestions** for each detected issue
- 📈 **Historical Reporting** in JSON format
- 🔄 **Git Integration** for version control of reports
- 🧵 **Multi-threaded Architecture** for concurrent monitoring
- ⚙️ **System Optimization** commands for performance tuning

## Requirements

- Python 3.8+
- psutil library (`pip install psutil`)
- Linux-based system (tested on Ubuntu 22.04, CentOS 7)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/system-resource-monitor.git
cd system-resource-monitor

# Install dependencies
pip install -r requirements.txt

# Make the script executable
chmod +x system_monitor.py
```

## Usage

### Docker Usage

> **Note:**
> - The optimization script (`optimize.sh`) requires a privileged container (`--privileged`) and a compatible Linux host. Some commands (like `sysctl` and disk scheduler tuning) may not work in minimal Docker images or non-Linux environments.
> - The default `python:3.8-slim` image does not include `sysctl` or support all kernel parameter changes. For full optimization support, use a more complete base image and ensure your host allows these operations.
> - Monitoring and reporting features work in all environments.

#### Build the Docker image
```bash
# From the project root
docker build -t system-resource-monitor .
```

#### Run the monitor (5 minutes example)
```bash
docker run --rm --name monitor system-resource-monitor python system_monitor.py --duration 300
```

#### Run with optimization and report
```bash
docker run --rm -v $(pwd):/app system-resource-monitor python system_monitor.py --optimize --report system_report.json
```

#### Run the optimization script only
```bash
docker run --rm --privileged system-resource-monitor ./optimize.sh
```

### Basic Monitoring (5 minutes)
```bash
./system_monitor.py --duration 300
```

### Generate Report with Optimization
```bash
./system_monitor.py --optimize --report system_report.json
```

### Custom Monitoring Configuration
```bash
# 2-second interval for 2 minutes
./system_monitor.py --interval 2 --duration 120
```

### Optimization Script
```bash
# Run standalone optimizations
./optimize.sh
```

## Configuration

Modify monitoring thresholds in `system_monitor.py`:
```python
self.thresholds = {
    'cpu': 80,          # CPU usage percentage
    'memory': 75,        # RAM usage percentage
    'disk': 85,          # Disk usage percentage
    'swap': 50           # Swap usage percentage
}
```

## Sample Report Output

```json
{
  "metadata": {
    "system": "Linux",
    "hostname": "server-01",
    "duration": "300 seconds"
  },
  "analysis": [
    {
      "timestamp": "2025-06-23T14:30:45.123456",
      "issues": [
        {
          "type": "CPU",
          "severity": "High",
          "message": "High CPU usage: 87.5%",
          "details": "Core loads: 92.1%, 85.3%, 79.8%, 93.2%",
          "suggestion": "Check CPU-intensive processes with 'top' command..."
        },
        {
          "type": "Disk",
          "severity": "Critical",
          "message": "Disk space low: / (92.3%)",
          "details": "Used: 98.34GB of 106.48GB",
          "suggestion": "Clean up disk space on /..."
        }
      ]
    }
  ],
  "data_points": 60
}
```

## Optimization Script (optimize.sh)

The included optimization script performs:
- Kernel parameter tuning
- Swappiness adjustment
- File handle limit increase
- Disk scheduler optimization
- Filesystem buffer flushing
- Cache management

```bash
#!/bin/bash
# System optimization script

# Adjust swappiness
sysctl vm.swappiness=10

# Increase file handles
sysctl fs.file-max=2097152
ulimit -n 65536

# Disk scheduler tuning
echo deadline > /sys/block/sda/queue/scheduler

# Clear caches
sync
echo 3 > /proc/sys/vm/drop_caches
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Roadmap

- [ ] Add container (Docker) monitoring support
- [ ] Implement alerting system (email/SMS notifications)
- [ ] Develop web-based dashboard
- [ ] Add machine learning for predictive analysis
- [ ] Create Windows compatibility layer

## Support

For issues and feature requests, please [open an issue](https://github.com/yourusername/system-resource-monitor/issues).

---

**System Resource Monitor v1.0** | [Documentation](docs/) | [Changelog](CHANGELOG.md)