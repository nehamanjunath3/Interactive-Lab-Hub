#!/bin/bash
# One-time setup script for the Voice AI Assistant
# Run on the Raspberry Pi: bash setup.sh

set -e

echo "=== Installing system packages ==="
sudo apt update
sudo apt install -y \
    python3-pip \
    python3-venv \
    portaudio19-dev \
    espeak-ng \
    ffmpeg \
    i2c-tools

echo ""
echo "=== Enabling I2C (if not already on) ==="
sudo raspi-config nonint do_i2c 0

echo ""
echo "=== Creating Python virtual environment ==="
python3 -m venv venv
source venv/bin/activate

echo ""
echo "=== Installing Python packages ==="
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=== Scanning I2C bus (confirm your devices show up) ==="
i2cdetect -y 1

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Before running, set your Anthropic API key:"
echo "  export ANTHROPIC_API_KEY='sk-ant-...'"
echo ""
echo "IMPORTANT — I2C address for the two Qwiic buttons:"
echo "  Both buttons default to 0x6F. You must change the GREEN button's"
echo "  address to 0x5F before they can be used together."
echo "  Do this in Arduino IDE or via the SparkFun button address change"
echo "  example sketch, OR connect them one at a time."
echo ""
echo "To run:"
echo "  source venv/bin/activate"
echo "  python assistant.py"
