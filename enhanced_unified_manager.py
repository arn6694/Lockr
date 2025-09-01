#!/usr/bin/env python3
"""
Lockr - Enterprise Server & Password Management
Combines password creation, Ansible Vault storage, retrieval, and server management
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import subprocess
import os
import json
import secrets
import string
from datetime import datetime, timedelta
import tempfile
import shutil
import paramiko
import socket
import threading
import time

app = Flask(__name__, static_folder='static')
app.secret_key = secrets.token_hex(32)

# Configure session to be more persistent
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # 24 hour session
app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP for local development
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Import configuration
try:
    from config import *
except ImportError:
    # Fallback configuration if config.py is not available
    VAULT_DIR = "/home/brian/playbooks/vault"
    VAULT_KEY = "/home/brian/playbooks/.vault_key"
    ANSIBLE_VAULT_CMD = "/usr/bin/ansible-vault"  # Use full path
    SSH_KEY_PATH = "/home/brian/.ssh/id_ed25519"
    SSH_USER = "brian"

# Ensure required directories exist
os.makedirs(VAULT_DIR, exist_ok=True)

# Server storage (in production, use a database)
SERVERS_FILE = "/home/brian/playbooks/servers.json"

# Mock data for demonstration (replace with actual data in production)
MOCK_SERVERS = [
    {"name": "valheim", "ip": "192.168.1.100", "status": "online", "last_access": "2024-08-30 14:30", "ssh_status": "connected"},
    {"name": "archie", "ip": "192.168.1.101", "status": "online", "last_access": "2024-08-30 15:45", "ssh_status": "connected"},
    {"name": "zero", "ip": "192.168.1.102", "status": "offline", "last_access": "2024-08-30 12:15", "ssh_status": "disconnected"}
]

MOCK_USERS = ["root", "admin", "backup", "monitoring"]

def load_servers():
    """Load servers from JSON file"""
    try:
        if os.path.exists(SERVERS_FILE):
            with open(SERVERS_FILE, 'r') as f:
                return json.load(f)
        else:
            return MOCK_SERVERS
    except Exception as e:
        print(f"Error loading servers: {e}")
        return MOCK_SERVERS

def save_servers(servers):
    """Save servers to JSON file"""
    try:
        os.makedirs(os.path.dirname(SERVERS_FILE), exist_ok=True)
        with open(SERVERS_FILE, 'w') as f:
            json.dump(servers, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving servers: {e}")
        return False

def perform_health_check(server_ip, server_name):
    """Perform comprehensive health check on a server with detailed diagnostics"""
    health_results = {
        "server": server_name,
        "ip": server_ip,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overall_status": "unknown",
        "checks": {},
        "troubleshooting": []
    }
    
    try:
        # 1. Basic Connectivity Check
        connectivity_result = test_connectivity_detailed(server_ip, timeout=5)
        health_results["checks"]["connectivity"] = connectivity_result
        
        # 2. SSH Port Check
        ssh_result = test_ssh_port_detailed(server_ip, 22, timeout=5)
        health_results["checks"]["ssh_port"] = ssh_result
        
        # 3. SSH Authentication Check (if we have SSH keys)
        ssh_auth_result = test_ssh_authentication_detailed(server_ip)
        health_results["checks"]["ssh_auth"] = ssh_auth_result
        
        # 4. System Resource Check (if SSH is available)
        if ssh_auth_result["status"] == "authenticated":
            system_resources = check_system_resources_detailed(server_ip)
            health_results["checks"]["system_resources"] = system_resources
        else:
            health_results["checks"]["system_resources"] = {
                "status": "unknown",
                "details": "Cannot check system resources without SSH access",
                "troubleshooting": ["Fix SSH authentication first to enable system resource monitoring"]
            }
        
        # Generate troubleshooting recommendations
        health_results["troubleshooting"] = generate_troubleshooting_recommendations(health_results["checks"])
        
        # Determine overall status - prioritize connectivity over system resources
        connectivity_status = health_results["checks"].get("connectivity", {}).get("status")
        ssh_port_status = health_results["checks"].get("ssh_port", {}).get("status")
        ssh_auth_status = health_results["checks"].get("ssh_auth", {}).get("status")
        system_resources_status = health_results["checks"].get("system_resources", {}).get("status")
        
        # Critical connectivity checks
        if connectivity_status == "offline":
            health_results["overall_status"] = "unhealthy"
        elif ssh_port_status == "closed":
            health_results["overall_status"] = "unhealthy"
        elif ssh_auth_status in ["auth_failed", "no_key"]:
            health_results["overall_status"] = "degraded"
        elif system_resources_status == "issues":
            # System resource issues are less critical - only mark as degraded if other issues exist
            if connectivity_status == "online" and ssh_port_status == "open" and ssh_auth_status == "authenticated":
                health_results["overall_status"] = "degraded"
            else:
                health_results["overall_status"] = "degraded"
        else:
            health_results["overall_status"] = "healthy"
            
        return health_results
        
    except Exception as e:
        health_results["overall_status"] = "error"
        health_results["checks"]["error"] = {
            "status": "error",
            "details": f"Health check failed: {str(e)}",
            "troubleshooting": ["Check if the server IP address is correct", "Verify network connectivity to the server"]
        }
        return health_results

def test_ssh_port(host, port, timeout=5):
    """Test if SSH port is open on a host"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        app.logger.error(f"SSH port test failed for {host}:{port}: {e}")
        return False

def test_ssh_authentication(host):
    """Test SSH key authentication to a host"""
    try:
        if not os.path.exists(SSH_KEY_PATH):
            return False
            
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        private_key = paramiko.Ed25519Key.from_private_key_file(SSH_KEY_PATH)
        ssh.connect(host, username=SSH_USER, pkey=private_key, timeout=10)
        ssh.close()
        return True
    except Exception as e:
        app.logger.error(f"SSH authentication test failed for {host}: {e}")
        return False

def check_system_resources(host):
    """Check system resources on a remote host"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        private_key = paramiko.Ed25519Key.from_private_key_file(SSH_KEY_PATH)
        ssh.connect(host, username=SSH_USER, pkey=private_key, timeout=10)
        
        # Check CPU load
        stdin, stdout, stderr = ssh.exec_command("uptime | awk '{print $10}' | sed 's/,//'", timeout=10)
        cpu_load = stdout.read().decode().strip()
        
        # Check memory usage
        stdin, stdout, stderr = ssh.exec_command("free -m | awk 'NR==2{printf \"%.1f%%\", $3*100/$2}'", timeout=10)
        memory_usage = stdout.read().decode().strip()
        
        # Check disk usage
        stdin, stdout, stderr = ssh.exec_command("df -h / | awk 'NR==2{print $5}'", timeout=10)
        disk_usage = stdout.read().decode().strip()
        
        ssh.close()
        
        # Determine resource health
        try:
            load_float = float(cpu_load)
            mem_float = float(memory_usage.replace('%', ''))
            disk_float = float(disk_usage.replace('%', ''))
            
            if load_float < 2.0 and mem_float < 80 and disk_float < 80:
                status = "healthy"
            elif load_float < 5.0 and mem_float < 90 and disk_float < 90:
                status = "warning"
            else:
                status = "critical"
                
        except ValueError:
            status = "unknown"
        
        return {
            "status": status,
            "details": f"CPU Load: {cpu_load}, Memory: {memory_usage}, Disk: {disk_usage}",
            "cpu_load": cpu_load,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage
        }
        
    except Exception as e:
        app.logger.error(f"System resource check failed for {host}: {e}")
        return {
            "status": "error",
            "details": f"Failed to check system resources: {str(e)}"
        }

def test_connectivity(host, timeout=5):
    """Test basic connectivity to a host"""
    try:
        # Try multiple possible ping locations
        ping_locations = ['/usr/bin/ping', '/bin/ping', 'ping']
        ping_cmd = None
        
        for location in ping_locations:
            if os.path.exists(location) or location == 'ping':
                ping_cmd = location
                break
        
        if not ping_cmd:
            return test_connectivity_socket(host, timeout)
        
        # Use more lenient ping parameters for better compatibility
        result = subprocess.run([ping_cmd, '-c', '1', '-W', '3', host], 
                              capture_output=True, text=True, timeout=timeout+2)
        
        # Debug output for troubleshooting
        print(f"Ping result for {host}: returncode={result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        print(f"Command executed: {ping_cmd} -c 1 -W 3 {host}")
        
        if result.returncode == 0:
            return {"ping": True, "error": None}
        else:
            # Check if it's actually unreachable or just slow
            if "100% packet loss" in result.stdout or "100% packet loss" in result.stderr:
                return {"ping": False, "error": "Host unreachable"}
            elif "timeout" in result.stdout.lower() or "timeout" in result.stderr.lower():
                return {"ping": False, "error": "Ping timeout"}
            else:
                # Try socket test as fallback
                return test_connectivity_socket(host, timeout)
    except subprocess.TimeoutExpired:
        return {"ping": False, "error": "Ping timeout"}
    except FileNotFoundError:
        # Fallback to socket-based connectivity test
        return test_connectivity_socket(host, timeout)
    except Exception as e:
        return {"ping": False, "error": f"Connectivity test error: {str(e)}"}

def test_connectivity_socket(host, timeout=5):
    """Fallback connectivity test using socket connections"""
    try:
        # Try to connect to common ports (SSH, HTTP, HTTPS)
        ports = [22, 80, 443]
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    print(f"Socket test successful for {host}:{port}")
                    return {"ping": True, "error": None, "method": f"port {port}"}
            except Exception as port_error:
                print(f"Socket test failed for {host}:{port} - {port_error}")
                continue
        
        print(f"All socket tests failed for {host}")
        return {"ping": False, "error": "No accessible ports found"}
    except Exception as e:
        print(f"Socket test error for {host}: {e}")
        return {"ping": False, "error": f"Socket test error: {str(e)}"}

def test_connectivity_detailed(host, timeout=5):
    """Test basic connectivity with detailed diagnostics"""
    try:
        # Try ping first
        ping_locations = ['/usr/bin/ping', '/bin/ping', 'ping']
        ping_cmd = None
        
        for location in ping_locations:
            if os.path.exists(location) or location == 'ping':
                ping_cmd = location
                break
        
        if ping_cmd:
            try:
                result = subprocess.run([ping_cmd, '-c', '1', '-W', str(timeout), host], 
                                      capture_output=True, text=True, timeout=timeout+2)
                if result.returncode == 0:
                    return {
                        "status": "online",
                        "details": f"Ping successful to {host}",
                        "method": "ping",
                        "troubleshooting": []
                    }
                else:
                    # Try socket fallback
                    socket_result = test_connectivity_socket(host, timeout)
                    if socket_result["ping"]:
                        return {
                            "status": "online",
                            "details": f"Connectivity successful via {socket_result['method']} (ping failed but port accessible)",
                            "method": socket_result["method"],
                            "troubleshooting": ["Ping failed but port connectivity works - server may have ICMP disabled"]
                        }
                    else:
                        return {
                            "status": "offline",
                            "details": f"Ping failed (return code: {result.returncode}): {result.stderr.strip() or result.stdout.strip() or 'No response'}",
                            "method": "ping",
                            "troubleshooting": [
                                "Check if the server IP address is correct",
                                "Verify the server is powered on and connected to the network",
                                "Check firewall settings - server may be blocking ICMP packets",
                                "Try connecting from another machine to isolate network issues",
                                "Check if the server is behind a NAT/firewall that blocks ping"
                            ]
                        }
            except subprocess.TimeoutExpired:
                return {
                    "status": "offline",
                    "details": f"Ping timeout after {timeout} seconds",
                    "method": "ping",
                    "troubleshooting": [
                        "Server may be overloaded or unresponsive",
                        "Check network latency and connectivity",
                        "Verify the server is not in sleep/hibernation mode",
                        "Check if the server IP address is correct"
                    ]
                }
        else:
            # Fallback to socket test
            socket_result = test_connectivity_socket(host, timeout)
            if socket_result["ping"]:
                return {
                    "status": "online",
                    "details": f"Connectivity successful via {socket_result['method']}",
                    "method": socket_result["method"],
                    "troubleshooting": []
                }
            else:
                return {
                    "status": "offline",
                    "details": f"Socket connectivity failed: {socket_result['error']}",
                    "method": "socket",
                    "troubleshooting": [
                        "Check if the server IP address is correct",
                        "Verify the server is powered on and connected to the network",
                        "Check if SSH service is running on the server",
                        "Verify network routing and firewall settings"
                    ]
                }
    except Exception as e:
        return {
            "status": "error",
            "details": f"Connectivity test failed: {str(e)}",
            "method": "unknown",
            "troubleshooting": [
                "Check if the server IP address is correct",
                "Verify network connectivity to the server",
                "Check system resources on the Lockr server"
            ]
        }

def test_ssh_port_detailed(host, port, timeout=5):
    """Test SSH port with detailed diagnostics"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return {
                "status": "open",
                "details": f"SSH port {port} is accessible",
                "troubleshooting": []
            }
        else:
            return {
                "status": "closed",
                "details": f"SSH port {port} is not accessible (error code: {result})",
                "troubleshooting": [
                    "Check if SSH service is running on the server: sudo systemctl status ssh",
                    "Verify SSH is listening on port 22: sudo netstat -tlnp | grep :22",
                    "Check firewall settings: sudo ufw status or sudo iptables -L",
                    "Ensure SSH service is enabled: sudo systemctl enable ssh",
                    "Check if SSH is configured to listen on the correct interface",
                    "Verify the server is not behind a NAT that blocks port 22"
                ]
            }
    except Exception as e:
        return {
            "status": "error",
            "details": f"SSH port test failed: {str(e)}",
            "troubleshooting": [
                "Check if the server IP address is correct",
                "Verify network connectivity to the server",
                "Check if SSH service is running on the server"
            ]
        }

def test_ssh_authentication_detailed(host):
    """Test SSH authentication with detailed diagnostics"""
    try:
        if not os.path.exists(SSH_KEY_PATH):
            return {
                "status": "no_key",
                "details": f"SSH key not found at {SSH_KEY_PATH}",
                "troubleshooting": [
                    "Generate SSH key pair: ssh-keygen -t ed25519 -f ~/.ssh/lockr_key",
                    "Copy public key to server: ssh-copy-id -i ~/.ssh/lockr_key.pub user@server",
                    "Verify SSH key permissions: chmod 600 ~/.ssh/lockr_key",
                    "Check if SSH key path is correct in Lockr configuration"
                ]
            }
            
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            private_key = paramiko.Ed25519Key.from_private_key_file(SSH_KEY_PATH)
            ssh.connect(host, username=SSH_USER, pkey=private_key, timeout=10)
            ssh.close()
            return {
                "status": "authenticated",
                "details": f"SSH key authentication successful as {SSH_USER}",
                "troubleshooting": []
            }
        except paramiko.AuthenticationException as e:
            return {
                "status": "auth_failed",
                "details": f"SSH authentication failed: {str(e)}",
                "troubleshooting": [
                    "Verify the public key is installed on the server: ssh-copy-id -i ~/.ssh/lockr_key.pub user@server",
                    "Check if the correct user account is configured in Lockr",
                    "Verify SSH key permissions: chmod 600 ~/.ssh/lockr_key",
                    "Check server's authorized_keys file: ~/.ssh/authorized_keys",
                    "Ensure the public key matches the private key being used",
                    "Try manual SSH connection: ssh -i ~/.ssh/lockr_key user@server"
                ]
            }
        except paramiko.SSHException as e:
            return {
                "status": "ssh_error",
                "details": f"SSH connection error: {str(e)}",
                "troubleshooting": [
                    "Check if SSH service is running on the server",
                    "Verify SSH configuration allows key authentication",
                    "Check server logs: sudo journalctl -u ssh",
                    "Ensure the server is not blocking SSH connections"
                ]
            }
        except Exception as e:
            return {
                "status": "error",
                "details": f"SSH authentication test failed: {str(e)}",
                "troubleshooting": [
                    "Check if the server IP address is correct",
                    "Verify network connectivity to the server",
                    "Check SSH service status on the server"
                ]
            }
    except Exception as e:
        return {
            "status": "error",
            "details": f"SSH authentication test failed: {str(e)}",
            "troubleshooting": [
                "Check if the server IP address is correct",
                "Verify network connectivity to the server",
                "Check SSH service status on the server"
            ]
        }

def check_system_resources_detailed(host):
    """Check system resources with detailed diagnostics"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        private_key = paramiko.Ed25519Key.from_private_key_file(SSH_KEY_PATH)
        ssh.connect(host, username=SSH_USER, pkey=private_key, timeout=10)
        
        issues = []
        details = []
        
        # Check CPU load (more lenient threshold)
        try:
            stdin, stdout, stderr = ssh.exec_command("uptime | awk '{print $10}' | sed 's/,//'", timeout=10)
            cpu_load = stdout.read().decode().strip()
            if cpu_load and float(cpu_load) > 4.0:  # Increased threshold from 2.0 to 4.0
                issues.append(f"Very high CPU load: {cpu_load}")
            details.append(f"CPU Load: {cpu_load}")
        except:
            details.append("CPU Load: Unable to check")
        
        # Check memory usage (more lenient threshold)
        try:
            stdin, stdout, stderr = ssh.exec_command("free -m | awk 'NR==2{printf \"%.1f%%\", $3*100/$2}'", timeout=10)
            memory_usage = stdout.read().decode().strip()
            if memory_usage and float(memory_usage.replace('%', '')) > 95:  # Increased threshold from 90% to 95%
                issues.append(f"Very high memory usage: {memory_usage}")
            details.append(f"Memory Usage: {memory_usage}")
        except:
            details.append("Memory Usage: Unable to check")
        
        # Check disk usage (more lenient threshold)
        try:
            stdin, stdout, stderr = ssh.exec_command("df -h / | awk 'NR==2{print $5}'", timeout=10)
            disk_usage = stdout.read().decode().strip()
            if disk_usage and float(disk_usage.replace('%', '')) > 95:  # Increased threshold from 90% to 95%
                issues.append(f"Very high disk usage: {disk_usage}")
            details.append(f"Disk Usage: {disk_usage}")
        except:
            details.append("Disk Usage: Unable to check")
        
        # Check system uptime
        try:
            stdin, stdout, stderr = ssh.exec_command("uptime -p", timeout=10)
            uptime = stdout.read().decode().strip()
            details.append(f"Uptime: {uptime}")
        except:
            details.append("Uptime: Unable to check")
        
        ssh.close()
        
        if issues:
            return {
                "status": "issues",
                "details": "; ".join(details),
                "issues": issues,
                "troubleshooting": [
                    "Check running processes: top or htop",
                    "Monitor system resources: watch -n 1 'free -h && df -h'",
                    "Check system logs: sudo journalctl -f",
                    "Consider restarting services or the server if issues persist",
                    "Check for runaway processes consuming resources"
                ]
            }
        else:
            return {
                "status": "healthy",
                "details": "; ".join(details),
                "troubleshooting": []
            }
            
    except Exception as e:
        return {
            "status": "error",
            "details": f"System resource check failed: {str(e)}",
            "troubleshooting": [
                "Check if SSH authentication is working",
                "Verify the server is responsive",
                "Check system logs on the server"
            ]
        }

def generate_troubleshooting_recommendations(checks):
    """Generate overall troubleshooting recommendations based on check results"""
    recommendations = []
    
    # Connectivity issues
    if checks.get("connectivity", {}).get("status") == "offline":
        recommendations.append("🔴 CRITICAL: Server is not reachable - check network connectivity and server power")
    
    # SSH port issues
    if checks.get("ssh_port", {}).get("status") == "closed":
        recommendations.append("🟡 SSH service not accessible - check if SSH is running and firewall settings")
    
    # SSH auth issues
    if checks.get("ssh_auth", {}).get("status") in ["auth_failed", "no_key"]:
        recommendations.append("🟡 SSH authentication failed - verify SSH keys and user configuration")
    
    # System resource issues (less critical)
    if checks.get("system_resources", {}).get("status") == "issues":
        recommendations.append("🟡 System resource issues detected - monitor but not critical for basic functionality")
    
    # Priority order
    if not recommendations:
        recommendations.append("✅ All systems appear to be functioning normally")
    
    return recommendations

def try_alternative_server_setup(ip_address, hostname):
    """Try to set up SSH access directly from Lockr using alternative methods"""
    try:
        print(f"Attempting direct SSH setup for {ip_address}")
        
        # Try to connect using password authentication or other methods
        # This is a fallback for servers that don't have SSH keys yet
        setup_result = try_direct_ssh_setup(ip_address, hostname)
        
        if setup_result['success']:
            return {
                "success": True,
                "message": f"Server {hostname} ({ip_address}) added and SSH setup completed automatically",
                "setup_required": False,
                "setup_method": "direct",
                "details": "SSH access configured directly from Lockr"
            }
        else:
            return {
                "success": True,
                "message": f"Server {hostname} ({ip_address}) added but requires manual SSH setup",
                "setup_required": True,
                "setup_method": "manual",
                "error": setup_result['error'],
                "details": "Please set up SSH access manually and then use 'Test Connection' to verify"
            }
        
    except Exception as e:
        print(f"Alternative setup failed for {ip_address}: {e}")
        return {
            "success": True,
            "message": f"Server {hostname} ({ip_address}) added successfully",
            "setup_required": True,
            "setup_method": "error",
            "error": str(e)
        }

def generate_brian_setup_script(ip_address):
    """Generate the brian setup script with current SSH public key"""
    try:
        # Read the current user's public key
        public_key_path = SSH_KEY_PATH.replace('id_ed25519', 'id_ed25519.pub')
        if not os.path.exists(public_key_path):
            return None
        
        with open(public_key_path, 'r') as f:
            ssh_key_content = f.read().strip()
        
        # Extract just the key part (remove the comment)
        ssh_key = ssh_key_content.split()[1] if len(ssh_key_content.split()) > 1 else ssh_key_content
        
        # Generate the setup script
        script_content = f"""#!/bin/bash
set -e  # Exit immediately if any command exits with a non-zero status

# Custom parameters for the brian account
ADMIN_USER="brian"
SSH_KEY="{ssh_key}"
PUBKEY="ssh-ed25519 {ssh_key} brian@ser8"
HOME_DIR="/home/${{ADMIN_USER}}"
SUDOERS_FILE="/etc/sudoers.d/sudoers_${{ADMIN_USER}}"

echo "Setting up brian user account on $(hostname)..."

# Check if the user 'brian' exists; if not, create the user
if ! grep -q "^${{ADMIN_USER}}:" /etc/passwd; then
    echo "Creating local user ${{ADMIN_USER}}..."
    useradd -d "${{HOME_DIR}}" -m -s /bin/bash ${{ADMIN_USER}}
    passwd -l ${{ADMIN_USER}}
fi

# Ensure the .ssh directory exists for the user
if [ ! -d "${{HOME_DIR}}/.ssh" ]; then
    echo "Creating ${{HOME_DIR}}/.ssh directory..."
    mkdir -p "${{HOME_DIR}}/.ssh"
    chown -R ${{ADMIN_USER}}:${{ADMIN_USER}} "${{HOME_DIR}}"
    chmod 700 "${{HOME_DIR}}/.ssh"
fi  

# Path to the authorized_keys file
AUTHORIZED_KEYS="${{HOME_DIR}}/.ssh/authorized_keys"

# Add the public key if it is not already present
if [ ! -f "${{AUTHORIZED_KEYS}}" ] || ! grep -q "${{SSH_KEY}}" "${{AUTHORIZED_KEYS}}"; then
    echo "Adding public key to ${{AUTHORIZED_KEYS}}..."
    cat <<EOF >> "${{AUTHORIZED_KEYS}}"
${{PUBKEY}}
EOF
    chown -R ${{ADMIN_USER}}:${{ADMIN_USER}} "${{HOME_DIR}}/.ssh"
    chmod 600 "${{AUTHORIZED_KEYS}}"
fi

# Grant passwordless sudo privileges to the user
if [ ! -f "${{SUDOERS_FILE}}" ]; then
    echo "Setting up sudo for ${{ADMIN_USER}}..."
    echo "${{ADMIN_USER}} ALL=(ALL) NOPASSWD: ALL" > "${{SUDOERS_FILE}}"
    chmod 644 "${{SUDOERS_FILE}}"
fi

echo "Setup complete! User brian now has SSH key access and sudo privileges."
echo "You can now SSH to this server using: ssh brian@{ip_address}"
"""
        
        return script_content
        
    except Exception as e:
        print(f"Failed to generate setup script: {e}")
        return None

def try_direct_ssh_setup(ip_address, hostname):
    """Execute Ansible playbook to set up SSH access via central server"""
    try:
        print(f"Executing Ansible playbook for SSH setup on {ip_address}")
        
        # Path to the setup script
        setup_script = os.path.join(os.getcwd(), "setup_server_ssh.sh")
        
        if not os.path.exists(setup_script):
            return {
                "success": False,
                "error": f"Setup script not found: {setup_script}",
                "manual_steps": [
                    f"1. SSH to {ip_address} using existing credentials",
                    f"2. Add your SSH public key to ~/.ssh/authorized_keys",
                    f"3. Test SSH key authentication",
                    f"4. Use 'Test Connection' in Lockr to verify setup"
                ]
            }
        
        # Execute the Ansible playbook
        cmd = f"{setup_script} {ip_address} {hostname}"
        print(f"Executing: {cmd}")
        
        # Set environment variables for the subprocess
        env = os.environ.copy()
        env['PATH'] = f"/usr/local/bin:/usr/bin:/bin:{env.get('PATH', '')}"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300, env=env)
        
        print(f"Command output: {result.stdout}")
        print(f"Command error: {result.stderr}")
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": f"SSH setup completed successfully for {hostname} ({ip_address})",
                "output": result.stdout,
                "method": "ansible_playbook"
            }
        else:
            return {
                "success": False,
                "error": f"Ansible playbook failed with exit code {result.returncode}",
                "output": result.stdout,
                "error_output": result.stderr,
                "manual_steps": [
                    f"1. SSH to {ip_address} using existing credentials",
                    f"2. Add your SSH public key to ~/.ssh/authorized_keys",
                    f"3. Test SSH key authentication",
                    f"4. Use 'Test Connection' in Lockr to verify setup"
                ]
            }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Ansible playbook execution timed out (5 minutes)",
            "manual_steps": [
                f"1. SSH to {ip_address} using existing credentials",
                f"2. Add your SSH public key to ~/.ssh/authorized_keys",
                f"3. Test SSH key authentication",
                f"4. Use 'Test Connection' in Lockr to verify setup"
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Ansible playbook execution failed: {str(e)}",
            "manual_steps": [
                f"1. SSH to {ip_address} using existing credentials",
                f"2. Add your SSH public key to ~/.ssh/authorized_keys",
                f"3. Test SSH key authentication",
                f"4. Use 'Test Connection' in Lockr to verify setup"
            ]
        }

def test_ssh_connection(host, username, key_path, timeout=10):
    """Test SSH connection to a host"""
    try:
        print(f"Testing SSH connection to {host} as user {username}")
        print(f"Using key: {key_path}")
        
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Load private key
        try:
            private_key = paramiko.Ed25519Key.from_private_key_file(key_path)
            print(f"Private key loaded successfully")
        except Exception as key_error:
            print(f"Failed to load private key: {key_error}")
            return {"ssh": False, "error": f"Private key load failed: {str(key_error)}"}
        
        # Connect with timeout
        print(f"Attempting SSH connection...")
        ssh.connect(host, username=username, pkey=private_key, timeout=timeout)
        print(f"SSH connection established successfully")
        
        # Test basic command
        stdin, stdout, stderr = ssh.exec_command('whoami', timeout=5)
        user = stdout.read().decode().strip()
        print(f"Remote user: {user}")
        
        ssh.close()
        
        if user == username:
            return {"ssh": True, "error": None, "user": user}
        else:
            return {"ssh": False, "error": f"User mismatch: expected {username}, got {user}"}
            
    except paramiko.AuthenticationException as auth_error:
        print(f"SSH authentication failed: {auth_error}")
        return {"ssh": False, "error": f"SSH authentication failed: {str(auth_error)}"}
    except paramiko.SSHException as e:
        print(f"SSH error: {e}")
        return {"ssh": False, "error": f"SSH error: {str(e)}"}
    except socket.timeout:
        print(f"SSH connection timeout")
        return {"ssh": False, "error": "SSH connection timeout"}
    except Exception as e:
        print(f"Unexpected SSH error: {e}")
        return {"ssh": False, "error": f"Connection error: {str(e)}"}

def upload_and_execute_script(host, username, key_path, script_content):
    """Upload and execute the brian-install.sh script on a remote server"""
    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Load private key
        private_key = paramiko.Ed25519Key.from_private_key_file(key_path)
        
        # Connect
        ssh.connect(host, username=username, pkey=private_key, timeout=15)
        
        # Create SFTP client
        sftp = ssh.open_sftp()
        
        # First, upload the public key
        public_key_path = key_path.replace('id_ed25519', 'id_ed25519.pub')
        if not os.path.exists(public_key_path):
            return {
                "success": False,
                "error": f"Public key not found: {public_key_path}"
            }
        
        # Upload public key to /tmp
        remote_key_path = "/tmp/brian_public_key"
        sftp.put(public_key_path, remote_key_path)
        
        # Upload script to /tmp
        remote_script_path = "/tmp/brian-install.sh"
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(script_content)
            temp_file.flush()
            sftp.put(temp_file.name, remote_script_path)
        
        # Clean up local temp file
        os.unlink(temp_file.name)
        
        # Make script executable and run it
        ssh.exec_command(f"chmod +x {remote_script_path}")
        stdin, stdout, stderr = ssh.exec_command(f"sudo {remote_script_path}", timeout=60)
        
        # Wait for completion
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            # Verify setup by testing sudo access
            stdin, stdout, stderr = ssh.exec_command("sudo -n true", timeout=10)
            sudo_test = stdout.channel.recv_exit_status()
            
            if sudo_test == 0:
                # Clean up remote files
                ssh.exec_command(f"rm -f {remote_script_path} {remote_key_path}")
                
                ssh.close()
                return {
                    "success": True,
                    "message": "Script executed successfully and setup verified",
                    "exit_status": exit_status
                }
            else:
                ssh.exec_command(f"rm -f {remote_script_path} {remote_key_path}")
                ssh.close()
                return {
                    "success": False,
                    "error": "Setup verification failed - sudo access not working"
                }
        else:
            # Clean up remote files
            ssh.exec_command(f"rm -f {remote_script_path} {remote_key_path}")
            ssh.close()
            return {
                "success": False,
                "error": f"Script execution failed with exit status {exit_status}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Script execution error: {str(e)}"
        }

def generate_secure_password(length=16):
    """Generate a secure random password"""
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Ensure at least one character from each set
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(symbols)
    ]
    
    # Fill the rest randomly
    all_chars = lowercase + uppercase + digits + symbols
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))
    
    # Shuffle the password
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    return ''.join(password_list)

def create_vault_structure(server, username, password):
    """Create the vault directory structure and store password"""
    try:
        # Create timestamp for this password
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        vault_dir = f"{VAULT_DIR}/{server}_{username}_{timestamp}"
        
        # Create directory
        os.makedirs(vault_dir, exist_ok=True)
        
        # Create password file
        password_file = f"{vault_dir}/password.txt"
        with open(password_file, 'w') as f:
            f.write(password)
        
        # Create current pointer file
        current_file = f"{VAULT_DIR}/{server}_{username}_current"
        with open(current_file, 'w') as f:
            f.write(password_file)
        
        # Create initial timestamp file with creation time
        timestamp_file = f"{VAULT_DIR}/{server}_{username}_timestamp"
        creation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(timestamp_file, 'w') as f:
            f.write(creation_time)
        
        # Encrypt with Ansible Vault
        encrypted_file = f"{vault_dir}/password.txt.vault"
        
        # Try multiple possible ansible-vault locations
        vault_cmd = ANSIBLE_VAULT_CMD
        if vault_cmd == "ansible-vault":
            # Try to find the full path
            for possible_path in ['/usr/bin/ansible-vault', '/usr/local/bin/ansible-vault', 'ansible-vault']:
                if os.path.exists(possible_path) or possible_path == 'ansible-vault':
                    vault_cmd = possible_path
                    break
        
        print(f"Using ansible-vault command: {vault_cmd}")
        
        result = subprocess.run([
            vault_cmd, "encrypt", password_file,
            "--vault-password-file", VAULT_KEY,
            "--output", encrypted_file
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Remove plaintext password file
            os.remove(password_file)
            
            # Update current pointer to encrypted file
            with open(current_file, 'w') as f:
                f.write(encrypted_file)
            
            return {
                "success": True,
                "vault_dir": vault_dir,
                "encrypted_file": encrypted_file,
                "timestamp": timestamp
            }
        else:
            return {
                "success": False,
                "error": f"Vault encryption failed: {result.stderr}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error creating vault structure: {str(e)}"
        }

def retrieve_password_from_vault(server, username):
    """Retrieve password from Ansible Vault"""
    try:
        # Find the current password file
        current_file = f"{VAULT_DIR}/{server}_{username}_current"
        
        if not os.path.exists(current_file):
            return {
                "success": False,
                "error": f"No password found for {username}@{server}"
            }
        
        # Read the current encrypted file path
        with open(current_file, 'r') as f:
            encrypted_file = f.read().strip()
        
        if not os.path.exists(encrypted_file):
            return {
                "success": False,
                "error": f"Vault file not found: {encrypted_file}"
            }
        
        # Decrypt with Ansible Vault
        vault_cmd = ANSIBLE_VAULT_CMD
        if vault_cmd == "ansible-vault":
            # Try to find the full path
            for possible_path in ['/usr/bin/ansible-vault', '/usr/local/bin/ansible-vault', 'ansible-vault']:
                if os.path.exists(possible_path) or possible_path == 'ansible-vault':
                    vault_cmd = possible_path
                    break
        
        result = subprocess.run([
            vault_cmd, "decrypt", encrypted_file,
            "--vault-password-file", VAULT_KEY,
            "--output", "-"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Update the timestamp for this password (last access)
            update_password_timestamp(server, username)
            
            return {
                "success": True,
                "password": result.stdout.strip(),
                "server": server,
                "username": username,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": f"Vault decryption failed: {result.stderr}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error retrieving password: {str(e)}"
        }

def update_password_timestamp(server, username):
    """Update the timestamp for a password"""
    try:
        timestamp_file = os.path.join(VAULT_DIR, f"{server}_{username}_timestamp")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(timestamp_file, 'w') as f:
            f.write(current_time)
        return True
    except Exception as e:
        app.logger.error(f"Error updating timestamp for {username}@{server}: {e}")
        return False

def list_all_passwords():
    """List all available passwords in the vault"""
    try:
        passwords = []
        
        if not os.path.exists(VAULT_DIR):
            return {"success": False, "error": "Vault directory not found"}
        
        # Find all current pointer files
        for file in os.listdir(VAULT_DIR):
            if file.endswith('_current'):
                parts = file.replace('_current', '').split('_', 1)
                if len(parts) == 2:
                    server, username = parts
                    
                    # Get the actual password file path
                    current_file = os.path.join(VAULT_DIR, file)
                    with open(current_file, 'r') as f:
                        password_file = f.read().strip()
                    
                    # Check if timestamp file exists for this password
                    timestamp_file = os.path.join(VAULT_DIR, f"{server}_{username}_timestamp")
                    if os.path.exists(timestamp_file):
                        with open(timestamp_file, 'r') as f:
                            timestamp_str = f.read().strip()
                            last_updated = timestamp_str
                    else:
                        # Fallback to file modification time if no timestamp file
                        if os.path.exists(password_file):
                            mtime = os.path.getmtime(password_file)
                            last_updated = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            last_updated = "Unknown"
                        
                        # Create timestamp file for backward compatibility
                        try:
                            creation_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                            with open(timestamp_file, 'w') as f:
                                f.write(creation_time)
                        except Exception as e:
                            app.logger.error(f"Failed to create timestamp file for {username}@{server}: {e}")
                    
                    passwords.append({
                        "server": server,
                        "username": username,
                        "last_updated": last_updated,
                        "status": "active"
                    })
        
        return {"success": True, "passwords": passwords}
        
    except Exception as e:
        return {"success": False, "error": f"Error listing passwords: {str(e)}"}

@app.route('/')
def index():
    """Main dashboard page"""
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    
    servers = load_servers()
    
    # Count servers by actual status
    total_servers = len(servers)
    online_servers = 0
    offline_servers = 0
    degraded_servers = 0
    
    for server in servers:
        if server['status'] == 'online':
            online_servers += 1
        elif server['status'] == 'offline':
            offline_servers += 1
        elif server['status'] == 'degraded':
            degraded_servers += 1
        else:
            # If status is unknown, check connectivity
            if test_connectivity(server['ip'], timeout=3):
                server['status'] = 'online'
                online_servers += 1
            else:
                server['status'] = 'offline'
                offline_servers += 1
    
    # Save updated statuses
    save_servers(servers)
    
    return render_template('enhanced_dashboard.html', 
                         servers=servers,
                         total_servers=total_servers,
                         online_servers=online_servers,
                         offline_servers=offline_servers,
                         degraded_servers=degraded_servers)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple authentication page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple authentication - replace with proper auth in production
        if username == 'admin' and password == 'admin123':
            session.permanent = True  # Make session persistent
            session['authenticated'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('enhanced_login.html', error="Invalid credentials")
    
    return render_template('enhanced_login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/add_server', methods=['POST'])
def add_server():
    """API endpoint to add a new server"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    hostname = data.get('hostname')
    ip_address = data.get('ip_address')
    
    if not hostname or not ip_address:
        return jsonify({"error": "Hostname and IP address required"}), 400
    
    try:
        # Test basic connectivity first
        ping_result = test_connectivity(ip_address)
        if not ping_result['ping']:
            return jsonify({
                "success": False,
                "error": f"Connectivity test failed: {ping_result['error']}"
            }), 400
        
        # Check if SSH key exists
        if not os.path.exists(SSH_KEY_PATH):
            return jsonify({
                "success": False,
                "error": f"SSH private key not found: {SSH_KEY_PATH}. Please ensure your SSH key exists and update the SSH_KEY_PATH configuration."
            }), 400
        
        # Test SSH connection (this may fail for new servers without keys)
        ssh_result = test_ssh_connection(ip_address, SSH_USER, SSH_KEY_PATH)
        ssh_available = ssh_result['ssh']
        
        if not ssh_available:
            print(f"SSH not available for {ip_address}: {ssh_result['error']}")
            print(f"This is normal for new servers. Proceeding with setup...")
        
        # For new servers, we'll need to use alternative methods to deploy SSH keys
        # This could be via password authentication, cloud-init, or manual setup
        
        # Get the brian-install.sh script content
        script_content = """#!/bin/bash
set -e  # Exit immediately if any command exits with a non-zero status

# Custom parameters for the brian account
ADMIN_USER="brian"
SSH_KEY="$(cat /tmp/brian_public_key)"
PUBKEY="ssh-ed25519 ${SSH_KEY} ${ADMIN_USER}@ser8"
HOME_DIR="/home/${ADMIN_USER}"
SUDOERS_FILE="/etc/sudoers.d/sudoers_${ADMIN_USER}"

# Check if the user 'brian' exists; if not, create the user
if ! grep -q "^${ADMIN_USER}:" /etc/passwd; then
    echo "Creating local user ${ADMIN_USER}..."
    useradd -d "${HOME_DIR}" -m -s /bin/bash ${ADMIN_USER}
    passwd -l ${ADMIN_USER}
fi

# Ensure the .ssh directory exists for the user
if [ ! -d "${HOME_DIR}/.ssh" ]; then
    echo "Creating ${HOME_DIR}/.ssh directory..."
    mkdir -p "${HOME_DIR}/.ssh"
    chown -R ${ADMIN_USER}:${ADMIN_USER} "${HOME_DIR}"
    chmod 700 "${HOME_DIR}/.ssh"
fi  

# Path to the authorized_keys file
AUTHORIZED_KEYS="${HOME_DIR}/.ssh/authorized_keys"

# Add the public key if it is not already present
if [ ! -f "${AUTHORIZED_KEYS}" ] || ! grep -q "${SSH_KEY}" "${AUTHORIZED_KEYS}"; then
    echo "Adding public key to ${AUTHORIZED_KEYS}..."
    cat <<EOF >> "${AUTHORIZED_KEYS}"
${PUBKEY}
EOF
    chown -R ${ADMIN_USER}:${ADMIN_USER} "${HOME_DIR}/.ssh"
    chmod 600 "${AUTHORIZED_KEYS}"
fi

# Grant passwordless sudo privileges to the user
if [ ! -f "${SUDOERS_FILE}" ]; then
    echo "Setting up sudo for ${ADMIN_USER}..."
    echo "${ADMIN_USER} ALL=(ALL) NOPASSWD: ALL" > "${SUDOERS_FILE}"
    chmod 644 "${SUDOERS_FILE}"
fi
"""
        
        # Handle server setup based on SSH availability
        if ssh_available:
            # Server already has SSH access, execute setup script
            script_result = upload_and_execute_script(ip_address, SSH_USER, SSH_KEY_PATH, script_content)
        else:
            # Server doesn't have SSH access yet - try alternative setup methods
            script_result = try_alternative_server_setup(ip_address, hostname)
        
        if script_result['success']:
            # Add server to the list
            servers = load_servers()
            new_server = {
                "name": hostname,
                "ip": ip_address,
                "status": "online",
                "last_access": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "ssh_status": "connected" if ssh_available else "setup_required",
                "setup_date": datetime.now().isoformat(),
                "setup_required": not ssh_available
            }
            
            servers.append(new_server)
            save_servers(servers)
            
            # Log the successful addition
            log_action(session['username'], 'add_server', hostname, ip_address, 'success')
            
            if not ssh_available:
                return jsonify({
                    "success": True,
                    "message": f"Server {hostname} ({ip_address}) added successfully but requires manual SSH key setup. Please add your public key to the server manually.",
                    "server": new_server,
                    "setup_required": True,
                    "setup_instructions": [
                        "1. SSH to the server using existing credentials",
                        "2. Add your public key to ~/.ssh/authorized_keys",
                        "3. Test SSH key authentication",
                        "4. Use 'Test Connection' in Lockr to verify setup"
                    ]
                })
            else:
                return jsonify({
                    "success": True,
                    "message": f"Server {hostname} ({ip_address}) added successfully",
                    "server": new_server
                })
        else:
            return jsonify({
                "success": False,
                "error": f"Server setup failed: {script_result['error']}"
            }), 400
            
    except Exception as e:
        log_action(session['username'], 'add_server', hostname, ip_address, 'failed')
        return jsonify({
            "success": False,
            "error": f"Error adding server: {str(e)}"
        }), 500

@app.route('/api/test_server', methods=['POST'])
def test_server():
    """API endpoint to test server connectivity"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    ip_address = data.get('ip_address')
    
    if not ip_address:
        return jsonify({"error": "IP address required"}), 400
    
    try:
        # Test ping connectivity
        ping_result = test_connectivity(ip_address)
        
        # Test SSH connection if ping succeeds
        ssh_result = None
        if ping_result['ping']:
            ssh_result = test_ssh_connection(ip_address, SSH_USER, SSH_KEY_PATH)
        
        return jsonify({
            "success": True,
            "ping": ping_result,
            "ssh": ssh_result,
            "ip_address": ip_address
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error testing server: {str(e)}"
        }), 500

@app.route('/api/servers')
def get_servers():
    """API endpoint to get server list"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    servers = load_servers()
    return jsonify({"servers": servers, "status": "success"})

@app.route('/api/remove_server', methods=['POST'])
def remove_server():
    """API endpoint to remove a server from management"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    server_name = data.get('server_name')
    
    if not server_name:
        return jsonify({"error": "Server name required"}), 400
    
    servers = load_servers()
    
    # Find and remove the server
    original_count = len(servers)
    servers = [s for s in servers if s['name'] != server_name]
    
    if len(servers) == original_count:
        return jsonify({"error": f"Server '{server_name}' not found"}), 404
    
    # Save updated server list
    if save_servers(servers):
        return jsonify({
            "status": "success",
            "message": f"Server '{server_name}' removed successfully",
            "servers": servers
        })
    else:
        return jsonify({"error": "Failed to save server list"}), 500

@app.route('/api/validate_user', methods=['POST'])
def validate_user():
    """API endpoint to validate if a user exists on a server"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    server_ip = data.get('server_ip')
    username = data.get('username')
    
    if not server_ip or not username:
        return jsonify({"error": "Server IP and username required"}), 400
    
    try:
        # Test SSH connection and check if user exists
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Load private key
        if not os.path.exists(SSH_KEY_PATH):
            return jsonify({"error": f"SSH key not found at {SSH_KEY_PATH}"}), 500
        
        private_key = paramiko.Ed25519Key.from_private_key_file(SSH_KEY_PATH)
        
        # Connect to server
        ssh.connect(server_ip, username=SSH_USER, pkey=private_key, timeout=15)
        
        # Check if user exists
        stdin, stdout, stderr = ssh.exec_command(f'id {username}', timeout=10)
        user_exists = stdout.channel.recv_exit_status() == 0
        
        ssh.close()
        
        return jsonify({
            "status": "success",
            "user_exists": user_exists,
            "server_ip": server_ip,
            "username": username,
            "message": f"User '{username}' {'exists' if user_exists else 'does not exist'} on {server_ip}"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to validate user: {str(e)}"
        }), 500

@app.route('/api/change_user_password', methods=['POST'])
def change_user_password():
    """API endpoint to change a user's password on a server"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    server_ip = data.get('server_ip')
    username = data.get('username')
    new_password = data.get('new_password')
    
    if not server_ip or not username or not new_password:
        return jsonify({"error": "Server IP, username, and new password required"}), 400
    
    try:
        # Test SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Load private key
        if not os.path.exists(SSH_KEY_PATH):
            return jsonify({"error": f"SSH key not found at {SSH_KEY_PATH}"}), 500
        
        private_key = paramiko.Ed25519Key.from_private_key_file(SSH_KEY_PATH)
        
        # Connect to server
        ssh.connect(server_ip, username=SSH_USER, pkey=private_key, timeout=15)
        
        # Change user password using chpasswd
        change_password_cmd = f'echo "{username}:{new_password}" | sudo chpasswd'
        app.logger.info(f"Executing password change command: {change_password_cmd}")
        stdin, stdout, stderr = ssh.exec_command(change_password_cmd, timeout=30)
        exit_status = stdout.channel.recv_exit_status()
        
        app.logger.info(f"Password change command exit status: {exit_status}")
        stderr_output = stderr.read().decode()
        if stderr_output:
            app.logger.error(f"Password change stderr: {stderr_output}")
        
        if exit_status == 0:
            app.logger.info("Password change command succeeded, now verifying...")
            
            # For root users, skip SSH verification since root SSH login is often disabled
            if username == 'root':
                app.logger.info("Skipping SSH verification for root user (root SSH login typically disabled)")
                password_changed = True
            else:
                # Verify the password change worked by testing login for non-root users
                test_ssh = paramiko.SSHClient()
                test_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                try:
                    app.logger.info(f"Testing SSH connection with new password for {username}@{server_ip}")
                    test_ssh.connect(server_ip, username=username, password=new_password, timeout=10)
                    app.logger.info("SSH connection with new password successful")
                    test_ssh.close()
                    password_changed = True
                except Exception as verify_error:
                    app.logger.error(f"Password verification failed: {verify_error}")
                    password_changed = False
        else:
            app.logger.error(f"Password change command failed with exit status {exit_status}")
            password_changed = False
        
        ssh.close()
        
        if password_changed:
            # Update the timestamp for this password
            update_password_timestamp(server_ip, username)
            
            return jsonify({
                "status": "success",
                "message": f"Password for user '{username}' changed successfully on {server_ip}",
                "server_ip": server_ip,
                "username": username
            })
        else:
            return jsonify({
                "status": "error",
                "error": f"Failed to change password for user '{username}' on {server_ip}"
            }), 500
        
    except paramiko.AuthenticationException as auth_error:
        return jsonify({
            "status": "error",
            "error": f"SSH authentication failed: {str(auth_error)}",
            "details": "The server doesn't have your SSH key set up yet. Please set up SSH access first.",
            "solution": "Use 'Manage Servers' to add your SSH key to the server, or manually add it to ~/.ssh/authorized_keys"
        }), 500
    except paramiko.SSHException as ssh_error:
        return jsonify({
            "status": "error",
            "error": f"SSH connection error: {str(ssh_error)}",
            "details": "Unable to establish SSH connection to the server",
            "solution": "Check if the server is reachable and SSH is running on port 22"
        }), 500
    except socket.timeout:
        return jsonify({
            "status": "error",
            "error": "SSH connection timeout",
            "details": "The server didn't respond to SSH connection attempts",
            "solution": "Check server connectivity and firewall settings"
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to change password: {str(e)}",
            "details": "An unexpected error occurred during password change",
            "solution": "Check server logs and ensure SSH access is properly configured"
        }), 500

@app.route('/api/create_password', methods=['POST'])
def create_password():
    """API endpoint to create and store a new password"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    server = data.get('server')
    username = data.get('username')
    password_length = data.get('password_length', 16)
    
    if not server or not username:
        return jsonify({"error": "Server and username required"}), 400
    
    # Generate secure password
    new_password = generate_secure_password(password_length)
    
    # Store in vault
    result = create_vault_structure(server, username, new_password)
    
    if result['success']:
        # Update the timestamp for this password
        update_password_timestamp(server, username)
        
        # Log the creation for audit purposes
        log_action(session['username'], 'create', server, username, 'success')
        
        # Note: Password is stored in vault but not deployed to server
        # Server password change requires SSH access to be set up first
        return jsonify({
            "status": "success",
            "message": f"Password created for {username}@{server} and stored securely in Ansible Vault",
            "password": new_password,
            "server": server,
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "vault_location": result['vault_dir'],
            "note": "Password is stored securely but not yet deployed to the server. Use 'Change Password' feature after setting up SSH access."
        })
    else:
        log_action(session['username'], 'create', server, username, 'failed')
        return jsonify({
            "status": "error",
            "message": result['error']
        }), 400

@app.route('/api/retrieve_password', methods=['POST'])
def retrieve_password():
    """API endpoint to retrieve password"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    server = data.get('server')
    username = data.get('username', 'root')
    
    if not server:
        return jsonify({"error": "Server name required"}), 400
    
    result = retrieve_password_from_vault(server, username)
    
    if result['success']:
        # Log the access for audit purposes
        log_action(session['username'], 'retrieve', server, username, 'success')
        return jsonify({
            "status": "success",
            "password": result['password'],
            "server": server,
            "username": username,
            "timestamp": result['timestamp']
        })
    else:
        log_action(session['username'], 'retrieve', server, username, 'failed')
        return jsonify({
            "status": "error",
            "message": result['error']
        }), 400

@app.route('/api/list_passwords')
def get_passwords():
    """API endpoint to list all passwords"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    result = list_all_passwords()
    return jsonify(result)

@app.route('/api/health_check', methods=['POST'])
def health_check():
    """API endpoint to perform health check on a specific server"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 400

    data = request.get_json()
    server_ip = data.get('server_ip')
    server_name = data.get('server_name', 'Unknown')
    
    if not server_ip:
        return jsonify({"error": "Server IP required"}), 400
    
    try:
        health_result = perform_health_check(server_ip, server_name)
        return jsonify({
            "success": True,
            "health_data": health_result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Health check failed: {str(e)}"
        }), 500

@app.route('/api/health_check_all', methods=['POST'])
def health_check_all():
    """API endpoint to perform health check on all servers"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 400

    try:
        servers = load_servers()
        all_health_results = []
        
        for server in servers:
            health_result = perform_health_check(server['ip'], server['name'])
            all_health_results.append(health_result)
            
            # Update server status based on health check
            if health_result['overall_status'] == 'healthy':
                server['status'] = 'online'
            elif health_result['overall_status'] == 'degraded':
                server['status'] = 'degraded'
            else:
                server['status'] = 'offline'
        
        # Save updated server statuses
        save_servers(servers)
        
        return jsonify({
            "success": True,
            "health_results": all_health_results,
            "summary": {
                "total_servers": len(servers),
                "healthy": len([s for s in all_health_results if s['overall_status'] == 'healthy']),
                "degraded": len([s for s in all_health_results if s['overall_status'] == 'degraded']),
                "unhealthy": len([s for s in all_health_results if s['overall_status'] == 'unhealthy']),
                "offline": len([s for s in all_health_results if s['overall_status'] == 'unhealthy'])
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Health check failed: {str(e)}"
        }), 500

@app.route('/api/health_check_targeted', methods=['POST'])
def health_check_targeted():
    """API endpoint to perform health check on specific servers only"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 400

    data = request.get_json()
    target_servers = data.get('servers', [])
    
    if not target_servers:
        return jsonify({"error": "No servers specified"}), 400
    
    try:
        all_health_results = []
        
        for server_data in target_servers:
            server_ip = server_data.get('ip')
            server_name = server_data.get('server', 'Unknown')
            
            if server_ip:
                health_result = perform_health_check(server_ip, server_name)
                all_health_results.append(health_result)
        
        # Update server statuses in the stored servers list
        servers = load_servers()
        for i, server in enumerate(servers):
            for health_result in all_health_results:
                if server['ip'] == health_result['ip']:
                    if health_result['overall_status'] == 'healthy':
                        servers[i]['status'] = 'online'
                    elif health_result['overall_status'] == 'degraded':
                        servers[i]['status'] = 'degraded'
                    else:
                        servers[i]['status'] = 'offline'
                    break
        
        # Save updated server statuses
        save_servers(servers)
        
        return jsonify({
            "success": True,
            "health_results": all_health_results,
            "summary": {
                "total_checked": len(all_health_results),
                "healthy": len([s for s in all_health_results if s['overall_status'] == 'healthy']),
                "degraded": len([s for s in all_health_results if s['overall_status'] == 'degraded']),
                "unhealthy": len([s for s in all_health_results if s['overall_status'] == 'unhealthy'])
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Targeted health check failed: {str(e)}"
        }), 500

@app.route('/api/debug_connectivity', methods=['POST'])
def debug_connectivity():
    """Debug endpoint to test connectivity directly"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 400

    data = request.get_json()
    ip_address = data.get('ip_address')
    
    if not ip_address:
        return jsonify({"error": "IP address required"}), 400
    
    print(f"Debug connectivity test for {ip_address}")
    
    # Test ping directly
    try:
        result = subprocess.run(['/usr/bin/ping', '-c', '1', '-W', '3', ip_address], 
                              capture_output=True, text=True, timeout=7)
        print(f"Direct ping result: returncode={result.returncode}")
        print(f"Direct ping stdout: {result.stdout}")
        print(f"Direct ping stderr: {result.stderr}")
        
        return jsonify({
            "ping_returncode": result.returncode,
            "ping_stdout": result.stdout,
            "ping_stderr": result.stderr,
            "ping_success": result.returncode == 0
        })
    except Exception as e:
        print(f"Direct ping error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug_ssh', methods=['POST'])
def debug_ssh():
    """Debug endpoint to test SSH connection directly"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 400

    data = request.get_json()
    ip_address = data.get('ip_address')
    username = data.get('username', 'brian')
    
    if not ip_address:
        return jsonify({"error": "IP address required"}), 400
    
    print(f"Debug SSH test for {username}@{ip_address}")
    
    # Test SSH connection directly
    try:
        from config import SSH_KEY_PATH
        result = test_ssh_connection(ip_address, username, SSH_KEY_PATH, timeout=15)
        print(f"SSH test result: {result}")
        
        return jsonify(result)
    except Exception as e:
        print(f"SSH test error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/retry_server_setup/<hostname>')
def retry_server_setup(hostname):
    """Retry SSH setup for a server that failed initial setup"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 400
    
    try:
        # Find the server in the servers list
        servers = load_servers()
        server = None
        for s in servers:
            if s.get('name') == hostname:
                server = s
                break
        
        if not server:
            return jsonify({"error": f"Server {hostname} not found"}), 404
        
        # Generate the setup script
        setup_script = generate_brian_setup_script(server['ip'])
        if not setup_script:
            return jsonify({"error": "Failed to generate setup script"}), 500
        
        # Try direct SSH setup
        setup_result = try_direct_ssh_setup(server['ip'], hostname)
        
        if setup_result['success']:
            # Update server status to connected
            for s in servers:
                if s.get('name') == hostname:
                    s['ssh_status'] = 'connected'
                    s['setup_required'] = False
                    break
            save_servers(servers)
            
            return jsonify({
                "success": True,
                "message": f"SSH setup completed successfully for {hostname}",
                "details": setup_result.get('details', 'SSH access configured')
            })
        else:
            return jsonify({
                "success": False,
                "error": f"SSH setup failed: {setup_result['error']}",
                "manual_steps": setup_result.get('manual_steps', [])
            }), 500
        
    except Exception as e:
        return jsonify({"error": f"Failed to retry setup: {str(e)}"}), 500

@app.route('/api/change_admin_password', methods=['POST'])
def change_admin_password():
    """API endpoint to change admin password"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 400
    
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({"error": "Current and new password required"}), 400
    
    # Validate current password (hardcoded for demo - in production use proper auth)
    if current_password != "admin123":
        return jsonify({"error": "Current password is incorrect"}), 400
    
    # Validate new password
    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters long"}), 400
    
    # In production, you would:
    # 1. Hash the new password
    # 2. Store it in a secure database
    # 3. Update the authentication system
    
    # For now, we'll just return success
    # TODO: Implement actual password storage and update mechanism
    
    log_action(session['username'], 'change_admin_password', 'system', 'admin', 'success')
    
    return jsonify({
        "success": True,
        "message": "Password changed successfully. Please log in with your new password."
    })

def log_action(user, action, server, target_user, status):
    """Log actions for audit purposes"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "action": action,
        "server": server,
        "target_user": target_user,
        "status": status,
        "ip": request.remote_addr
    }
    
    # In production, log to a proper logging system
    print(f"ACTION_LOG: {json.dumps(log_entry)}")

if __name__ == '__main__':
    # Ensure vault directory exists
    os.makedirs(VAULT_DIR, exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
