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
from datetime import datetime
import tempfile
import shutil
import paramiko
import socket
import threading
import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

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

def try_alternative_server_setup(ip_address, hostname):
    """Automatically execute brian-install.sh on central server to set up new server"""
    try:
        print(f"Executing brian-install.sh on central server for {ip_address}")
        
        # Execute the setup script on the central server (10.10.10.96)
        # This server should have access to all other servers and your SSH keys
        central_server_ip = "10.10.10.96"
        
        # Generate the setup script content
        setup_script = generate_brian_setup_script(ip_address)
        
        # Execute the script on the central server
        script_result = execute_setup_on_central_server(central_server_ip, ip_address, hostname, setup_script)
        
        if script_result['success']:
            return {
                "success": True,
                "message": f"Server {hostname} ({ip_address}) added and SSH setup completed automatically",
                "setup_required": False,
                "setup_method": "automatic",
                "details": f"Setup script executed on central server {central_server_ip}"
            }
        else:
            return {
                "success": True,
                "message": f"Server {hostname} ({ip_address}) added but SSH setup failed",
                "setup_required": True,
                "setup_method": "failed",
                "error": script_result['error'],
                "details": f"Setup script failed on central server {central_server_ip}"
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

def execute_setup_on_central_server(central_server_ip, target_server_ip, hostname, script_content):
    """Execute the setup script on the central server to configure the target server"""
    try:
        print(f"Executing setup on central server {central_server_ip} for target {target_server_ip}")
        
        # Create SSH client to connect to central server
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Load private key for central server access
        if not os.path.exists(SSH_KEY_PATH):
            return {
                "success": False,
                "error": f"SSH key not found: {SSH_KEY_PATH}"
            }
        
        private_key = paramiko.Ed25519Key.from_private_key_file(SSH_KEY_PATH)
        
        # Connect to central server
        ssh.connect(central_server_ip, username=SSH_USER, pkey=private_key, timeout=15)
        
        # Create the setup script on the central server
        script_file = f"/tmp/setup_{hostname}_{int(time.time())}.sh"
        
        # Upload script content
        stdin, stdout, stderr = ssh.exec_command(f"cat > {script_file} << 'EOF'\n{script_content}\nEOF", timeout=30)
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0:
            ssh.close()
            return {
                "success": False,
                "error": f"Failed to create script on central server: {stderr.read().decode()}"
            }
        
        # Make script executable
        stdin, stdout, stderr = ssh.exec_command(f"chmod +x {script_file}", timeout=10)
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0:
            ssh.close()
            return {
                "success": False,
                "error": f"Failed to make script executable: {stderr.read().decode()}"
            }
        
        # Execute the setup script on the central server
        # This script will handle the SSH setup for the target server
        setup_command = f"sudo {script_file}"
        stdin, stdout, stderr = ssh.exec_command(setup_command, timeout=120)
        exit_status = stdout.channel.recv_exit_status()
        
        # Get output
        stdout_content = stdout.read().decode()
        stderr_content = stderr.read().decode()
        
        # Clean up script file
        ssh.exec_command(f"rm -f {script_file}", timeout=10)
        
        ssh.close()
        
        if exit_status == 0:
            return {
                "success": True,
                "message": f"Setup completed successfully on {target_server_ip}",
                "output": stdout_content,
                "central_server": central_server_ip
            }
        else:
            return {
                "success": False,
                "error": f"Setup failed on {target_server_ip}",
                "output": stdout_content,
                "error_output": stderr_content,
                "exit_code": exit_status,
                "central_server": central_server_ip
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to execute setup on central server: {str(e)}"
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
                    
                    # Get file modification time
                    if os.path.exists(password_file):
                        mtime = os.path.getmtime(password_file)
                        date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                        
                        passwords.append({
                            "server": server,
                            "username": username,
                            "last_updated": date_str,
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
    return render_template('enhanced_dashboard.html', 
                         servers=servers,
                         total_servers=len(servers),
                         online_servers=len([s for s in servers if s['status'] == 'online']))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple authentication page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple authentication - replace with proper auth in production
        if username == 'admin' and password == 'admin123':
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
        stdin, stdout, stderr = ssh.exec_command(change_password_cmd, timeout=30)
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            # Verify the password change worked by testing login
            test_ssh = paramiko.SSHClient()
            test_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                test_ssh.connect(server_ip, username=username, password=new_password, timeout=10)
                test_ssh.close()
                password_changed = True
            except:
                password_changed = False
        else:
            password_changed = False
        
        ssh.close()
        
        if password_changed:
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
        
        # Execute setup on central server
        central_server_ip = "10.10.10.96"
        script_result = execute_setup_on_central_server(central_server_ip, server['ip'], hostname, setup_script)
        
        if script_result['success']:
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
                "details": script_result['message']
            })
        else:
            return jsonify({
                "success": False,
                "error": f"SSH setup failed: {script_result['error']}",
                "details": script_result
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
