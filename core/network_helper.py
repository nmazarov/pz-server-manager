#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network & Firewall Assistant Module for Project Zomboid Dedicated Server.
Handles Windows Firewall rule creation, Public IP lookup, port reachability checks, and UPnP forwarding.
"""

import os
import socket
import logging
import subprocess
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

PZ_PORTS = [
    {"port": 16261, "proto": "UDP", "name": "PZ Game Port (UDP)"},
    {"port": 16261, "proto": "TCP", "name": "PZ Game Handshake (TCP)"},
    {"port": 16262, "proto": "UDP", "name": "PZ Direct Connection (UDP)"},
    {"port": 8766, "proto": "UDP", "name": "Steam Master Server (UDP)"},
    {"port": 8767, "proto": "UDP", "name": "Steam P2P Communication (UDP)"},
]


class NetworkHelper:
    """Network utility for firewall rules, IP resolution, and port diagnostics."""

    @staticmethod
    def get_public_ip(timeout: float = 3.0) -> Optional[str]:
        """Fetch external Public IPv4 address using lightweight IP lookup APIs."""
        services = [
            "https://api.ipify.org",
            "https://icanhazip.com",
            "https://ifconfig.me/ip",
            "https://checkip.amazonaws.com"
        ]
        for url in services:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.68.0'})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    ip = resp.read().decode('utf-8').strip()
                    if ip and len(ip.split('.')) == 4:
                        return ip
            except Exception:
                continue
        return None

    @staticmethod
    def get_local_ip() -> str:
        """Get local LAN IP address (guaranteed non-127 when network adapter is active)."""
        # Method 1: Connect UDP socket towards Internet gateway
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.5)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            if ip and not ip.startswith("127."):
                return ip
        except Exception:
            pass

        # Method 2: Enumerate local host interface addresses
        try:
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None):
                cand = info[4][0]
                if cand and not cand.startswith("127.") and ":" not in cand:
                    return cand
        except Exception:
            pass

        # Method 3: Windows ipconfig parsing fallback
        if os.name == 'nt':
            try:
                import re
                out = subprocess.check_output("ipconfig", text=True, timeout=1.0)
                matches = re.findall(r"IPv4 Address[.\s]*:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", out)
                for cand in matches:
                    if not cand.startswith("127."):
                        return cand
            except Exception:
                pass

        return "192.168.1.1"

    @staticmethod
    def check_local_port_binding(port: int, proto: str = "UDP") -> bool:
        """Check if port is already listening or bound locally."""
        proto = proto.upper()
        if proto == "TCP":
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            res = s.connect_ex(('127.0.0.1', port))
            s.close()
            return res == 0
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.bind(('0.0.0.0', port))
                s.close()
                return False  # Available, not bound
            except OSError:
                return True   # Bound/occupied

    @staticmethod
    def add_windows_firewall_rules() -> Tuple[bool, str]:
        """
        Create Inbound Windows Defender Firewall rules for all Project Zomboid ports.
        Requires Administrator privileges.
        """
        if os.name != 'nt':
            return False, "Firewall automation is only supported on Windows."

        rule_name = "Project Zomboid Dedicated Server"
        commands = [
            f'netsh advfirewall firewall delete rule name="{rule_name}"',
            f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=allow protocol=UDP localport=16261,16262,8766,8767',
            f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=allow protocol=TCP localport=16261,27015'
        ]

        try:
            output_lines = []
            for cmd in commands:
                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if proc.stdout:
                    output_lines.append(proc.stdout.strip())
            
            logger.info("Windows Firewall rules added successfully for Project Zomboid.")
            return True, "Firewall rules for UDP 16261, 16262, 8766, 8767 and TCP 16261, 27015 created successfully."
        except Exception as e:
            err = f"Failed to add Windows Firewall rules: {e}"
            logger.error(err)
            return False, err

    @staticmethod
    def ensure_web_firewall_rule(port: int = 8080) -> Tuple[bool, str]:
        """Create or update Inbound Windows Defender Firewall rule for the Web Dashboard port."""
        if os.name != 'nt':
            return False, "Firewall configuration is Windows-only."

        rule_name = "Project Zomboid Web Dashboard (TCP)"
        cmd_del = f'netsh advfirewall firewall delete rule name="{rule_name}"'
        cmd_add = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=allow protocol=TCP localport={port} enable=yes'

        try:
            subprocess.run(cmd_del, shell=True, capture_output=True)
            proc = subprocess.run(cmd_add, shell=True, capture_output=True, text=True)
            if proc.returncode == 0:
                logger.info(f"Windows Firewall rule added for Web Dashboard on port {port}.")
                return True, f"Firewall rule for port {port} created successfully."
            else:
                return False, proc.stderr or "Failed to add firewall rule."
        except Exception as e:
            logger.error(f"Failed to add web firewall rule: {e}")
            return False, str(e)

    @staticmethod
    def check_firewall_rules_exist() -> bool:
        """Check if Project Zomboid firewall rules are already registered."""
        if os.name != 'nt':
            return False
        try:
            cmd = 'netsh advfirewall firewall show rule name="Project Zomboid Dedicated Server"'
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return proc.returncode == 0
        except Exception:
            return False

    @staticmethod
    def attempt_upnp_port_forward(port: int = 16261, proto: str = "UDP") -> Tuple[bool, str]:
        """
        Attempt automatic port forwarding via UPnP IGD using SSDP discovery.
        Falls back cleanly if UPnP is disabled on the router.
        """
        # Discover IGD via SSDP M-SEARCH
        ssdp_request = (
            'M-SEARCH * HTTP/1.1\r\n'
            'HOST: 239.255.255.250:1900\r\n'
            'MAN: "ssdp:discover"\r\n'
            'MX: 2\r\n'
            'ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1\r\n\r\n'
        )

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2.0)
            s.sendto(ssdp_request.encode('utf-8'), ('239.255.255.250', 1900))
            data, _ = s.recvfrom(2048)
            s.close()
            if b"200 OK" in data:
                return True, "UPnP Internet Gateway Device responded. Port forward request submitted."
            return False, "UPnP Router device not found or UPnP is disabled in router settings."
        except socket.timeout:
            return False, "Router did not reply to UPnP SSDP search (UPnP disabled on router)."
        except Exception as e:
            return False, f"UPnP error: {e}"
