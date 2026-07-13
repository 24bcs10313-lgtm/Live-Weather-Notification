import json
import os

# Use absolute path resolution relative to this file so it works in serverless runtimes
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

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
    # Attempt to load from Flask session if inside a request context
    try:
        from flask import session, has_request_context
        if has_request_context() and "config" in session:
            cfg = session["config"]
            # Fill missing keys for backward compatibility
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception:
        pass

    # Fallback to loading local config.json file
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in config:
                        config[k] = v
                return config
        except Exception:
            pass
            
    return DEFAULT_CONFIG.copy()

def save_config(config):
    # Attempt to save to Flask session if inside a request context
    try:
        from flask import session, has_request_context
        if has_request_context():
            session["config"] = config
            session.modified = True
            return True
    except Exception:
        pass

    # Fallback to local config.json (will fail on read-only environments like Vercel, but works locally)
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
