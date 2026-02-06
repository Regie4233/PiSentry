import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")

print("\n--- Checking Picamera2 Import ---")
try:
    import picamera2

    print(f"SUCCESS: picamera2 module found at {picamera2.__file__}")
    from picamera2 import Picamera2

    print("SUCCESS: Picamera2 class imported.")
except ImportError as e:
    print(f"FAILURE: Could not import picamera2. Error: {e}")
    print("\nDIAGNOSIS:")
    print(
        "Likely cause: You are running in a virtual environment that was not created with '--system-site-packages'."
    )
    print(
        "The 'picamera2' library is a system package (apt install python3-picamera2) and is not available on PyPI."
    )
    print("Please delete and recreate your venv:")
    print("  rm -rf .venv")
    print("  python3 -m venv --system-site-packages .venv")
    print("  source .venv/bin/activate")
    print("  pip install -r requirements.txt")

print("\n--- Checking OpenCV ---")
try:
    import cv2

    print(f"SUCCESS: OpenCV imported. Version: {cv2.__version__}")
except ImportError as e:
    print(f"FAILURE: Could not import cv2. Error: {e}")
