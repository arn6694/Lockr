# Password Manager Web Interface

A professional, enterprise-grade web interface for your password management system that makes it easy to retrieve server passwords through a browser.

## Features

### 🎨 **Professional Design**
- Modern, responsive web interface
- Bootstrap 5 with custom styling
- Professional color scheme and animations
- Mobile-friendly design

### 🔐 **Secure Access**
- User authentication system
- Session management
- Audit logging for all password access
- Secure API endpoints

### 📊 **Dashboard Overview**
- Real-time server status monitoring
- Statistics and metrics
- Quick access to common functions
- Visual server status indicators

### 🚀 **Easy Password Retrieval**
- One-click password retrieval for common users
- Modal-based password forms
- Server and username selection
- Instant password display

### 📈 **Advanced Features**
- Password history tracking
- Server access patterns
- User activity monitoring
- Comprehensive logging

## Quick Start

### 1. **Install Dependencies**
```bash
# Make the startup script executable
chmod +x start_web_interface.sh

# Run the startup script
./start_web_interface.sh
```

### 2. **Access the Web Interface**
- Open your browser and go to: `http://localhost:5000`
- Login with: `admin` / `admin123`

### 3. **Start Using**
- View server status on the dashboard
- Click "Retrieve Password" for specific access
- Use quick action buttons for common tasks
- Monitor access history and patterns

## File Structure

```
Password-Manager/
├── web_interface.py          # Main Flask application
├── templates/                # HTML templates
│   ├── login.html           # Login page
│   └── dashboard.html       # Main dashboard
├── start_web_interface.sh   # Startup script
├── requirements.txt          # Python dependencies
└── WEB_INTERFACE_README.md  # This file
```

## Configuration

### **Update Paths**
Edit `web_interface.py` and update these paths to match your system:

```python
VAULT_DIR = "/home/svc_ans/playbooks/files/vault"
VAULT_KEY = "/home/svc_ans/.vault_key"
RETRIEVE_SCRIPT = "/home/svc_ans/playbooks/files/retrieve_password.sh"
```

### **Customize Servers**
Update the `MOCK_SERVERS` list in `web_interface.py` with your actual servers:

```python
MOCK_SERVERS = [
    {"name": "your-server", "ip": "192.168.1.100", "status": "online", "last_access": "2024-08-30 14:30"},
    # Add more servers...
]
```

## Security Features

### **Authentication**
- Session-based authentication
- Secure password handling
- Logout functionality
- Session timeout (configurable)

### **Audit Logging**
- All password access attempts logged
- User activity tracking
- IP address logging
- Success/failure status tracking

### **API Security**
- RESTful API endpoints
- JSON request/response handling
- Error handling and validation
- Rate limiting (can be added)

## Production Deployment

### **For Production Use**
1. **Change Default Credentials**
   - Update the hardcoded `admin/admin123` credentials
   - Implement proper user management system

2. **Add HTTPS**
   - Use a reverse proxy (nginx/Apache)
   - Configure SSL certificates
   - Enable HTTPS-only access

3. **Database Integration**
   - Replace mock data with database storage
   - Implement proper user management
   - Add role-based access control

4. **Monitoring & Logging**
   - Add proper logging to files
   - Implement monitoring and alerting
   - Add health checks

### **Docker Deployment**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "web_interface.py"]
```

## API Endpoints

### **Authentication**
- `POST /login` - User login
- `GET /logout` - User logout

### **Password Management**
- `GET /api/servers` - List all servers
- `POST /api/password` - Retrieve password
- `GET /api/history/<server>` - Get server password history

## Troubleshooting

### **Common Issues**

1. **Port Already in Use**
   ```bash
   # Find process using port 5000
   lsof -i :5000
   # Kill the process
   kill -9 <PID>
   ```

2. **Permission Denied**
   ```bash
   # Make startup script executable
   chmod +x start_web_interface.sh
   ```

3. **Python Dependencies**
   ```bash
   # Install system Python packages
   sudo apt-get install python3-venv python3-pip
   ```

4. **Path Issues**
   - Verify all paths in `web_interface.py` are correct
   - Ensure your `retrieve_password.sh` script is accessible

## Customization

### **Styling**
- Modify CSS variables in `templates/dashboard.html`
- Update color schemes and themes
- Add custom branding and logos

### **Functionality**
- Add new API endpoints
- Implement additional security features
- Add more dashboard widgets
- Integrate with monitoring systems

## Support

This web interface integrates with your existing password management system and provides a professional, easy-to-use interface for your team.

For issues or enhancements:
1. Check the Flask application logs
2. Verify all paths and permissions
3. Test individual components
4. Review the audit logs for access issues

---

**Note**: This is a demonstration version. For production use, implement proper security measures, user management, and monitoring.

