import time
import os
import cv2
import numpy as np
from datetime import datetime
import pytz
from config import Settings
import threading

# Try importing Picamera2
try:
    from libcamera import controls
    from picamera2 import Picamera2, Picamera2Config

    PICAMERA_AVAILABLE = True
except ImportError as e:
    print(f"DEBUG: Failed to import Picamera2: {e}")
    PICAMERA_AVAILABLE = False


class WebcamCamera:
    """
    Real Webcam implementation using OpenCV.
    """

    def __init__(self, device_index=0):
        self.cap = cv2.VideoCapture(device_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open webcam (index={device_index})")
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def capture_array(self):
        ret, frame = self.cap.read()
        if not ret:
            # Return black frame on failure to read
            return np.zeros((480, 640, 3), dtype=np.uint8)
        return frame

    def start(self):
        print("Webcam Started")

    def stop(self):
        self.cap.release()
        print("Webcam Stopped")


class CameraApp:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.running = False
        self.recording = False
        self.last_recording_time = 0
        self.last_motion_check = 0
        self.monitoring_enabled = False  # Default to False for manual start
        self.camera_error = None
        self.logs = []

        self.is_picamera = PICAMERA_AVAILABLE
        self.log(f"Initializing CameraApp (PICAMERA_AVAILABLE={PICAMERA_AVAILABLE})")

        if PICAMERA_AVAILABLE:
            try:
                self.log("Attempting to initialize Picamera2...")
                self.camera = Picamera2()
                config = self.camera.create_video_configuration(
                    main={"size": (640, 480), "format": "BGR888"}
                )
                self.camera.configure(config)
                self.camera.start()
                self.log("Picamera2 started successfully")
            except Exception as e:
                self.camera_error = f"Picamera Error: {e}"
                self.log(f"CRITICAL: {e}")
                self.camera = None
                raise RuntimeError(
                    f"Failed to initialize Picamera2: {e}"
                )  # STRICT MODE: Crash if fails
        else:
            # STRICT MODE: Do not fallback to webcam
            self.log("CRITICAL: Picamera2 library not found or import failed.")
            self.camera_error = "Picamera2 Library Missing"
            self.camera = None
            raise RuntimeError("Picamera2 library is not available. Please install it.")

        self.current_frame = None
        self.prev_frame_gray = None

        self.prev_frame_gray = None
        self.captures_dir = "captures"
        if not os.path.exists(self.captures_dir):
            os.makedirs(self.captures_dir)

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        print(entry)
        self.logs.insert(0, entry)  # Prepend for newest first
        # Keep last 100 logs
        if len(self.logs) > 100:
            self.logs = self.logs[:100]

    def get_timestamp(self):
        tz = pytz.timezone(self.settings.get("timezone"))
        return datetime.now(tz).strftime("%Y-%m-%d_%H-%M-%S_%f_EST")

    def detect_motion(self, frame):
        """
        Detects motion in the frame based on grid logic.
        """
        # Resize to low res for grid processing (e.g., matching grid dims or slightly larger)
        # Using 160x120 for processing to have enough pixels per cell
        proc_w, proc_h = 160, 120
        small_frame = cv2.resize(frame, (proc_w, proc_h))

        # Extract Green channel
        green = small_frame[:, :, 1]

        # Blur to reduce noise
        green = cv2.GaussianBlur(green, (21, 21), 0)

        if self.prev_frame_gray is None:
            self.prev_frame_gray = green
            return False

        # Frame Delta
        delta = cv2.absdiff(self.prev_frame_gray, green)
        self.prev_frame_gray = green

        # Threshold
        thresh_val = self.settings.get("motion_threshold")
        _, thresh = cv2.threshold(delta, thresh_val, 255, cv2.THRESH_BINARY)

        # Check active grid zones
        grid_mask = self.settings.get("grid_mask")
        if not grid_mask:
            # If no mask set, assume full screen motion detection logic or ignore?
            # Let's default to full screen if empty, or maybe nothing.
            # Typically user wants to select areas. Let's assume empty = everything for now or nothing.
            # User said "where detection should occur", implying whitelist.
            # If list is empty, let's treat it as "detect everywhere" for start, or strictly "detect nowhere".
            # Let's detect everywhere if empty for better UX out of box.
            pass

        # Grid Analysis
        rows = self.settings.get("grid_rows")
        cols = self.settings.get("grid_cols")
        cell_w = proc_w // cols
        cell_h = proc_h // rows

        motion_detected = False

        # If mask is empty, check global motion
        if not grid_mask:
            if np.sum(thresh) > 100:  # Simple global threshold
                motion_detected = True
        else:
            for cell_idx in grid_mask:
                # Convert 1D index to 2D
                r = cell_idx // cols
                c = cell_idx % cols

                # ROI
                x1 = c * cell_w
                y1 = r * cell_h
                x2 = x1 + cell_w
                y2 = y1 + cell_h

                roi = thresh[y1:y2, x1:x2]
                if np.sum(roi) > 10:  # Sensitivity per cell
                    motion_detected = True
                    break

        return motion_detected

    def capture_image(self, frame):
        filename = f"{self.get_timestamp()}.jpg"
        filepath = os.path.join(self.captures_dir, filename)
        quality = self.settings.get("image_quality")
        # Use OpenCV's IMWRITE_JPEG_QUALITY param (0-100)
        cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        print(f"Captured: {filename} (Quality: {quality})")

    def get_latest_frame(self):
        """Generator that yields MJPEG frames."""
        while True:
            if self.current_frame is not None:
                try:
                    ret, buffer = cv2.imencode(".jpg", self.current_frame)
                    if ret:
                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n"
                            + buffer.tobytes()
                            + b"\r\n"
                        )
                except Exception as e:
                    pass
            time.sleep(0.05)  # 20 FPS cap for stream

    def run(self):
        self.running = True

        print("Camera Monitoring Started")

        recording_start_time = 0

        while self.running:
            # 1. Capture Frame
            if self.camera:
                try:
                    frame = self.camera.capture_array()
                    self.current_frame = frame  # Store for streaming
                except Exception as e:
                    self.log(f"Error capturing frame: {e}")
                    time.sleep(1)  # prevent tight loop on error
                    continue
            else:
                # No camera available (error state)
                # Keep loop running to serve web UI, but wait
                time.sleep(1)
                continue

            # 2. Check Motion (if not already recording)
            if self.monitoring_enabled and not self.recording:
                if self.detect_motion(frame):
                    print("Motion Detected! Starting Time-lapse.")
                    self.recording = True
                    recording_start_time = time.time()
                    # Capture first frame immediately
                    self.capture_image(frame)
                    self.last_recording_time = time.time()

            # 3. Handle Recording State
            if self.recording:
                # Check if duration elapsed
                if time.time() - recording_start_time > self.settings.get(
                    "time_lapse_duration"
                ):
                    print("Time-lapse ended. Returning to surveillance.")
                    self.recording = False
                else:
                    # Check interval
                    if time.time() - self.last_recording_time > self.settings.get(
                        "time_between_snaps"
                    ):
                        self.capture_image(frame)
                        self.last_recording_time = time.time()

            time.sleep(0.1)  # Loop throttling

    def stop(self):
        self.running = False
        if self.camera:
            try:
                self.camera.stop()
                self.log("Camera stopped")
            except Exception as e:
                self.log(f"Error stopping camera: {e}")

    def start_monitoring(self):
        self.monitoring_enabled = True
        print("Monitoring Started")

    def stop_monitoring(self):
        self.monitoring_enabled = False
        self.recording = False  # enhancing safety to stop current recording if any
        print("Monitoring Stopped")
