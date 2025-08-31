# Lockr Enterprise - Systemd Service Quick Reference

## 🚀 Quick Start

```bash
# Install Lockr as a systemd service
./install_systemd_service.sh

# Or use the management script
./manage_lockr_service.sh install
```

## 📋 Service Management Commands

### Basic Control
```bash
# Start the service
./manage_lockr_service.sh start
# or
sudo systemctl start lockr

# Stop the service
./manage_lockr_service.sh stop
# or
sudo systemctl stop lockr

# Restart the service
./manage_lockr_service.sh restart
# or
sudo systemctl restart lockr
```

### Status and Monitoring
```bash
# Check service status
./manage_lockr_service.sh status
# or
sudo systemctl status lockr

# View service logs (follow mode)
./manage_lockr_service.sh logs
# or
sudo journalctl -u lockr -f

# View last N lines of logs
./manage_lockr_service.sh logs-n 100
# or
sudo journalctl -u lockr -n 100
```

### Boot Configuration
```bash
# Enable service to start on boot
./manage_lockr_service.sh enable
# or
sudo systemctl enable lockr

# Disable service from starting on boot
./manage_lockr_service.sh disable
# or
sudo systemctl disable lockr
```

### Service Information
```bash
# Show comprehensive service information
./manage_lockr_service.sh info

# Check if service is running
sudo systemctl is-active lockr

# Check if service is enabled
sudo systemctl is-enabled lockr
```

## 🔧 Installation and Removal

```bash
# Install the systemd service
./manage_lockr_service.sh install

# Remove the systemd service
./manage_lockr_service.sh uninstall
```

## 📊 Service Details

- **Service Name**: `lockr`
- **Service File**: `/etc/systemd/system/lockr.service`
- **Working Directory**: `/home/brian/Cursor/Password-Manager`
- **User**: `brian`
- **Web Interface**: `http://localhost:5000`
- **Default Login**: `admin` / `admin123`

## 🛡️ Security Features

- **Restricted Access**: Limited file system access
- **Resource Limits**: File descriptors and process limits
- **Service Isolation**: Secure service boundaries
- **Journal Logging**: Centralized log management

## 🚨 Troubleshooting

### Service Won't Start
```bash
# Check service status
sudo systemctl status lockr

# View detailed logs
sudo journalctl -u lockr -n 50

# Check prerequisites
ls -la venv/bin/flask
ls -la enhanced_unified_manager.py
```

### Permission Issues
```bash
# Ensure correct ownership
sudo chown -R brian:brian /home/brian/Cursor/Password-Manager

# Check service file permissions
ls -la /etc/systemd/system/lockr.service
```

### Network Issues
```bash
# Check if port 5000 is in use
sudo netstat -tlnp | grep :5000

# Check firewall settings
sudo ufw status
```

## 📝 Log Locations

- **Systemd Logs**: `sudo journalctl -u lockr`
- **Application Logs**: Check the web interface for action logs
- **Service Logs**: `sudo journalctl -u lockr -f` (follow mode)

## 🔄 Service Lifecycle

1. **Install**: `./manage_lockr_service.sh install`
2. **Enable**: `./manage_lockr_service.sh enable`
3. **Start**: `./manage_lockr_service.sh start`
4. **Monitor**: `./manage_lockr_service.sh status`
5. **Stop**: `./manage_lockr_service.sh stop`
6. **Disable**: `./manage_lockr_service.sh disable`
7. **Uninstall**: `./manage_lockr_service.sh uninstall`

## 💡 Pro Tips

- Use `./manage_lockr_service.sh logs` to monitor the service in real-time
- The service automatically restarts on failure
- Check `./manage_lockr_service.sh info` for comprehensive service details
- Use `sudo systemctl daemon-reload` after manual service file changes
- Monitor resource usage with `sudo systemctl status lockr`

---

**Note**: All commands should be run from the `/home/brian/Cursor/Password-Manager` directory unless specified otherwise.
