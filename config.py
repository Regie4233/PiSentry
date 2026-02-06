import json
import os
from typing import List, Dict, Any

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "motion_threshold": 20,
    "grid_mask": [],  # List of active cell indices
    "time_lapse_duration": 10,  # Seconds to record after motion
    "time_between_snaps": 0.5,  # Seconds between frames in time-lapse
    "timezone": "US/Eastern",
    "grid_rows": 12,
    "grid_cols": 16,
    "image_quality": 80,
}


class Settings:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        if not os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "w") as f:
                    json.dump(DEFAULT_CONFIG, f, indent=4)
            except Exception as e:
                print(f"Error creating default config: {e}")
            return DEFAULT_CONFIG.copy()

        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()

    def save_config(self, new_config: Dict[str, Any]):
        self.config.update(new_config)
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str):
        return self.config.get(key, DEFAULT_CONFIG.get(key))

    def update(self, key: str, value: Any):
        self.config[key] = value
        self.save_config(self.config)
