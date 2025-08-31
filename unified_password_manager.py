#!/usr/bin/env python3
"""
Unified Password Manager
Combines password creation, Ansible Vault storage, and retrieval in one interface
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

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Configuration - adjust these paths to match your system
VAULT_DIR = "/home/brian/playbooks/vault"
VAULT_KEY = "/home/brian/playbooks/.vault_key"
ANSIBLE_VAULT_CMD = "ansible-vault"

# Mock data for demonstration (replace with actual data in production)
MOCK_SERVERS = [
    {"name": "valheim", "ip": "192.168.1.100", "status": "online", "last_access": "2024-08-30 14:30"},
    {"name": "archie", "ip": "192.168.1.101", "status": "online", "last_access": "2024-08-30 15:45"},
    {"name": "zero", "ip": "192.168.1.102", "status": "offline", "last_access": "2024-08-30 12:15"}
]

MOCK_USERS = ["root", "admin", "backup", "monitoring"]

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
        result = subprocess.run([
            ANSIBLE_VAULT_CMD, "encrypt", password_file,
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
        result = subprocess.run([
            ANSIBLE_VAULT_CMD, "decrypt", encrypted_file,
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
    
    return render_template('unified_dashboard.html', 
                         servers=MOCK_SERVERS,
                         total_servers=len(MOCK_SERVERS),
                         online_servers=len([s for s in MOCK_SERVERS if s['status'] == 'online']))

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
            return render_template('unified_login.html', error="Invalid credentials")
    
    return render_template('unified_login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

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
        
        return jsonify({
            "status": "success",
            "message": f"Password created for {username}@{server}",
            "password": new_password,
            "server": server,
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "vault_location": result['vault_dir']
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

@app.route('/api/servers')
def get_servers():
    """API endpoint to get server list"""
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify({"servers": MOCK_SERVERS, "status": "success"})

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
