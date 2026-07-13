import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "city": "New Delhi",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "interval_minutes": 30,
    "enable_notifications": True,
    "temp_high_threshold": 35.0,
    "temp_low_threshold": 15.0,
    "rain_alert_enabled": True,
    "wind_alert_enabled": False,
    "wind_threshold_kmh": 40.0
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Ensure all keys from DEFAULT_CONFIG exist (backward compatibility)
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
            return config
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
