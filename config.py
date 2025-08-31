#!/usr/bin/env python3
"""
Lockr Configuration File
Customize these settings to match your environment
"""

import os

# SSH Configuration
SSH_KEY_PATH = "/home/brian/.ssh/id_ed25519"  # Your private SSH key path
SSH_USER = "brian"  # Your SSH username

# Ansible Vault Configuration
VAULT_DIR = "/home/brian/playbooks/vault"  # Directory for storing encrypted passwords
VAULT_KEY = "/home/brian/playbooks/.vault_key"  # Path to your vault key file
ANSIBLE_VAULT_CMD = "ansible-vault"  # Ansible vault command

# Server Management
SERVERS_FILE = "/home/brian/playbooks/servers.json"  # File to store server information

# Web Interface
WEB_HOST = "0.0.0.0"  # Host to bind to (0.0.0.0 for all interfaces)
WEB_PORT = 5000  # Port to run on
WEB_DEBUG = True  # Debug mode (set to False in production)

# Authentication (for development - change in production)
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"

# Timeouts
SSH_TIMEOUT = 15  # SSH connection timeout in seconds
SCRIPT_TIMEOUT = 60  # Script execution timeout in seconds
PING_TIMEOUT = 5  # Ping timeout in seconds

# Ensure required directories exist
os.makedirs(VAULT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SERVERS_FILE), exist_ok=True)
