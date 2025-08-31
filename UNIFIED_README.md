# Unified Password Manager

A comprehensive, enterprise-grade password management system that combines **password creation**, **Ansible Vault storage**, and **retrieval** in one unified graphical interface.

## 🚀 What This System Does

### **Password Creation**
- **Generates secure random passwords** with configurable length (8-64 characters)
- **Ensures complexity** - includes lowercase, uppercase, digits, and symbols
- **Automatic storage** in Ansible Vault for maximum security

### **Secure Storage**
- **Ansible Vault encryption** for all password files
- **Timestamped directories** for password history tracking
- **Current pointer system** for easy access to latest passwords
- **Automatic cleanup** of plaintext files after encryption

### **Easy Retrieval**
- **One-click password access** through web interface
- **Copy-to-clipboard** functionality for quick use
- **Search by server and username** combinations
- **Audit logging** of all access attempts

## 🏗️ System Architecture

```
~/playbooks/
├── vault/                           # Encrypted password storage
│   ├── server_username_timestamp/   # Individual password directories
│   │   └── password.txt.vault      # Encrypted password file
│   └── server_username_current     # Pointer to latest password
├── .vault_key                      # Master encryption key
└── password-manager/               # Web interface files
    ├── unified_password_manager.py  # Main Flask application
    ├── templates/                   # HTML templates
    └── start_unified_manager.sh    # Startup script
```

## 🔐 Security Features

### **Password Generation**
- **Cryptographically secure** random generation
- **Complexity requirements** enforced
- **Configurable length** (8-64 characters)
- **No weak patterns** or predictable sequences

### **Storage Security**
- **Ansible Vault encryption** (industry standard)
- **Master key protection** with restricted permissions
- **Automatic plaintext cleanup** after encryption
- **Timestamped versioning** for audit trails

### **Access Control**
- **User authentication** system
- **Session management** with secure cookies
- **Audit logging** of all operations
- **IP address tracking** for security monitoring

## 🎯 Key Features

### **Unified Interface**
- **Single dashboard** for all password operations
- **Light/dark mode** toggle for user preference
- **Responsive design** works on all devices
- **Professional appearance** suitable for enterprise use

### **Quick Actions**
- **Create passwords** for any server/user combination
- **Retrieve passwords** with one click
- **View all stored passwords** in organized tables
- **Server status monitoring** with visual indicators

### **Management Tools**
- **Password inventory** across all servers
- **User management** by server
- **History tracking** for compliance
- **Bulk operations** for efficiency

## 🚀 Quick Start

### **1. Install Dependencies**
```bash
# Install Ansible
sudo apt update
sudo apt install ansible

# Install Python packages
sudo apt install python3 python3-pip python3-venv python3-full
```

### **2. Set Up Your Environment**
```bash
# Create directory structure
mkdir -p ~/playbooks/{vault,password-manager}

# Navigate to password manager
cd ~/playbooks/password-manager

# Copy files from this repository
# (You'll need to copy the files manually or clone the repo)
```

### **3. Configure Paths**
Edit `unified_password_manager.py` and update:
```python
VAULT_DIR = "/home/YOUR_USERNAME/playbooks/vault"
VAULT_KEY = "/home/YOUR_USERNAME/playbooks/.vault_key"
```

### **4. Generate Vault Key**
```bash
cd ~/playbooks
openssl rand -hex 32 > .vault_key
chmod 600 .vault_key
```

### **5. Start the System**
```bash
cd ~/playbooks/password-manager
chmod +x start_unified_manager.sh
./start_unified_manager.sh
```

### **6. Access Web Interface**
- Open browser to `http://localhost:5000`
- Login with `admin` / `admin123`
- Start creating and managing passwords!

## 📱 Using the Interface

### **Creating Passwords**
1. Click **"Create New Password"** button
2. Select **server** from dropdown
3. Enter **username** (defaults to "root")
4. Choose **password length** (8-64 characters)
5. Click **"Create Password"**
6. **Copy the generated password** to clipboard
7. Password is **automatically encrypted** and stored

### **Retrieving Passwords**
1. Click **"Retrieve Password"** button
2. Select **server** and **username**
3. Click **"Retrieve"**
4. **Copy the decrypted password** to clipboard
5. Access is **logged for audit purposes**

### **Managing Passwords**
- **View all passwords** in organized tables
- **See password history** by server
- **Monitor access patterns** and usage
- **Track password age** and rotation needs

## 🔧 Configuration Options

### **Server Management**
Update `MOCK_SERVERS` in `unified_password_manager.py`:
```python
MOCK_SERVERS = [
    {"name": "your-server", "ip": "192.168.1.100", "status": "online", "last_access": "2024-08-30 14:30"},
    # Add more servers...
]
```

### **Password Policies**
Modify `generate_secure_password()` function for:
- **Character set requirements**
- **Length restrictions**
- **Complexity rules**
- **Special character handling**

### **Security Settings**
- **Session timeout** configuration
- **Password expiration** policies
- **Access rate limiting**
- **Audit log retention**

## 🛡️ Production Deployment

### **Security Hardening**
1. **Change default credentials** (`admin/admin123`)
2. **Use HTTPS** with SSL certificates
3. **Implement proper user management**
4. **Add role-based access control**
5. **Enable two-factor authentication**

### **Infrastructure**
1. **Use production WSGI server** (Gunicorn/uWSGI)
2. **Set up reverse proxy** (nginx/Apache)
3. **Configure monitoring** and alerting
4. **Implement backup** and recovery
5. **Add load balancing** for high availability

### **Compliance**
1. **Password policy enforcement**
2. **Regular security audits**
3. **Access review procedures**
4. **Incident response plans**
5. **Regulatory compliance** (SOX, HIPAA, etc.)

## 🐛 Troubleshooting

### **Common Issues**

**"Vault encryption failed"**
- Check Ansible installation: `ansible --version`
- Verify vault key permissions: `chmod 600 .vault_key`
- Ensure vault directory exists and is writable

**"Module not found"**
- Activate virtual environment: `source venv/bin/activate`
- Install requirements: `pip install -r requirements.txt`
- Check Python version: `python3 --version`

**"Permission denied"**
- Fix file permissions: `chmod +x start_unified_manager.sh`
- Check directory ownership: `ls -la ~/playbooks`
- Verify vault key access: `ls -la ~/playbooks/.vault_key`

**"Port already in use"**
- Find process: `lsof -i :5000`
- Kill process: `kill -9 <PID>`
- Or change port in `unified_password_manager.py`

### **Debug Mode**
Enable debug logging by setting:
```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

## 📈 Advanced Features

### **API Integration**
- **RESTful API endpoints** for automation
- **JSON request/response** handling
- **Authentication headers** for security
- **Rate limiting** and throttling

### **Automation**
- **Ansible playbook integration** for password deployment
- **Scheduled password rotation** with cron jobs
- **Bulk password operations** for multiple servers
- **API-based password management** for DevOps workflows

### **Monitoring**
- **Real-time server status** checking
- **Password expiration alerts**
- **Access pattern analysis**
- **Security incident detection**

## 🤝 Contributing

This system is designed to be:
- **Modular** - easy to add new features
- **Extensible** - supports custom integrations
- **Maintainable** - clean, documented code
- **Secure** - follows security best practices

## 📄 License

This project is provided as-is for educational and professional use. Please ensure compliance with your organization's security policies and applicable regulations.

---

**Note**: This is a demonstration version. For production use, implement proper security measures, user management, and monitoring systems.
