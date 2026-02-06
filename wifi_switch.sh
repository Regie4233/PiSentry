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

# Set defaults
HOTSPOT_IP=${HOTSPOT_IP:-10.42.0.1}

# Configuration checks
if [ -z "$HOME_SSID" ] || [ -z "$HOME_PASS" ] || [ -z "$HOTSPOT_SSID" ] || [ -z "$HOTSPOT_PASS" ]; then
    echo "Error: Missing configuration variables in .env"
    exit 1
fi

# Function to check current active connection
get_active_connection() {
    sudo nmcli -t -f NAME connection show --active | head -n 1
}

CURRENT_CONNECTION=$(get_active_connection)

enable_hotspot() {
    echo "Enabling Hotspot ($HOTSPOT_SSID)..."
    
    # Check if the connection profile already exists
    if sudo nmcli connection show "$HOTSPOT_SSID" >/dev/null 2>&1; then
        echo "Connection profile '$HOTSPOT_SSID' exists. Bringing it up..."
    else
        echo "Creating new Hotspot connection profile..."
        sudo nmcli connection add type wifi ifname wlan0 con-name "$HOTSPOT_SSID" autoconnect yes ssid "$HOTSPOT_SSID"
        sudo nmcli connection modify "$HOTSPOT_SSID" 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared ipv4.addresses $HOTSPOT_IP/24 wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$HOTSPOT_PASS"
    fi

    # Bring up the connection
    sudo nmcli connection up "$HOTSPOT_SSID"
    
    # Verify
    if [ "$(get_active_connection)" == "$HOTSPOT_SSID" ]; then
        echo "Hotspot active! IP: $HOTSPOT_IP" 
        echo "Connect to SSID: $HOTSPOT_SSID"
    else
        echo "Error: Failed to activate hotspot."
        exit 1
    fi
}

enable_wifi() {
    echo "Connecting to Home Wi-Fi ($HOME_SSID)..."
    
    # Bring down hotspot if active
    sudo nmcli connection down "$HOTSPOT_SSID" >/dev/null 2>&1
    
    # Connect to Home Wi-Fi
    sudo nmcli device wifi connect "$HOME_SSID" password "$HOME_PASS"
}

# Logic
if [ "$1" == "force" ]; then
    enable_hotspot
    exit 0
fi

if [ "$CURRENT_CONNECTION" == "$HOTSPOT_SSID" ]; then
    echo "Currently in Hotspot mode. Switching to Client..."
    enable_wifi
else
    echo "Currently not in Hotspot mode. Switching to Hotspot..."
    enable_hotspot
fi
