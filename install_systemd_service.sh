#!/bin/bash

# Lockr Enterprise - Systemd Service Installation Script
# This script installs Lockr as a systemd service for automatic startup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="lockr"
SERVICE_FILE="lockr.service"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_PATH="/etc/systemd/system/${SERVICE_FILE}"

echo -e "${BLUE}🔒 Lockr Enterprise - Systemd Service Installation${NC}"
echo -e "${BLUE}==================================================${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ This script should not be run as root${NC}"
   echo -e "${YELLOW}Please run as your user (brian) and use sudo when prompted${NC}"
   exit 1
fi

# Check if we're in the right directory
if [[ ! -f "enhanced_unified_manager.py" ]]; then
    echo -e "${RED}❌ Please run this script from the Password-Manager directory${NC}"
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo -e "${YELLOW}Please run './start_enhanced_manager.sh' first to create the venv${NC}"
    exit 1
fi

# Check if Python dependencies are installed
if [[ ! -f "venv/bin/flask" ]]; then
    echo -e "${RED}❌ Flask not found in virtual environment${NC}"
    echo -e "${YELLOW}Please run './start_enhanced_manager.sh' first to install dependencies${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Stop existing service if running
echo -e "${BLUE}🛑 Stopping existing Lockr service...${NC}"
sudo systemctl stop ${SERVICE_NAME} 2>/dev/null || true
sudo systemctl disable ${SERVICE_NAME} 2>/dev/null || true

# Copy service file to systemd directory
echo -e "${BLUE}📁 Installing systemd service file...${NC}"
sudo cp "${SERVICE_FILE}" "${SERVICE_PATH}"

# Update service file paths to use absolute paths
echo -e "${BLUE}🔧 Updating service file paths...${NC}"
sudo sed -i "s|WorkingDirectory=.*|WorkingDirectory=${CURRENT_DIR}|g" "${SERVICE_PATH}"
sudo sed -i "s|Environment=PATH=.*|Environment=PATH=${CURRENT_DIR}/venv/bin|g" "${SERVICE_PATH}"
sudo sed -i "s|ExecStart=.*|ExecStart=${CURRENT_DIR}/venv/bin/python ${CURRENT_DIR}/enhanced_unified_manager.py|g" "${SERVICE_PATH}"

# Reload systemd daemon
echo -e "${BLUE}🔄 Reloading systemd daemon...${NC}"
sudo systemctl daemon-reload

# Enable and start the service
echo -e "${BLUE}🚀 Enabling and starting Lockr service...${NC}"
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl start ${SERVICE_NAME}

# Wait a moment for service to start
sleep 3

# Check service status
echo -e "${BLUE}📊 Checking service status...${NC}"
if sudo systemctl is-active --quiet ${SERVICE_NAME}; then
    echo -e "${GREEN}✅ Lockr service is running successfully!${NC}"
    echo -e "${BLUE}🌐 Web Interface: http://localhost:5000${NC}"
    echo -e "${BLUE}🔑 Login: admin / admin123${NC}"
else
    echo -e "${RED}❌ Service failed to start${NC}"
    echo -e "${YELLOW}Checking service logs...${NC}"
    sudo journalctl -u ${SERVICE_NAME} -n 20 --no-pager
    exit 1
fi

echo -e "${GREEN}🎉 Lockr Enterprise is now installed as a systemd service!${NC}"
echo -e "${BLUE}📋 Service Management Commands:${NC}"
echo -e "${YELLOW}  Start:   sudo systemctl start lockr${NC}"
echo -e "${YELLOW}  Stop:    sudo systemctl stop lockr${NC}"
echo -e "${YELLOW}  Restart: sudo systemctl restart lockr${NC}"
echo -e "${YELLOW}  Status:  sudo systemctl status lockr${NC}"
echo -e "${YELLOW}  Logs:    sudo journalctl -u lockr -f${NC}"
echo -e "${YELLOW}  Enable:  sudo systemctl enable lockr${NC}"
echo -e "${YELLOW}  Disable: sudo systemctl disable lockr${NC}"

echo -e "${BLUE}🚀 The service will automatically start on boot!${NC}"
