#!/bin/bash

# Load configuration from .env file
ENV_FILE="$(dirname "$0")/.env"
if [ -f "$ENV_FILE" ]; then
    # Load .env variables, ignoring comments
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Configuration checks
if [ -z "$HOME_SSID" ] || [ -z "$HOME_PASS" ] || [ -z "$HOTSPOT_SSID" ] || [ -z "$HOTSPOT_PASS" ]; then
    echo "Error: Missing configuration variables in .env"
    exit 1
fi

# IMPROVED CHECK: Look for the specific profile name in the active connections list
IS_HOTSPOT_ACTIVE=$(nmcli -t -f NAME connection show --active | grep -x "$HOTSPOT_SSID")

# Check for "force" argument
if [ "$1" == "force" ]; then
    if [ "$IS_HOTSPOT_ACTIVE" = "$HOTSPOT_SSID" ]; then
        echo "Hotspot is already active."
    else
        echo "Forcing Hotspot activation..."
        # Clear the device
        sudo nmcli device disconnect wlan0
        # The 'name' flag ensures the PROFILE name matches the SSID for our check above
        sudo nmcli device wifi hotspot ssid "$HOTSPOT_SSID" password "$HOTSPOT_PASS" name "$HOTSPOT_SSID"
        echo "Hotspot is now active. SSH into 10.42.0.1"
    fi
    exit 0
fi

if [ "$IS_HOTSPOT_ACTIVE" = "$HOTSPOT_SSID" ]; then
    echo "Hotspot active. Switching to Home Wi-Fi ($HOME_SSID)..."
    sudo nmcli connection down "$HOTSPOT_SSID"
    # Wait 2 seconds for the radio to clear
    sleep 2
    sudo nmcli device wifi connect "$HOME_SSID" password "$HOME_PASS"
else
    echo "Switching from Home Wi-Fi to Hotspot ($HOTSPOT_SSID)..."
    # Clear the device
    sudo nmcli device disconnect wlan0
    # The 'name' flag ensures the PROFILE name matches the SSID for our check above
    sudo nmcli device wifi hotspot ssid "$HOTSPOT_SSID" password "$HOTSPOT_PASS" name "$HOTSPOT_SSID"
    echo "Hotspot is now active. SSH into 10.42.0.1"
fi
