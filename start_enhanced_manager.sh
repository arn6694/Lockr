#!/bin/bash

# Lockr - Enterprise Server & Password Management Startup Script
# This script starts the Lockr platform with server management capabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON_FILE="enhanced_unified_manager.py"
REQUIREMENTS_FILE="enhanced_requirements.txt"

echo -e "${BLUE}🔒 Lockr - Enterprise Platform Startup${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed or not in PATH${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo -e "${GREEN}✅ Python 3 found: $(python3 --version)${NC}"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment found${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Check if Flask is installed
if ! python -c "import flask" &> /dev/null; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "$REQUIREMENTS_FILE" ]; then
        pip install -r "$REQUIREMENTS_FILE"
        echo -e "${GREEN}✅ Dependencies installed from requirements.txt${NC}"
    else
        echo -e "${RED}❌ Requirements file not found: $REQUIREMENTS_FILE${NC}"
        echo "Installing basic Flask dependencies..."
        pip install Flask==2.3.3 Werkzeug==2.3.7 Jinja2==3.1.2
        echo -e "${GREEN}✅ Basic Flask dependencies installed${NC}"
    fi
else
    echo -e "${GREEN}✅ Flask already installed${NC}"
fi

# Check if paramiko is installed (required for SSH operations)
if ! python -c "import paramiko" &> /dev/null; then
    echo -e "${YELLOW}📦 Installing SSH dependencies...${NC}"
    pip install paramiko==3.3.1 cryptography==41.0.7 bcrypt==4.0.1 pynacl==1.5.0
    echo -e "${GREEN}✅ SSH dependencies installed${NC}"
fi

# Check if the main Python file exists
if [ ! -f "$PYTHON_FILE" ]; then
    echo -e "${RED}❌ Main application file not found: $PYTHON_FILE${NC}"
    echo "Please ensure the enhanced password manager files are in the current directory"
    exit 1
fi

echo ""
echo -e "${GREEN}🎯 Starting Lockr Enterprise Platform...${NC}"
echo -e "${BLUE}📱 Web Interface: http://localhost:5000${NC}"
echo -e "${BLUE}🔑 Login: admin / admin123${NC}"
echo -e "${YELLOW}⚠️  Press Ctrl+C to stop the server${NC}"
echo ""

# Start the Flask application
python "$PYTHON_FILE"
