#!/bin/bash
# 3DGS Simulation Asset Optimizer - Environment Setup Script

echo "[1/4] Creating Python virtual environment (venv)..."
python3 -m venv venv

echo "[2/4] Activating virtual environment..."
source venv/bin/activate

echo "[3/4] Upgrading pip..."
pip install --upgrade pip

echo "[4/4] Installing required dependencies..."
pip install -r python_prototype/requirements.txt

echo ""
echo "====================================================="
echo "Setup complete! 🚀"
echo "Please run the following command to activate your env:"
echo "source venv/bin/activate"
echo "====================================================="
