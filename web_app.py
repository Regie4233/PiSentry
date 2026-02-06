from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List
import os
import zipfile
import io

app = FastAPI()

# Ensure directories exist
for dir_name in ["static", "captures"]:
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/captures", StaticFiles(directory="captures"), name="captures")

templates = Jinja2Templates(directory="templates")


class ConfigModel(BaseModel):
    motion_threshold: int
    grid_mask: List[int]
    time_lapse_duration: int
    time_between_snaps: float
    timezone: str
    grid_rows: int
    grid_cols: int
    image_quality: int


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/config")
async def get_config(request: Request):
    camera_app = request.app.state.camera_app
    return camera_app.settings.config


@app.post("/api/config")
async def update_config(config: ConfigModel, request: Request):
    camera_app = request.app.state.camera_app
    # Update settings
    for key, value in config.dict().items():
        camera_app.settings.update(key, value)
    return {"status": "success", "config": camera_app.settings.config}


@app.get("/api/status")
async def get_status(request: Request):
    camera_app = request.app.state.camera_app
    return {
        "running": camera_app.running,
        "monitoring_enabled": camera_app.monitoring_enabled,
        "recording": camera_app.recording,
        "mock_mode": not camera_app.is_picamera,
        "camera_error": camera_app.camera_error,
    }


@app.post("/api/start")
async def start_monitoring(request: Request):
    camera_app = request.app.state.camera_app
    camera_app.start_monitoring()
    return {"status": "started"}


@app.post("/api/stop")
async def stop_monitoring(request: Request):
    camera_app = request.app.state.camera_app
    camera_app.stop_monitoring()
    return {"status": "stopped"}


@app.get("/api/logs")
async def get_logs(request: Request):
    camera_app = request.app.state.camera_app
    return {"logs": camera_app.logs}


@app.get("/api/images")
async def list_images():
    images = []
    capture_dir = "captures"
    if os.path.exists(capture_dir):
        files = sorted(os.listdir(capture_dir), reverse=True)
        for f in files:
            if f.endswith(".jpg"):
                images.append({"filename": f, "url": f"/captures/{f}"})
    return images


@app.post("/api/images/delete_all")
async def delete_all_images():
    capture_dir = "captures"
    if os.path.exists(capture_dir):
        for f in os.listdir(capture_dir):
            file_path = os.path.join(capture_dir, f)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
    return {"status": "deleted"}


@app.get("/api/images/download")
async def download_images():
    capture_dir = "captures"
    if not os.path.exists(capture_dir):
        raise HTTPException(status_code=404, detail="No captures found")

    zip_io = io.BytesIO()
    with zipfile.ZipFile(
        zip_io, mode="w", compression=zipfile.ZIP_DEFLATED
    ) as temp_zip:
        for f in os.listdir(capture_dir):
            file_path = os.path.join(capture_dir, f)
            if os.path.isfile(file_path):
                temp_zip.write(file_path, f)

    zip_io.seek(0)
    return StreamingResponse(
        zip_io,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": "attachment; filename=captures.zip"},
    )


@app.get("/video_feed")
async def video_feed(request: Request):
    """Video streaming route. Put this in the src attribute of an img tag."""
    camera_app = request.app.state.camera_app
    return StreamingResponse(
        camera_app.get_latest_frame(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
