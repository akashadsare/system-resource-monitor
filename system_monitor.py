#!/usr/bin/env python3
"""
System Resource Monitor and Optimizer
Monitors CPU, memory, disk, and network usage
Identifies bottlenecks and suggests optimizations
"""

import psutil
import time
import logging
import argparse
import json
import threading
import os
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    filename='system_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ResourceMonitor:
    def __init__(self, interval=5):
        self.interval = interval
        self.running = False
        self.thread = None
        self.data_buffer = []
        self.thresholds = {
            'cpu': 80,
            'memory': 75,
            'disk': 85,
            'swap': 50
        }

    def get_cpu_stats(self):
        """Get CPU usage with per-core breakdown"""
        return {
            'total': psutil.cpu_percent(interval=0.1),
            'per_core': psutil.cpu_percent(interval=0.1, percpu=True),
            'frequency': psutil.cpu_freq().current,
            'load_avg': os.getloadavg()
        }

    def get_memory_stats(self):
        """Get RAM and swap memory usage"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            'ram': {
                'total': mem.total,
                'available': mem.available,
                'used': mem.used,
                'percent': mem.percent
            },
            'swap': {
                'total': swap.total,
                'used': swap.used,
                'percent': swap.percent
            }
        }

    def get_disk_stats(self):
        """Get disk I/O and usage statistics"""
        partitions = []
        for partition in psutil.disk_partitions():
            usage = psutil.disk_usage(partition.mountpoint)
            partitions.append({
                'device': partition.device,
                'mount': partition.mountpoint,
                'total': usage.total,
                'used': usage.used,
                'percent': usage.percent
            })
        
        io = psutil.disk_io_counters()
        return {
            'partitions': partitions,
            'io': {
                'read_bytes': io.read_bytes,
                'write_bytes': io.write_bytes,
                'read_time': io.read_time,
                'write_time': io.write_time
            }
        }

    def get_network_stats(self):
        """Get network I/O statistics"""
        net = psutil.net_io_counters()
        return {
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv
        }

    def collect_data(self):
        """Collect all system metrics"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': self.get_cpu_stats(),
            'memory': self.get_memory_stats(),
            'disk': self.get_disk_stats(),
            'network': self.get_network_stats()
        }

    def analyze_bottlenecks(self, data):
        """Identify system bottlenecks based on collected data"""
        issues = []
        
        # CPU analysis
        if data['cpu']['total'] > self.thresholds['cpu']:
            core_loads = [f"{load:.1f}%" for load in data['cpu']['per_core']]
            issues.append({
                'type': 'CPU',
                'severity': 'High',
                'message': f"High CPU usage: {data['cpu']['total']:.1f}%",
                'details': f"Core loads: {', '.join(core_loads)}",
                'suggestion': "Check CPU-intensive processes with 'top' command\nConsider process optimization or load balancing"
            })
        
        # Memory analysis
        if data['memory']['ram']['percent'] > self.thresholds['memory']:
            issues.append({
                'type': 'Memory',
                'severity': 'High',
                'message': f"High RAM usage: {data['memory']['ram']['percent']:.1f}%",
                'details': f"Available: {data['memory']['ram']['available'] / (1024**3):.2f} GB",
                'suggestion': "Identify memory-hogging processes with 'ps aux --sort=-%mem'\nConsider adding more RAM or optimizing applications"
            })
        
        # Disk analysis
        for partition in data['disk']['partitions']:
            if partition['percent'] > self.thresholds['disk']:
                issues.append({
                    'type': 'Disk',
                    'severity': 'Critical' if partition['percent'] > 90 else 'High',
                    'message': f"Disk space low: {partition['mount']} ({partition['percent']:.1f}%)",
                    'details': f"Used: {partition['used'] / (1024**3):.2f}GB of {partition['total'] / (1024**3):.2f}GB",
                    'suggestion': f"Clean up disk space on {partition['mount']}\nUse 'du -sh {partition['mount']}/* | sort -rh' to find large files"
                })
        
        # Swap analysis
        if data['memory']['swap']['percent'] > self.thresholds['swap']:
            issues.append({
                'type': 'Swap',
                'severity': 'High',
                'message': f"High swap usage: {data['memory']['swap']['percent']:.1f}%",
                'details': f"Swap used: {data['memory']['swap']['used'] / (1024**3):.2f}GB",
                'suggestion': "Reduce memory pressure or increase swap space\nCheck for memory leaks in applications"
            })
        
        return issues

    def monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                data = self.collect_data()
                self.data_buffer.append(data)
                
                # Analyze and report issues
                issues = self.analyze_bottlenecks(data)
                if issues:
                    logging.warning(f"Detected {len(issues)} potential bottlenecks")
                    for issue in issues:
                        logging.warning(f"{issue['type']} issue: {issue['message']}")
                
                time.sleep(self.interval)
            except Exception as e:
                logging.error(f"Monitoring error: {str(e)}")

    def start(self):
        """Start monitoring in a background thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.monitor_loop)
            self.thread.daemon = True
            self.thread.start()
            logging.info("Monitoring started")

    def stop(self):
        """Stop monitoring"""
        if self.running:
            self.running = False
            if self.thread is not None:
                self.thread.join(timeout=1.0)
            logging.info("Monitoring stopped")

    def generate_report(self, filename):
        """Generate JSON report with analysis"""
        report = {
            'metadata': {
                'system': os.uname().sysname,
                'hostname': os.uname().nodename,
                'duration': f"{len(self.data_buffer) * self.interval} seconds"
            },
            'analysis': [],
            'data_points': len(self.data_buffer)
        }
        
        # Analyze all collected data points
        for data in self.data_buffer:
            report['analysis'].append({
                'timestamp': data['timestamp'],
                'issues': self.analyze_bottlenecks(data)
            })
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        return filename

def optimize_system():
    """Execute system optimization commands"""
    print("Executing system optimizations...")
    os.system('sync')  # Flush filesystem buffers
    os.system('echo 3 > /proc/sys/vm/drop_caches')  # Clear page cache
    print("Optimizations completed")

def git_commit_report(report_file):
    """Commit report to Git repository"""
    if not os.path.exists('.git'):
        os.system('git init')
    
    os.system(f'git add {report_file}')
    commit_message = f"System report {datetime.now().strftime('%Y%m%d-%H%M%S')}"
    os.system(f'git commit -m "{commit_message}"')
    print(f"Report committed to Git: {commit_message}")

def main():
    parser = argparse.ArgumentParser(description='System Resource Monitor')
    parser.add_argument('--interval', type=int, default=5, help='Monitoring interval in seconds')
    parser.add_argument('--duration', type=int, default=300, help='Total monitoring duration in seconds')
    parser.add_argument('--optimize', action='store_true', help='Run system optimizations')
    parser.add_argument('--report', help='Generate report filename')
    args = parser.parse_args()

    monitor = ResourceMonitor(interval=args.interval)
    
    try:
        if args.optimize:
            optimize_system()
        
        print("Starting system monitoring...")
        monitor.start()
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print("\nMonitoring interrupted")
    finally:
        monitor.stop()
        
        if args.report:
            report_file = monitor.generate_report(args.report)
            print(f"Generated report: {report_file}")
            git_commit_report(report_file)

if __name__ == "__main__":
    main()