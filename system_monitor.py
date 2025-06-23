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
from pathlib import Path
import socket
import platform

# Setup logging with both file and console handlers
def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"system_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return log_file

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
            'swap': 50,
            'network': 90  # Network utilization threshold
        }
        self.baseline = None
        self.alert_callbacks = []

    def set_thresholds(self, **kwargs):
        """Update monitoring thresholds"""
        for key, value in kwargs.items():
            if key in self.thresholds:
                self.thresholds[key] = value
                logging.info(f"Updated {key} threshold to {value}")

    def add_alert_callback(self, callback):
        """Add callback function for alerts"""
        self.alert_callbacks.append(callback)

    def trigger_alerts(self, issues):
        """Trigger registered alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                callback(issues)
            except Exception as e:
                logging.error(f"Alert callback error: {str(e)}")

    def get_cpu_stats(self):
        """Get CPU usage with per-core breakdown and temperature if available"""
        stats = {
            'total': psutil.cpu_percent(interval=0.1),
            'per_core': psutil.cpu_percent(interval=0.1, percpu=True),
            'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else None,
            'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None,
            'ctx_switches': psutil.cpu_stats().ctx_switches,
            'interrupts': psutil.cpu_stats().interrupts,
            'soft_interrupts': psutil.cpu_stats().soft_interrupts,
            'syscalls': psutil.cpu_stats().syscalls
        }
        
        # Try to get CPU temperature on supported systems
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                cpu_temps = []
                for name, entries in temps.items():
                    if 'cpu' in name.lower():
                        cpu_temps.extend(entry.current for entry in entries)
                if cpu_temps:
                    stats['temperature'] = sum(cpu_temps) / len(cpu_temps)
        except Exception:
            pass
            
        return stats

    def get_memory_stats(self):
        """Get RAM and swap memory usage with detailed breakdown"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            'ram': {
                'total': mem.total,
                'available': mem.available,
                'used': mem.used,
                'free': mem.free,
                'percent': mem.percent,
                'cached': mem.cached if hasattr(mem, 'cached') else None,
                'buffers': mem.buffers if hasattr(mem, 'buffers') else None
            },
            'swap': {
                'total': swap.total,
                'used': swap.used,
                'free': swap.free,
                'percent': swap.percent,
                'sin': swap.sin if hasattr(swap, 'sin') else None,
                'sout': swap.sout if hasattr(swap, 'sout') else None
            }
        }

    def get_disk_stats(self):
        """Get disk I/O and usage statistics with SMART data if available"""
        partitions = []
        for partition in psutil.disk_partitions(all=True):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    'device': partition.device,
                    'mount': partition.mountpoint,
                    'fstype': partition.fstype,
                    'opts': partition.opts,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                })
            except (PermissionError, OSError) as e:
                logging.warning(f"Could not get usage for {partition.mountpoint}: {str(e)}")
        
        try:
            io = psutil.disk_io_counters(perdisk=True)
            io_stats = {
                disk: {
                    'read_bytes': stats.read_bytes,
                    'write_bytes': stats.write_bytes,
                    'read_time': stats.read_time,
                    'write_time': stats.write_time,
                    'read_count': stats.read_count,
                    'write_count': stats.write_count
                } for disk, stats in io.items()
            }
        except Exception as e:
            logging.error(f"Could not get disk I/O stats: {str(e)}")
            io_stats = {}
        
        return {
            'partitions': partitions,
            'io': io_stats
        }

    def get_network_stats(self):
        """Get detailed network I/O statistics and connections"""
        net_io = psutil.net_io_counters(pernic=True)
        net_if = psutil.net_if_stats()
        
        # Get network interface statistics
        interfaces = {}
        for nic, stats in net_io.items():
            if_stats = net_if.get(nic)
            interfaces[nic] = {
                'bytes_sent': stats.bytes_sent,
                'bytes_recv': stats.bytes_recv,
                'packets_sent': stats.packets_sent,
                'packets_recv': stats.packets_recv,
                'errin': stats.errin if hasattr(stats, 'errin') else None,
                'errout': stats.errout if hasattr(stats, 'errout') else None,
                'dropin': stats.dropin if hasattr(stats, 'dropin') else None,
                'dropout': stats.dropout if hasattr(stats, 'dropout') else None,
                'speed': if_stats.speed if if_stats and hasattr(if_stats, 'speed') else None,
                'mtu': if_stats.mtu if if_stats else None,
                'is_up': if_stats.isup if if_stats else None
            }
        
        # Get active connections
        try:
            connections = []
            for conn in psutil.net_connections(kind='inet'):
                connections.append({
                    'fd': conn.fd,
                    'family': conn.family,
                    'type': conn.type,
                    'laddr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                    'raddr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                    'status': conn.status,
                    'pid': conn.pid
                })
        except (psutil.AccessDenied, PermissionError):
            connections = []
            logging.warning("Could not get network connections (requires elevated privileges)")
        
        return {
            'interfaces': interfaces,
            'connections': connections,
            'hostname': socket.gethostname(),
            'fqdn': socket.getfqdn()
        }

    def collect_data(self):
        """Collect all system metrics"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'platform': platform.platform(),
                    'python_version': platform.python_version(),
                    'processor': platform.processor(),
                    'machine': platform.machine()
                },
                'cpu': self.get_cpu_stats(),
                'memory': self.get_memory_stats(),
                'disk': self.get_disk_stats(),
                'network': self.get_network_stats()
            }
            
            # Calculate rates if we have previous data
            if self.data_buffer:
                last_data = self.data_buffer[-1]
                interval = (datetime.fromisoformat(data['timestamp']) - 
                          datetime.fromisoformat(last_data['timestamp'])).total_seconds()
                
                if interval > 0:
                    # Calculate network rates
                    for nic in data['network']['interfaces']:
                        if nic in last_data['network']['interfaces']:
                            current = data['network']['interfaces'][nic]
                            previous = last_data['network']['interfaces'][nic]
                            current['bytes_sent_rate'] = (current['bytes_sent'] - previous['bytes_sent']) / interval
                            current['bytes_recv_rate'] = (current['bytes_recv'] - previous['bytes_recv']) / interval
            
            return data
        except Exception as e:
            logging.error(f"Error collecting data: {str(e)}")
            raise

    def analyze_bottlenecks(self, data):
        """Identify system bottlenecks based on collected data"""
        issues = []
        
        # CPU analysis
        if data['cpu']['total'] > self.thresholds['cpu']:
            core_loads = [f"{load:.1f}%" for load in data['cpu']['per_core']]
            severity = 'Critical' if data['cpu']['total'] > 95 else 'High'
            issues.append({
                'type': 'CPU',
                'severity': severity,
                'message': f"High CPU usage: {data['cpu']['total']:.1f}%",
                'details': f"Core loads: {', '.join(core_loads)}",
                'suggestion': (
                    "1. Check CPU-intensive processes with 'top' command\n"
                    "2. Consider process optimization or load balancing\n"
                    "3. Monitor system temperature and throttling"
                )
            })
        
        # Memory analysis
        mem = data['memory']['ram']
        if mem['percent'] > self.thresholds['memory']:
            severity = 'Critical' if mem['percent'] > 90 else 'High'
            issues.append({
                'type': 'Memory',
                'severity': severity,
                'message': f"High RAM usage: {mem['percent']:.1f}%",
                'details': (
                    f"Available: {mem['available'] / (1024**3):.2f} GB\n"
                    f"Used: {mem['used'] / (1024**3):.2f} GB\n"
                    f"Cached: {mem.get('cached', 0) / (1024**3):.2f} GB"
                ),
                'suggestion': (
                    "1. Identify memory-hogging processes with 'ps aux --sort=-%mem'\n"
                    "2. Check for memory leaks\n"
                    "3. Consider increasing RAM or enabling swap"
                )
            })
        
        # Disk analysis
        for partition in data['disk']['partitions']:
            if partition['percent'] > self.thresholds['disk']:
                severity = 'Critical' if partition['percent'] > 95 else 'High'
                issues.append({
                    'type': 'Disk',
                    'severity': severity,
                    'message': f"Disk space low: {partition['mount']} ({partition['percent']:.1f}%)",
                    'details': (
                        f"Used: {partition['used'] / (1024**3):.2f}GB of "
                        f"{partition['total'] / (1024**3):.2f}GB\n"
                        f"Filesystem: {partition['fstype']}"
                    ),
                    'suggestion': (
                        f"1. Clean up disk space on {partition['mount']}\n"
                        f"2. Use 'du -sh {partition['mount']}/* | sort -rh' to find large files\n"
                        "3. Consider adding storage or enabling compression"
                    )
                })
        
        # Network analysis
        for nic, stats in data['network']['interfaces'].items():
            if 'bytes_sent_rate' in stats and stats.get('speed'):
                # Convert speed from Mbps to Bytes/s for comparison
                max_bytes_per_sec = stats['speed'] * 1024 * 1024 / 8
                current_rate = max(stats['bytes_sent_rate'], stats['bytes_recv_rate'])
                utilization = (current_rate / max_bytes_per_sec) * 100
                
                if utilization > self.thresholds['network']:
                    severity = 'Critical' if utilization > 95 else 'High'
                    issues.append({
                        'type': 'Network',
                        'severity': severity,
                        'message': f"High network utilization on {nic}: {utilization:.1f}%",
                        'details': (
                            f"Send rate: {stats['bytes_sent_rate'] / 1024 / 1024:.2f} MB/s\n"
                            f"Receive rate: {stats['bytes_recv_rate'] / 1024 / 1024:.2f} MB/s"
                        ),
                        'suggestion': (
                            "1. Identify bandwidth-heavy processes with 'nethogs'\n"
                            "2. Check for network bottlenecks\n"
                            "3. Consider traffic shaping or upgrading network capacity"
                        )
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
                        logging.warning(f"{issue['type']} issue ({issue['severity']}): {issue['message']}")
                    self.trigger_alerts(issues)
                
                # Maintain buffer size (keep last hour of data at 5-second intervals)
                max_buffer_size = 720  # 3600 seconds / 5 seconds
                if len(self.data_buffer) > max_buffer_size:
                    self.data_buffer = self.data_buffer[-max_buffer_size:]
                
                time.sleep(self.interval)
            except Exception as e:
                logging.error(f"Monitoring error: {str(e)}")
                if not self.running:  # Only sleep on error if still running
                    break
                time.sleep(1)  # Sleep briefly before retrying

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
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'hostname': socket.gethostname(),
                'duration': f"{len(self.data_buffer) * self.interval} seconds",
                'start_time': self.data_buffer[0]['timestamp'] if self.data_buffer else None,
                'end_time': self.data_buffer[-1]['timestamp'] if self.data_buffer else None
            },
            'analysis': [],
            'data_points': len(self.data_buffer),
            'thresholds': self.thresholds
        }
        
        # Analyze all collected data points
        for data in self.data_buffer:
            report['analysis'].append({
                'timestamp': data['timestamp'],
                'issues': self.analyze_bottlenecks(data)
            })
        
        # Create reports directory if it doesn't exist
        report_dir = Path("reports")
        report_dir.mkdir(exist_ok=True)
        
        # Save report
        report_path = report_dir / filename
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logging.info(f"Report generated: {report_path}")
        return str(report_path)

def email_alert(issues):
    """Example alert callback for email notifications"""
    # This is a placeholder - implement actual email sending logic
    logging.info(f"Would send email alert for {len(issues)} issues")

def optimize_system():
    """Execute system optimization commands"""
    logging.info("Starting system optimizations...")
    
    optimizations = []
    
    # Filesystem optimizations
    try:
        os.system('sync')
        optimizations.append("Flushed filesystem buffers")
    except Exception as e:
        logging.error(f"Failed to sync filesystems: {str(e)}")
    
    # Clear page cache (requires root)
    try:
        if os.geteuid() == 0:  # Check if running as root
            os.system('echo 3 > /proc/sys/vm/drop_caches')
            optimizations.append("Cleared page cache")
        else:
            logging.warning("Skipping page cache clear (requires root)")
    except Exception as e:
        logging.error(f"Failed to clear page cache: {str(e)}")
    
    # Report results
    if optimizations:
        logging.info("Completed optimizations:\n" + "\n".join(f"- {opt}" for opt in optimizations))
    else:
        logging.warning("No optimizations were performed")

def git_commit_report(report_file):
    """Commit report to Git repository"""
    try:
        if not os.path.exists('.git'):
            os.system('git init')
            logging.info("Initialized new Git repository")
        
        os.system(f'git add {report_file}')
        commit_message = f"System report {datetime.now().strftime('%Y%m%d-%H%M%S')}"
        result = os.system(f'git commit -m "{commit_message}"')
        
        if result == 0:
            logging.info(f"Report committed to Git: {commit_message}")
        else:
            logging.error("Failed to commit report to Git")
    except Exception as e:
        logging.error(f"Git operation failed: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='System Resource Monitor')
    parser.add_argument('--interval', type=int, default=5,
                      help='Monitoring interval in seconds')
    parser.add_argument('--duration', type=int, default=300,
                      help='Total monitoring duration in seconds')
    parser.add_argument('--optimize', action='store_true',
                      help='Run system optimizations')
    parser.add_argument('--report', type=str,
                      default=f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                      help='Generate report filename')
    parser.add_argument('--email-alerts', action='store_true',
                      help='Enable email alerts')
    parser.add_argument('--thresholds', type=str,
                      help='JSON string with threshold values (e.g., \'{"cpu":85,"memory":80}\')')
    args = parser.parse_args()

    # Setup logging
    log_file = setup_logging()
    logging.info(f"Logging to: {log_file}")
    
    # Initialize monitor
    monitor = ResourceMonitor(interval=args.interval)
    
    # Set custom thresholds if provided
    if args.thresholds:
        try:
            thresholds = json.loads(args.thresholds)
            monitor.set_thresholds(**thresholds)
        except json.JSONDecodeError:
            logging.error("Invalid threshold JSON format")
            sys.exit(1)
    
    # Setup email alerts if requested
    if args.email_alerts:
        monitor.add_alert_callback(email_alert)
    
    try:
        # Run optimizations if requested
        if args.optimize:
            optimize_system()
        
        # Start monitoring
        logging.info(f"Starting system monitoring (duration: {args.duration}s, interval: {args.interval}s)")
        monitor.start()
        
        try:
            time.sleep(args.duration)
        except KeyboardInterrupt:
            logging.info("\nMonitoring interrupted by user")
        
        # Stop monitoring and generate report
        monitor.stop()
        if monitor.data_buffer:
            report_file = monitor.generate_report(args.report)
            git_commit_report(report_file)
        else:
            logging.warning("No data collected, skipping report generation")
        
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        sys.exit(1)
    finally:
        logging.info("Monitoring finished")

if __name__ == '__main__':
    main()