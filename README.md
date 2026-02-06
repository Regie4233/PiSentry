# PiSentry Camera App

A Raspberry Pi-based security camera application that detects motion and captures time-lapse sequences. It features a web interface for configuration, live monitoring, and viewing captured images.

## Features
- **Live Video Feed**: Stream real-time video from the camera.
- **Motion Detection**: Detects motion in specific grid zones.
- **Time-Lapse Recording**: Automatically captures a sequence of images when motion is detected.
- **Configurable Settings**: Adjust motion sensitivity, time-lapse duration, and capture intervals via the web UI.
- **Hotspot Mode**: Can create a Wi-Fi hotspot for easy access in the field.
- **Image Compression**: Adjustable JPEG quality settings to optimize storage usage and transfer speeds.
- **Auto-Start**: Service configuration for automatic startup on boot.

## Installation

### Prerequisites
- Raspberry Pi (Zero 2 W recommended)
- Python 3.9+
- `libcamera` installed and configured on the Pi

### System Dependencies
Install system requirements for OpenCV and camera interaction:
```bash
sudo apt update
sudo apt install -y python3-opencv python3-numpy libcamera-tools
```

### Application Setup
1. **Clone the repository**:
   ```bash
   git clone <repository-url> PiSentry
   cd PiSentry
   ```

2. **Create a Virtual Environment**:
   ```bash
   python3 -m venv --system-site-packages .venv
   source .venv/bin/activate
   ```

3. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: On Raspberry Pi, you might need to uncomment `picamera2` in `requirements.txt` or install it via system packages if using a system-site-packages venv.*

4. **Environment Configuration**:
   Copy the example environment file and configure your Wi-Fi credentials:
   ```bash
   cp .env.example .env
   nano .env
   ```
   Edit the `.env` file with your SSID and passwords.

## Usage

### Running Locally
To start the application manually:
```bash
python main.py
```
Access the web interface at `http://<raspberry-pi-ip>:8888`.

### Auto-Start Service
To enable the application to run automatically on boot (creating a hotspot if needed):

1. **Install the Service**:
   ```bash
   sudo cp pisentry.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable pisentry.service
   ```

2. **Start the Service**:
   ```bash
   sudo systemctl start pisentry.service
   ```

## How It Works

### Architecture
The application consists of three main components running concurrently:

1.  **Web Server (`web_app.py`)**: A FastAPI application that serves the frontend (`index.html`) and provides API endpoints for configuration and image management.
2.  **Camera Engine (`camera_app.py`)**: Runs in a separate thread. It captures frames from the camera (using `Picamera2` on Pi or OpenCV Webcam on PC), processes them for motion detection, and manages recording states.
3.  **Main Loop (`main.py`)**: Initializes the components and starts the threading model.

### Motion Detection & Recording
1.  **Frame Capture**: The system captures frames in a loop.
2.  **Preprocessing**: Frames are resized and converted to grayscale/green channel to reduce processing load.
3.  **Delta Calculation**: The current frame is compared to the previous frame to calculate the difference (delta).
4.  **Thresholding**: If the delta exceeds the localized threshold in the selected grid zones, motion is flagged.
5.  **Trigger**: Upon motion detection, the system enters "Recording Mode":
    - Captures an initial burst image.
    - Continues capturing images at the configured `time_between_snaps` interval.
    - Stops recording after the `time_lapse_duration` expires and returns to monitoring.

### Network Switching (`wifi_switch.sh`)
On startup, the system uses this script to check for a known Home Wi-Fi network. If unavailable (or if forced via the startup script), it switches the Raspberry Pi's Wi-Fi interface to Hotspot mode, allowing you to connect directly to the Pi's network to view the camera.

## Debugging & Inspection

If you encounter issues with the camera or dependencies, several utility scripts are provided to help diagnose the problem:

### `debug_camera.py`
**Purpose:** Verifies that the Python environment is set up correctly and that critical libraries are finding their system dependencies.
**Usage:**
```bash
python debug_camera.py
```
**Checks:**
- Python version and executable path.
- Imports `picamera2` and reports success or failure (common issue with venv).
- Imports `cv2` (OpenCV) and reports version.

### `inspect_api.py`
**Purpose:** Inspects the available methods in the `Picamera2` library. This is useful if you suspect a version mismatch or API change (e.g., between Bullseye and Bookworm OS versions).
**Usage:**
```bash
python inspect_api.py
```
**Output:** Lists available methods on the `Picamera2` class and instance, specifically looking for configuration methods.

### `inspect_pkg.py`
**Purpose:** detailed inspection of installed packages and import paths related to the camera.
**Usage:**
```bash
python inspect_pkg.py
```
**Checks:**
- Lists all installed packages matching "picamera".
- Attempts to import `picam2` and `picamera2` and reports results.
