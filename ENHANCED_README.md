# 🔒 Lockr - Enterprise Server & Password Management

A comprehensive web-based password management system that combines secure password storage with automated server provisioning and management capabilities.

## ✨ Features

### 🔐 Password Management
- **Secure Password Generation**: Generate cryptographically secure random passwords
- **Ansible Vault Integration**: Store passwords encrypted using Ansible Vault
- **Password Retrieval**: Secure access to stored passwords with audit logging
- **User Management**: Manage passwords for different users (root, admin, etc.)

### 🖥️ Server Management
- **Automated Server Provisioning**: Add new servers through the web interface
- **SSH Key Distribution**: Automatically configure SSH access using your existing keys
- **Script Execution**: Upload and execute your `brian-install.sh` script remotely
- **Connectivity Testing**: Test ping and SSH connectivity before adding servers
- **Status Monitoring**: Real-time server status and health monitoring
- **Automatic Cleanup**: Remove temporary files after server setup

### 🎨 User Interface
- **Modern Web Dashboard**: Professional Bootstrap 5 interface
- **Light/Dark Mode**: Toggle between themes with persistent preferences
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-time Updates**: Live status updates and notifications

## 🏗️ Architecture

### Core Components
```
Lockr Enterprise Platform
├── Flask Web Application (enhanced_unified_manager.py)
├── Web Interface (enhanced_dashboard.html, enhanced_login.html)
├── SSH Management (paramiko-based)
├── Ansible Vault Integration
├── Server Provisioning Engine
└── Audit Logging System
```

### Data Flow
1. **Server Addition**: User inputs hostname/IP → Connectivity test → SSH setup → Script execution → Verification → Storage
2. **Password Management**: Generate → Encrypt → Store in Vault → Retrieve → Decrypt → Display
3. **Security**: All operations logged, SSH keys managed securely, temporary files cleaned up

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- SSH key pair (`~/.ssh/brian_id_rsa` and `~/.ssh/brian_id_rsa.pub`)
- Ansible Vault setup (optional, for enhanced security)

### Installation

1. **Clone or download the files** to your desired directory
2. **Make the startup script executable**:
   ```bash
   chmod +x start_enhanced_manager.sh
   ```

3. **Run the startup script**:
   ```bash
   ./start_enhanced_manager.sh
   ```

4. **Access the web interface** at `http://localhost:5000`
5. **Login** with default credentials: `admin` / `admin123`

### First Run Setup

The startup script will automatically:
- Create a Python virtual environment
- Install all required dependencies
- Start the Flask web server
- Display connection information

## 🔧 Configuration

### File Paths
Edit `enhanced_unified_manager.py` to customize these paths:

```python
# Configuration - adjust these paths to match your system
VAULT_DIR = "/home/brian/playbooks/vault"
VAULT_KEY = "/home/brian/playbooks/.vault_key"
SSH_KEY_PATH = "/home/brian/.ssh/brian_id_rsa"
SSH_USER = "brian"
SERVERS_FILE = "/home/brian/playbooks/servers.json"
```

### SSH Key Setup
Ensure your SSH key pair is properly configured:
```bash
# Check if keys exist
ls -la ~/.ssh/brian_id_rsa*

# Set proper permissions
chmod 600 ~/.ssh/brian_id_rsa
chmod 644 ~/.ssh/brian_id_rsa.pub

# Test SSH connection to a target server
ssh -i ~/.ssh/brian_id_rsa brian@target_server_ip
```

## 📱 Usage Guide

### Adding a New Server

1. **Click "Add New Server"** from the Quick Actions section
2. **Enter server details**:
   - Hostname (e.g., "webserver", "database")
   - IP Address (e.g., "192.168.1.100")
3. **Test connection** to verify connectivity
4. **Click "Add Server"** to begin provisioning

The system will automatically:
- Test ping connectivity
- Verify SSH access
- Upload your `brian-install.sh` script
- Execute the script with sudo privileges
- Verify the setup (SSH key access, sudo privileges)
- Clean up temporary files
- Add the server to your management system

### Managing Passwords

#### Create Password
1. **Click "Create Password"** from Quick Actions
2. **Select server** from the dropdown
3. **Enter username** (default: root)
4. **Set password length** (8-64 characters)
5. **Click "Create Password"**

#### Retrieve Password
1. **Click "Retrieve Password"** from Quick Actions
2. **Select server** and **username**
3. **Click "Retrieve"**
4. **Copy password** using the copy button

### Server Management

#### View Server Status
- **Dashboard cards** show real-time server status
- **Color-coded indicators** (green=online, red=offline)
- **Quick action buttons** for each server

#### Monitor Servers
- **Refresh status** button updates all server information
- **Individual server cards** show detailed information
- **SSH status** and **last access** timestamps

## 🔒 Security Features

### Authentication
- **Session-based authentication** with secure cookies
- **Configurable credentials** (change default admin/admin123)
- **Logout functionality** with session cleanup

### Data Protection
- **Ansible Vault encryption** for password storage
- **SSH key-based authentication** for server access
- **Temporary file cleanup** after operations
- **Audit logging** of all actions

### Network Security
- **Localhost-only binding** by default
- **SSH key verification** before server operations
- **Connection timeouts** to prevent hanging operations

## 🛠️ Troubleshooting

### Common Issues

#### SSH Connection Failed
```bash
# Check SSH key permissions
chmod 600 ~/.ssh/brian_id_rsa
chmod 644 ~/.ssh/brian_id_rsa.pub

# Test SSH connection manually
ssh -i ~/.ssh/brian_id_rsa brian@target_ip

# Verify SSH agent
ssh-add ~/.ssh/brian_id_rsa
```

#### Python Dependencies
```bash
# Reinstall virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r enhanced_requirements.txt
```

#### Permission Issues
```bash
# Check file permissions
chmod +x start_enhanced_manager.sh
chmod 755 templates/
chmod 644 *.py *.html *.txt
```

### Error Messages

#### "SSH authentication failed"
- Verify SSH key exists and has correct permissions
- Check if target server has your public key in `~/.ssh/authorized_keys`
- Ensure SSH service is running on target server

#### "Script execution failed"
- Verify sudo access on target server
- Check if `brian-install.sh` script has execute permissions
- Review server logs for detailed error information

#### "Vault encryption failed"
- Ensure Ansible Vault is installed
- Verify vault key file exists and is readable
- Check vault directory permissions

## 🔧 Advanced Configuration

### Custom Script Integration
Modify the script content in `enhanced_unified_manager.py`:

```python
# Get the brian-install.sh script content
script_content = """#!/bin/bash
# Your custom server setup script here
# This will be executed on new servers
"""
```

### Database Integration
Replace file-based storage with a database:

```python
# Example: SQLite integration
import sqlite3

def load_servers():
    conn = sqlite3.connect('servers.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM servers')
    servers = cursor.fetchall()
    conn.close()
    return servers
```

### Custom Authentication
Implement your own authentication system:

```python
# Example: LDAP integration
import ldap

def authenticate_user(username, password):
    # Your LDAP authentication logic here
    pass
```

## 📊 Monitoring and Logging

### Audit Logs
All operations are logged with timestamps:
```json
{
    "timestamp": "2024-08-30T15:30:00",
    "user": "admin",
    "action": "add_server",
    "server": "webserver",
    "target_user": "192.168.1.100",
    "status": "success",
    "ip": "127.0.0.1"
}
```

### Performance Metrics
- **Server response times** for connectivity tests
- **Script execution duration** for provisioning
- **Password operation counts** and success rates

## 🚀 Production Deployment

### Security Considerations
1. **Change default credentials** immediately
2. **Use HTTPS** with proper SSL certificates
3. **Implement proper authentication** (LDAP, OAuth, etc.)
4. **Restrict network access** to authorized IPs
5. **Regular security updates** for dependencies

### Scaling
- **Load balancing** for multiple instances
- **Database backend** for large deployments
- **Redis caching** for session management
- **Monitoring and alerting** for production use

### Backup Strategy
- **Regular backups** of vault files and server data
- **Configuration version control** using Git
- **Disaster recovery** procedures documented

## 🤝 Contributing

### Development Setup
1. **Fork the repository**
2. **Create feature branch**
3. **Make changes** with proper testing
4. **Submit pull request** with description

### Testing
```bash
# Run basic tests
python -m pytest tests/

# Manual testing
./start_enhanced_manager.sh
# Navigate to http://localhost:5000
# Test all functionality manually
```

## 📄 License

This project is provided as-is for educational and operational purposes. Use at your own risk in production environments.

## 🆘 Support

### Documentation
- **This README** contains comprehensive usage information
- **Code comments** provide implementation details
- **Error messages** include troubleshooting guidance

### Community
- **GitHub Issues** for bug reports and feature requests
- **Code examples** in the source files
- **Configuration templates** for common use cases

---

**🎯 Ready to transform your server management workflow? Start Lockr and experience enterprise-grade server provisioning with secure password management!**
