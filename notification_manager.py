import subprocess
import threading
import time
import datetime
from config import load_config
from weather_service import fetch_weather

def escape_ps_string(s):
    """Escapes single quotes and newlines for safe inclusion in a PowerShell string."""
    return str(s).replace("'", "''").replace("\r", "").replace("\n", " ")

def send_toast(title, message):
    """Triggers a native Windows toast notification using a non-blocking PowerShell script."""
    clean_title = escape_ps_string(title)
    clean_message = escape_ps_string(message)
    
    ps_script = f"""
    [void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms');
    $notification = New-Object System.Windows.Forms.NotifyIcon;
    $notification.Icon = [System.Drawing.SystemIcons]::Information;
    $notification.BalloonTipIcon = 'Info';
    $notification.BalloonTipTitle = '{clean_title}';
    $notification.BalloonTipText = '{clean_message}';
    $notification.Visible = $True;
    $notification.ShowBalloonTip(7000);
    """
    try:
        # Run PowerShell without opening a console window (creationflags=0x08000000 / CREATE_NO_WINDOW)
        # Windows-specific: 0x08000000 prevents a cmd popup window.
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", ps_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=0x08000000
        )
        return True
    except Exception as e:
        print(f"Failed to show notification: {e}")
        return False

class WeatherScheduler:
    def __init__(self, ui_callback=None):
        self.ui_callback = ui_callback # Callback to notify GUI of weather updates
        self.running = False
        self.thread = None
        self.last_run_time = 0
        self.config = load_config()

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print("Background weather monitor started.")

    def stop(self):
        self.running = False
        print("Background weather monitor requested to stop.")

    def update_config(self):
        self.config = load_config()

    def check_now(self):
        """Manually trigger a check and notification."""
        self._check_weather_and_notify(is_manual=True)

    def _run_loop(self):
        # Initial wait of 2 seconds before the first check
        time.sleep(2)
        while self.running:
            self.config = load_config()
            interval_sec = max(60, self.config.get("interval_minutes", 30) * 60)
            now = time.time()
            
            if now - self.last_run_time >= interval_sec:
                self._check_weather_and_notify()
                self.last_run_time = now
            
            # Sleep in small slices (e.g. 2 seconds) to allow rapid thread termination on exit
            for _ in range(30):
                if not self.running:
                    return
                time.sleep(2)

    def _check_weather_and_notify(self, is_manual=False):
        self.config = load_config()
        city = self.config.get("city", "New Delhi")
        lat = self.config.get("latitude")
        lon = self.config.get("longitude")
        enable_notif = self.config.get("enable_notifications", True)
        
        if not lat or not lon:
            return
            
        weather = fetch_weather(lat, lon)
        if not weather:
            if is_manual:
                send_toast("Weather Error", f"Unable to fetch weather data for {city}.")
            return
            
        # Update the UI if a callback is registered
        if self.ui_callback:
            try:
                self.ui_callback(weather)
            except Exception as e:
                print(f"Error in UI update callback: {e}")

        # Send notifications if enabled (or if it's a manual test)
        if enable_notif or is_manual:
            temp = weather.get("temp", 0)
            desc = weather.get("desc", "Clear")
            emoji = weather.get("emoji", "☀️")
            rain_prob = weather.get("rain_prob", 0)
            wind = weather.get("wind_speed", 0)
            
            # Check alerts
            alerts = []
            
            # Temperature Alert
            if temp >= self.config.get("temp_high_threshold", 35.0):
                alerts.append(f"🔥 Extreme Heat: {temp}°C")
            elif temp <= self.config.get("temp_low_threshold", 15.0):
                alerts.append(f"❄️ Cold Weather: {temp}°C")
                
            # Rain Alert
            if self.config.get("rain_alert_enabled", True) and (weather.get("rain", 0) > 0 or weather.get("showers", 0) > 0 or "Rain" in desc or "Drizzle" in desc or "Thunderstorm" in desc):
                alerts.append("🌧️ Rain expected/occurring")
                
            # Wind Alert
            if self.config.get("wind_alert_enabled", False) and wind >= self.config.get("wind_threshold_kmh", 40.0):
                alerts.append(f"💨 High Wind Alert: {wind} km/h")
                
            # Formulate Message
            title = f"{emoji} Weather Update: {city}"
            msg_body = f"Temp: {temp}°C ({desc})\nHumidity: {weather.get('humidity')}% | Wind: {wind} km/h"
            
            if alerts:
                title = f"⚠️ Alert: {city} Weather"
                alert_text = " | ".join(alerts)
                msg_body = f"{alert_text}\nTemp: {temp}°C, {desc} ({emoji})"
            
            send_toast(title, msg_body)
