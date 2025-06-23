# 🚀 System Resource Monitor & Optimizer

<!--
![Dashboard Banner](https://via.placeholder.com/1000x250?text=System+Resource+Monitor+%26+Optimizer)
-->

<p align="center">
  <b>Track, analyze, and optimize your system resources in real time.</b><br>
  <a href="#features">Features</a> • <a href="#quickstart">Quickstart</a> • <a href="#usage">Usage</a> • <a href="#docker">Docker</a> • <a href="#optimization">Optimization</a> • <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
  <img src="https://img.shields.io/badge/Platform-Linux-important" />
  <img src="https://img.shields.io/badge/Docker-Ready-blue" />
</p>

---

> **Note:** The dashboard image above was a placeholder. A web dashboard is a planned feature (see Roadmap), but is not yet implemented in this repository.

## ✨ Features

- 📊 **Live Monitoring**: CPU, memory, disk, network, per-interface stats
- 🌡️ **Temperature Sensors**: (where supported)
- ⚡ **Bottleneck Detection**: Severity classification & actionable suggestions
- 📝 **Configurable Thresholds**: CLI or JSON
- 📈 **Historical JSON Reports**: With thresholds, time range, and analysis
- 🔄 **Git Integration**: Auto-commit reports
- 🧵 **Multi-threaded**: Fast, concurrent monitoring
- ⚙️ **System Optimization**: Kernel, disk, network, and persistent tuning
- 📨 **Email Alert Callback**: (ready for integration)
- 🗂️ **Organized Logging**: File & console

---

## 📦 Quickstart

```bash
# 1. Clone & enter the repo
$ git clone https://github.com/akashadsare/system-resource-monitor.git
$ cd system-resource-monitor

# 2. Install dependencies
$ pip install -r requirements.txt

# 3. Start monitoring (5 min default)
$ ./system_monitor.py
```

---

## 🐳 Docker

> **Note:** Optimization requires `--privileged` and a compatible Linux host. Some features (e.g., `sysctl`, disk tuning) may not work in minimal images or non-Linux environments.

```bash
# Build image
$ docker build -t system-resource-monitor .

# Run monitor (5 min)
$ docker run --rm system-resource-monitor python system_monitor.py --duration 300

# Run with optimization & report
$ docker run --rm -v $(pwd):/app system-resource-monitor python system_monitor.py --optimize --report system_report.json

# Run optimization script only
$ docker run --rm --privileged system-resource-monitor ./optimize.sh
```

---

## ⚡ Usage

### Basic Monitoring
```bash
./system_monitor.py --duration 300
```

### Custom Config
```bash
./system_monitor.py --interval 2 --duration 120 --thresholds '{"cpu":85,"memory":80,"disk":90}'
```

### Enable Email Alerts (placeholder)
```bash
./system_monitor.py --email-alerts
```

### Generate Report & Auto-commit
```bash
./system_monitor.py --optimize --report system_report.json
```

### Logs & Reports
- Logs: `logs/`
- Reports: `reports/`

---

## 🛠️ Optimization Script

The included `optimize.sh` script performs:
- Kernel parameter tuning (swappiness, cache, dirty ratios)
- File handle & network tuning
- Disk scheduler optimization (all detected disks)
- Filesystem buffer flushing & cache management
- Persistent changes via `/etc/sysctl.d/99-performance.conf`
- **Root privilege check**

```bash
sudo ./optimize.sh
```

---

## 🧩 Configuration

Edit thresholds in `system_monitor.py` or pass via CLI:
```python
self.thresholds = {
    'cpu': 80, 'memory': 75, 'disk': 85, 'swap': 50, 'network': 90
}
```

---

## 📊 Sample Report

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
          "suggestion": "Check CPU-intensive processes with 'top'..."
        }
      ]
    }
  ],
  "data_points": 60
}
```

---

## 🤝 Contributing

1. Fork & branch: `git checkout -b feature/your-feature`
2. Commit: `git commit -am 'Add feature'`
3. Push: `git push origin feature/your-feature`
4. Open a Pull Request

---

## 📜 License

MIT — see [LICENSE](LICENSE)

---

## 🚦 Roadmap

- [ ] Docker container monitoring
- [ ] Alerting system (email/SMS)
- [ ] Web dashboard
- [ ] Predictive analysis (ML)
- [ ] Windows compatibility

---

## 💬 Support

For issues & feature requests, [open an issue](https://github.com/akashadsare/system-resource-monitor/issues).

---

<p align="center">
  <b>System Resource Monitor v1.0</b> | <a href="docs/">Documentation</a> | <a href="CHANGELOG.md">Changelog</a><br>
  <sub>Author: Akash Adsare</sub>
</p>