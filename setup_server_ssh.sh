#!/bin/bash

# Setup Server SSH Access via Ansible
# This script runs the Ansible playbook to configure SSH access on target servers

set -e

# Default values
TARGET_SERVER_IP="${1:-10.10.10.5}"
TARGET_HOSTNAME="${2:-checkmk}"
PLAYBOOK_DIR="/home/brian/Cursor/Password-Manager/playbooks"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔒 Lockr - SSH Setup via Ansible${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "${YELLOW}Target Server:${NC} ${TARGET_HOSTNAME} (${TARGET_SERVER_IP})"
echo -e "${YELLOW}Central Server:${NC} 10.10.10.96"
echo -e "${YELLOW}Playbook:${NC} ${PLAYBOOK_DIR}/setup_ssh_access.yml"
echo ""

# Check if we're in the right directory
if [ ! -f "${PLAYBOOK_DIR}/setup_ssh_access.yml" ]; then
    echo -e "${RED}❌ Error: Playbook not found at ${PLAYBOOK_DIR}/setup_ssh_access.yml${NC}"
    echo -e "${YELLOW}Please ensure you're running this from the Lockr directory${NC}"
    exit 1
fi

# Check if Ansible is available
if ! command -v ansible-playbook &> /dev/null; then
    echo -e "${RED}❌ Error: ansible-playbook not found${NC}"
    echo -e "${YELLOW}Please install Ansible: sudo apt install ansible${NC}"
    exit 1
fi

# Change to playbook directory
cd "${PLAYBOOK_DIR}"

echo -e "${BLUE}🚀 Executing Ansible playbook...${NC}"
echo ""

# Run the Ansible playbook
ansible-playbook \
    -i inventory_central.yml \
    setup_ssh_access.yml \
    -e "target_server_ip=${TARGET_SERVER_IP}" \
    -e "target_hostname=${TARGET_HOSTNAME}" \
    --verbose

# Check the result
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ SSH setup completed successfully for ${TARGET_HOSTNAME} (${TARGET_SERVER_IP})${NC}"
    echo -e "${BLUE}You can now test SSH access: ssh brian@${TARGET_SERVER_IP}${NC}"
else
    echo ""
    echo -e "${RED}❌ SSH setup failed for ${TARGET_HOSTNAME} (${TARGET_SERVER_IP})${NC}"
    echo -e "${YELLOW}Check the output above for errors and ensure:${NC}"
    echo -e "${YELLOW}1. Central server 10.10.10.96 is accessible${NC}"
    echo -e "${YELLOW}2. brian-install.sh exists on the central server${NC}"
    echo -e "${YELLOW}3. Your SSH key is set up on the central server${NC}"
    exit 1
fi
