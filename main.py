from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import datetime

from config import load_config, save_config
from weather_service import geocode_city, fetch_weather

app = Flask(__name__)
# Secure secret key for session cookie encryption. Falls back to static string for serverless deploy compatibility.
app.secret_key = os.environ.get("SECRET_KEY", "weather_notification_secret_key_2026")

@app.route("/", methods=["GET"])
def index():
    # 1. Load active user settings (automatically loaded from session cookie or defaults)
    config = load_config()
    
    # 2. Handle geocoding city search query
    search_query = request.args.get("search_query", "").strip()
    search_results = None
    if search_query:
        search_results = geocode_city(search_query)
        
    # 3. Retrieve weather details for the current active city coordinates
    city = config.get("city", "New Delhi")
    lat = config.get("latitude", 28.6139)
    lon = config.get("longitude", 77.2090)
    
    weather = fetch_weather(lat, lon)
    
    # 4. Generate notification warning alerts based on active thresholds
    alerts = []
    if weather and config.get("enable_notifications", True):
        temp = weather.get("temp", 0)
        desc = weather.get("desc", "Clear")
        wind = weather.get("wind_speed", 0)
        
        # High Temp Warning
        high_thresh = config.get("temp_high_threshold", 35.0)
        if temp >= high_thresh:
            alerts.append(f"Extreme Heat Alert: Temperature in {city} is {temp}°C (Exceeds threshold of {high_thresh}°C)")
            
        # Low Temp Warning
        low_thresh = config.get("temp_low_threshold", 15.0)
        if temp <= low_thresh:
            alerts.append(f"Cold Weather Alert: Temperature in {city} is {temp}°C (Below threshold of {low_thresh}°C)")
            
        # Rain Warning
        if config.get("rain_alert_enabled", True):
            has_precipitation = (
                weather.get("precipitation", 0) > 0 or 
                weather.get("rain", 0) > 0 or 
                weather.get("showers", 0) > 0 or 
                weather.get("snowfall", 0) > 0 or
                any(keyword in desc for keyword in ["Rain", "Drizzle", "Storm", "Thunderstorm", "Snow"])
            )
            if has_precipitation:
                alerts.append(f"Precipitation Warning: Rain, snow, or storms are occurring or imminent in {city} ({desc})")
                
        # High Wind Warning
        if config.get("wind_alert_enabled", False):
            wind_thresh = config.get("wind_threshold_kmh", 40.0)
            if wind >= wind_thresh:
                alerts.append(f"High Wind Warning: Wind speed is {wind} km/h (Exceeds threshold of {wind_thresh} km/h)")

    # Current timestamp for update indicator
    last_updated = datetime.datetime.now().strftime("%I:%M %p")
    
    return render_template(
        "index.html",
        city=city,
        weather=weather,
        alerts=alerts,
        search_query=search_query,
        search_results=search_results,
        last_updated=last_updated
    )

@app.route("/select", methods=["POST"])
def select():
    # Retrieve details from geocode select list
    name = request.form.get("name")
    lat_str = request.form.get("lat")
    lon_str = request.form.get("lon")
    
    if name and lat_str and lon_str:
        config = load_config()
        config["city"] = name
        config["latitude"] = float(lat_str)
        config["longitude"] = float(lon_str)
        save_config(config)
        flash(f"Successfully changed location to {name}!")
        
    return redirect(url_for("index"))

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        config = load_config()
        
        # Checkboxes: only submitted if checked (value="y" or similar)
        config["enable_notifications"] = "enable_notifications" in request.form
        config["rain_alert_enabled"] = "rain_alert_enabled" in request.form
        config["wind_alert_enabled"] = "wind_alert_enabled" in request.form
        
        try:
            config["interval_minutes"] = int(request.form.get("interval_minutes", 30))
            config["temp_high_threshold"] = float(request.form.get("temp_high_threshold", 35.0))
            config["temp_low_threshold"] = float(request.form.get("temp_low_threshold", 15.0))
            config["wind_threshold_kmh"] = float(request.form.get("wind_threshold_kmh", 40.0))
            
            save_config(config)
            flash("Preferences saved successfully!")
        except ValueError:
            flash("Error saving: Threshold values must be numbers.")
            
        return redirect(url_for("settings"))
        
    # GET method: Load settings page
    config = load_config()
    return render_template("settings.html", config=config)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
