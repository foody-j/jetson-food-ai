"""
System Information Collector
Gathers comprehensive system information for MQTT metadata
"""

import socket
import platform
import psutil
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SystemInfo:
    """Collects and caches system information"""

    def __init__(self, device_name: Optional[str] = None, location: Optional[str] = None):
        """
        Initialize system info collector

        Args:
            device_name: Custom device name (default: hostname)
            location: Physical location of device (e.g., "Kitchen", "Factory Floor")
        """
        self._device_name = device_name
        self._location = location
        self._static_info = self._collect_static_info()

    def _collect_static_info(self) -> Dict[str, Any]:
        """Collect static system information (doesn't change during runtime)"""
        hostname = socket.gethostname()

        # Get all IP addresses
        ip_addresses = []
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # IPv4
                        if not addr.address.startswith('127.'):
                            ip_addresses.append({
                                "interface": interface,
                                "address": addr.address
                            })
        except Exception as e:
            logger.warning(f"Could not get network interfaces: {e}")
            ip_addresses = [{"interface": "unknown", "address": "unknown"}]

        # Get MAC address of first non-loopback interface
        mac_address = "unknown"
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                if interface != 'lo':
                    for addr in addrs:
                        if addr.family == psutil.AF_LINK:
                            mac_address = addr.address
                            break
                    if mac_address != "unknown":
                        break
        except Exception as e:
            logger.warning(f"Could not get MAC address: {e}")

        return {
            "hostname": hostname,
            "device_name": self._device_name or hostname,
            "location": self._location or "unknown",
            "ip_addresses": ip_addresses,
            "mac_address": mac_address,
            "platform": platform.system(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
        }

    def get_static_info(self) -> Dict[str, Any]:
        """Get static system information"""
        return self._static_info.copy()

    def get_dynamic_info(self) -> Dict[str, Any]:
        """Get dynamic system information (changes during runtime)"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_info = {
                "total_mb": round(memory.total / (1024 * 1024), 2),
                "used_mb": round(memory.used / (1024 * 1024), 2),
                "percent": memory.percent
            }

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_info = {
                "total_gb": round(disk.total / (1024 ** 3), 2),
                "used_gb": round(disk.used / (1024 ** 3), 2),
                "percent": disk.percent
            }

            # System uptime
            boot_time = psutil.boot_time()
            uptime_seconds = int(psutil.time.time() - boot_time)

            # GPU info (for Jetson)
            gpu_info = self._get_gpu_info()

            return {
                "cpu_percent": cpu_percent,
                "memory": memory_info,
                "disk": disk_info,
                "uptime_seconds": uptime_seconds,
                "gpu": gpu_info
            }

        except Exception as e:
            logger.error(f"Error collecting dynamic info: {e}")
            return {}

    def _get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information (Jetson-specific)"""
        gpu_info = {}

        try:
            # Try to read Jetson GPU stats
            # Temperature
            temp_files = [
                '/sys/devices/virtual/thermal/thermal_zone0/temp',
                '/sys/devices/virtual/thermal/thermal_zone1/temp',
            ]

            temps = []
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    with open(temp_file, 'r') as f:
                        temp = float(f.read().strip()) / 1000.0  # Convert to Celsius
                        temps.append(round(temp, 1))

            if temps:
                gpu_info['temperature_c'] = max(temps)

            # GPU usage (if available via tegrastats or other means)
            # This is platform-specific and might need adjustment
            if os.path.exists('/sys/devices/gpu.0/load'):
                with open('/sys/devices/gpu.0/load', 'r') as f:
                    load = int(f.read().strip())
                    gpu_info['load_percent'] = load

        except Exception as e:
            logger.debug(f"Could not read GPU info: {e}")

        return gpu_info if gpu_info else {"status": "unavailable"}

    def get_full_info(self) -> Dict[str, Any]:
        """Get complete system information (static + dynamic)"""
        info = self.get_static_info()
        info.update(self.get_dynamic_info())
        return info

    def to_dict(self) -> Dict[str, Any]:
        """Get static info as dictionary (for MQTT metadata)"""
        return self.get_static_info()
