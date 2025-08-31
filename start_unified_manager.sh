#!/bin/bash
# Start Unified Password Manager

echo "Starting Unified Password Manager..."
echo "==================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3 and try again"
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements (only if not already installed)
if ! python -c "import flask" 2>/dev/null; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Start the unified password manager
echo "Starting Unified Password Manager..."
echo "Web interface will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

python unified_password_manager.py
