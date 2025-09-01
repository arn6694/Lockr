#!/bin/bash

# Lockr Enterprise - Service Management Script
# Easy control of the Lockr systemd service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SERVICE_NAME="lockr"

# Function to show usage
show_usage() {
    echo -e "${BLUE}🔒 Lockr Enterprise - Service Management${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${YELLOW}Usage: $0 [command]${NC}"
    echo -e ""
    echo -e "${BLUE}Commands:${NC}"
    echo -e "${GREEN}  start     ${NC}Start the Lockr service"
    echo -e "${GREEN}  stop      ${NC}Stop the Lockr service"
    echo -e "${GREEN}  restart   ${NC}Restart the Lockr service"
    echo -e "${GREEN}  status    ${NC}Show service status"
    echo -e "${GREEN}  logs      ${NC}Show service logs (follow mode)"
    echo -e "${GREEN}  logs-n    ${NC}Show last N lines of logs (default: 50)"
    echo -e "${GREEN}  enable    ${NC}Enable service to start on boot"
    echo -e "${GREEN}  disable   ${NC}Disable service from starting on boot"
    echo -e "${GREEN}  install   ${NC}Install the systemd service"
    echo -e "${GREEN}  uninstall ${NC}Remove the systemd service"
    echo -e "${GREEN}  info      ${NC}Show service information"
    echo -e ""
    echo -e "${BLUE}Examples:${NC}"
    echo -e "${YELLOW}  $0 start${NC}"
    echo -e "${YELLOW}  $0 status${NC}"
    echo -e "${YELLOW}  $0 logs-n 100${NC}"
    echo -e "${YELLOW}  $0 install${NC}"
}

# Function to check if service exists
check_service_exists() {
    if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        echo -e "${RED}❌ Lockr service not found${NC}"
        echo -e "${YELLOW}Run '$0 install' to install the service first${NC}"
        exit 1
    fi
}

# Function to check if running as root for certain commands
check_root() {
    if [[ $EUID -eq 0 ]]; then
        echo -e "${RED}❌ This command should not be run as root${NC}"
        echo -e "${YELLOW}Please run as your user (brian)${NC}"
        exit 1
    fi
}

# Function to show service info
show_service_info() {
    echo -e "${BLUE}🔒 Lockr Enterprise Service Information${NC}"
    echo -e "${BLUE}=========================================${NC}"
    
    if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        echo -e "${GREEN}✅ Service Status:${NC}"
        systemctl status ${SERVICE_NAME} --no-pager -l
        
        echo -e "${BLUE}📊 Service Details:${NC}"
        echo -e "${YELLOW}  Service File:${NC} /etc/systemd/system/${SERVICE_NAME}.service"
        echo -e "${YELLOW}  Working Directory:${NC} $(pwd)"
        echo -e "${YELLOW}  Virtual Environment:${NC} $(pwd)/venv"
        echo -e "${YELLOW}  Python Executable:${NC} $(pwd)/venv/bin/python"
        echo -e "${YELLOW}  Main Script:${NC} $(pwd)/enhanced_unified_manager.py"
        echo -e "${YELLOW}  Web Interface:${NC} http://localhost:5000"
        echo -e "${YELLOW}  Default Login:${NC} admin / admin123"
        
        echo -e "${BLUE}🔧 Management Commands:${NC}"
        echo -e "${YELLOW}  Start:   ${NC}sudo systemctl start ${SERVICE_NAME}"
        echo -e "${YELLOW}  Stop:    ${NC}sudo systemctl stop ${SERVICE_NAME}"
        echo -e "${YELLOW}  Restart: ${NC}sudo systemctl restart ${SERVICE_NAME}"
        echo -e "${YELLOW}  Status:  ${NC}sudo systemctl status ${SERVICE_NAME}"
        echo -e "${YELLOW}  Logs:    ${NC}sudo journalctl -u ${SERVICE_NAME} -f"
    else
        echo -e "${RED}❌ Service not installed${NC}"
        echo -e "${YELLOW}Run '$0 install' to install the service${NC}"
    fi
}

# Main script logic
case "${1:-}" in
    start)
        check_root
        check_service_exists
        echo -e "${BLUE}🚀 Starting Lockr service...${NC}"
        sudo systemctl start ${SERVICE_NAME}
        echo -e "${GREEN}✅ Service started${NC}"
        ;;
    stop)
        check_root
        check_service_exists
        echo -e "${BLUE}🛑 Stopping Lockr service...${NC}"
        sudo systemctl stop ${SERVICE_NAME}
        echo -e "${GREEN}✅ Service stopped${NC}"
        ;;
    restart)
        check_root
        check_service_exists
        echo -e "${BLUE}🔄 Restarting Lockr service...${NC}"
        sudo systemctl restart ${SERVICE_NAME}
        echo -e "${GREEN}✅ Service restarted${NC}"
        ;;
    status)
        check_root
        check_service_exists
        echo -e "${BLUE}📊 Lockr service status:${NC}"
        sudo systemctl status ${SERVICE_NAME} --no-pager -l
        ;;
    logs)
        check_root
        check_service_exists
        echo -e "${BLUE}📝 Showing Lockr service logs (follow mode):${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop following logs${NC}"
        sudo journalctl -u ${SERVICE_NAME} -f
        ;;
    logs-n)
        check_root
        check_service_exists
        LINES=${2:-50}
        echo -e "${BLUE}📝 Showing last ${LINES} lines of Lockr service logs:${NC}"
        sudo journalctl -u ${SERVICE_NAME} -n ${LINES} --no-pager
        ;;
    enable)
        check_root
        check_service_exists
        echo -e "${BLUE}✅ Enabling Lockr service to start on boot...${NC}"
        sudo systemctl enable ${SERVICE_NAME}
        echo -e "${GREEN}✅ Service enabled${NC}"
        ;;
    disable)
        check_root
        check_service_exists
        echo -e "${BLUE}❌ Disabling Lockr service from starting on boot...${NC}"
        sudo systemctl disable ${SERVICE_NAME}
        echo -e "${GREEN}✅ Service disabled${NC}"
        ;;
    install)
        check_root
        echo -e "${BLUE}🔧 Installing Lockr systemd service...${NC}"
        if [[ -f "install_systemd_service.sh" ]]; then
            ./install_systemd_service.sh
        else
            echo -e "${RED}❌ Installation script not found${NC}"
            exit 1
        fi
        ;;
    uninstall)
        check_root
        check_service_exists
        echo -e "${BLUE}🗑️  Uninstalling Lockr systemd service...${NC}"
        sudo systemctl stop ${SERVICE_NAME}
        sudo systemctl disable ${SERVICE_NAME}
        sudo rm -f /etc/systemd/system/${SERVICE_NAME}.service
        sudo systemctl daemon-reload
        echo -e "${GREEN}✅ Service uninstalled${NC}"
        ;;
    info)
        show_service_info
        ;;
    *)
        show_usage
        exit 1
        ;;
esac

