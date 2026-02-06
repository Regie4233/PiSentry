#!/bin/bash

# Ensure script is not run as root (we need the actual user for the service file)
if [ "$EUID" -eq 0 ]; then
  echo "Please run this script as your normal user (not root/sudo)."
  exit 1
fi

# Get the absolute path of the current directory
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CURRENT_USER=$(whoami)

echo "Installing PiSentry..."
echo "  Directory: $APP_DIR"
echo "  User:      $CURRENT_USER"

# Generate Service File Content
SERVICE_CONTENT="[Unit]
Description=PiSentry Camera App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=/bin/bash $APP_DIR/startup.sh
Restart=on-failure
RestartSec=5
StandardOutput=append:$APP_DIR/service.log
StandardError=append:$APP_DIR/service_error.log

[Install]
WantedBy=multi-user.target"

echo ""
echo "--- Generated Service File Content ---"
echo "$SERVICE_CONTENT"
echo "--------------------------------------"
echo ""

read -p "Do you want to install this service to /etc/systemd/system/pisentry.service? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation aborted."
    exit 1
fi

echo "Installing service..."

# Write to a temp file first
echo "$SERVICE_CONTENT" > pisentry.service.tmp

# Move with sudo
sudo mv pisentry.service.tmp /etc/systemd/system/pisentry.service
sudo chown root:root /etc/systemd/system/pisentry.service
sudo chmod 644 /etc/systemd/system/pisentry.service

echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Enabling service..."
sudo systemctl enable pisentry.service

echo ""
echo "WARNING: Starting the service now will switch to Hotspot mode (10.42.0.1) and DISCONNECT your current Wi-Fi/SSH session."
read -p "Do you want to start the service now? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting service..."
    sudo systemctl start pisentry.service
else
    echo "Service installed and enabled. logic."
    echo "Reboot or run 'sudo systemctl start pisentry' to begin."
fi

echo "Installation Complete!"
echo "Check status with: sudo systemctl status pisentry.service"
