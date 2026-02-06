import threading
import uvicorn
from config import Settings
from camera_app import CameraApp
from web_app import app


def main():
    # Initialize Settings
    settings = Settings()

    # Initialize CameraApp
    camera_app = CameraApp(settings)

    # Store camera_app in FastAPI state
    app.state.camera_app = camera_app

    # Start Camera Thread
    camera_thread = threading.Thread(target=camera_app.run, daemon=True)
    camera_thread.start()

    try:
        # Start Web Server
        # host="0.0.0.0" to be accessible on network
        uvicorn.run(app, host="0.0.0.0", port=8888)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        camera_app.stop()
        camera_thread.join()


if __name__ == "__main__":
    main()
