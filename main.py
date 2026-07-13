<<<<<<< HEAD
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
=======
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import threading
import time

from config import load_config, save_config
from weather_service import geocode_city, fetch_weather, get_weather_desc
from notification_manager import WeatherScheduler, send_toast

# Color Palette (Dark Theme / Slate)
COLOR_BG = "#13141f"        # Deep slate/black background
COLOR_CARD = "#1b1c2b"      # Card background
COLOR_ACCENT = "#5d5fef"    # Purple/blue accent
COLOR_ACCENT_HOVER = "#4a4cc7"
COLOR_TEXT_PRIMARY = "#ffffff"
COLOR_TEXT_SECONDARY = "#888aa4"
COLOR_BORDER = "#25263b"
COLOR_ALERT = "#f38ba8"     # Red for warnings

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Live Weather Notification")
        self.root.geometry("500x620")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)
        
        # Center the window on start
        self.center_window(self.root, 500, 620)
        
        # Initialize configurations
        self.config = load_config()
        self.current_weather = None
        self.widget_window = None
        
        # Setup UI styles
        self.setup_styles()
        
        # Main Navigation and Content Frames
        self.create_navigation()
        self.create_pages()
        
        # Initialize and start Background Scheduler
        self.scheduler = WeatherScheduler(ui_callback=self.on_weather_update_callback)
        self.scheduler.start()
        
        # Perform initial weather fetch
        self.refresh_weather()
        
        # Show default dashboard page
        self.show_page("dashboard")
        
        # Bind Close window button
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def center_window(self, win, w, h):
        win.update_idletasks()
        ws = win.winfo_screenwidth()
        hs = win.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        win.geometry(f"{w}x{h}+{int(x)}+{int(y)}")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        
        # Configure Ttk Scrollbar
        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background=COLOR_CARD,
            troughcolor=COLOR_BG,
            bordercolor=COLOR_BORDER,
            lightcolor=COLOR_BORDER,
            darkcolor=COLOR_BORDER,
            arrowsize=10
        )
        style.layout("Vertical.TScrollbar", [
            ('vertical.Scrollbar.trough', {
                'children': [('vertical.Scrollbar.thumb', {'expand': '1'})],
                'sticky': 'ns'
            })
        ])

    def create_navigation(self):
        # Top Navigation Bar
        nav_frame = tk.Frame(self.root, bg=COLOR_CARD, height=60, bd=0, highlightthickness=0)
        nav_frame.pack(side="top", fill="x")
        nav_frame.pack_propagate(False)
        
        # Title Label
        title_label = tk.Label(
            nav_frame, 
            text="🌦️ Live Weather", 
            font=("Segoe UI Semibold", 14), 
            bg=COLOR_CARD, 
            fg=COLOR_TEXT_PRIMARY
        )
        title_label.pack(side="left", padx=20, pady=15)
        
        # Navigation Buttons Frame
        btn_frame = tk.Frame(nav_frame, bg=COLOR_CARD)
        btn_frame.pack(side="right", padx=10, pady=10)
        
        # Dashboard Tab Button
        self.btn_dash = tk.Button(btn_frame, text="Dashboard", font=("Segoe UI Semibold", 9), command=lambda: self.show_page("dashboard"))
        self.make_button_modern(self.btn_dash, COLOR_ACCENT, COLOR_ACCENT_HOVER)
        self.btn_dash.pack(side="left", padx=5)
        
        # Search Tab Button
        self.btn_search = tk.Button(btn_frame, text="Search City", font=("Segoe UI Semibold", 9), command=lambda: self.show_page("search"))
        self.make_button_modern(self.btn_search, COLOR_BORDER, COLOR_CARD)
        self.btn_search.pack(side="left", padx=5)
        
        # Settings Tab Button
        self.btn_settings = tk.Button(btn_frame, text="Settings", font=("Segoe UI Semibold", 9), command=lambda: self.show_page("settings"))
        self.make_button_modern(self.btn_settings, COLOR_BORDER, COLOR_CARD)
        self.btn_settings.pack(side="left", padx=5)

    def make_button_modern(self, btn, normal_bg, hover_bg, normal_fg=COLOR_TEXT_PRIMARY, hover_fg=COLOR_TEXT_PRIMARY):
        btn.config(
            bg=normal_bg,
            fg=normal_fg,
            activebackground=hover_bg,
            activeforeground=hover_fg,
            relief='flat',
            borderwidth=0,
            padx=12,
            pady=5,
            cursor='hand2'
        )
        def on_enter(e):
            if btn['bg'] != COLOR_ACCENT:  # Only change if not the active highlighted button
                btn.config(bg=hover_bg)
        def on_leave(e):
            if btn['bg'] != COLOR_ACCENT:
                btn.config(bg=normal_bg)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def set_active_tab(self, page_name):
        # Reset navigation button colors
        for btn in [self.btn_dash, self.btn_search, self.btn_settings]:
            btn.config(bg=COLOR_BORDER)
            
        if page_name == "dashboard":
            self.btn_dash.config(bg=COLOR_ACCENT)
        elif page_name == "search":
            self.btn_search.config(bg=COLOR_ACCENT)
        elif page_name == "settings":
            self.btn_settings.config(bg=COLOR_ACCENT)

    def create_pages(self):
        # Main content area
        self.content_container = tk.Frame(self.root, bg=COLOR_BG)
        self.content_container.pack(fill="both", expand=True)
        
        # 1. Dashboard Page
        self.page_dashboard = tk.Frame(self.content_container, bg=COLOR_BG)
        self.create_dashboard_page()
        
        # 2. Search Page
        self.page_search = tk.Frame(self.content_container, bg=COLOR_BG)
        self.create_search_page()
        
        # 3. Settings Page
        self.page_settings = tk.Frame(self.content_container, bg=COLOR_BG)
        self.create_settings_page()

    def show_page(self, page_name):
        self.set_active_tab(page_name)
        
        # Forget all pages
        self.page_dashboard.pack_forget()
        self.page_search.pack_forget()
        self.page_settings.pack_forget()
        
        # Show selected page
        if page_name == "dashboard":
            self.page_dashboard.pack(fill="both", expand=True, padx=20, pady=20)
            self.refresh_weather()
        elif page_name == "search":
            self.page_search.pack(fill="both", expand=True, padx=20, pady=20)
        elif page_name == "settings":
            self.page_settings.pack(fill="both", expand=True, padx=20, pady=20)
            self.load_settings_values()

    # ==================== PAGE: DASHBOARD ====================
    def create_dashboard_page(self):
        # Dashboard Canvas to draw the beautiful weather card
        self.dash_canvas = tk.Canvas(self.page_dashboard, bg=COLOR_BG, bd=0, highlightthickness=0, height=270)
        self.dash_canvas.pack(fill="x", pady=(0, 15))
        
        self.draw_card_background()
        
        # Secondary controls frame below card
        controls_frame = tk.Frame(self.page_dashboard, bg=COLOR_BG)
        controls_frame.pack(fill="x", pady=10)
        
        # Refresh Button
        btn_refresh = tk.Button(
            controls_frame, 
            text="🔄 Refresh Weather", 
            font=("Segoe UI Semibold", 10), 
            command=self.refresh_weather
        )
        self.make_button_modern(btn_refresh, COLOR_CARD, COLOR_BORDER)
        btn_refresh.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Background Run Button
        btn_bg = tk.Button(
            controls_frame, 
            text="📥 Run in Background", 
            font=("Segoe UI Semibold", 10), 
            command=self.run_in_background
        )
        self.make_button_modern(btn_bg, COLOR_ACCENT, COLOR_ACCENT_HOVER)
        btn_bg.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # Current Location Banner
        self.location_banner = tk.Frame(self.page_dashboard, bg=COLOR_CARD, bd=1, relief="solid", highlightbackground=COLOR_BORDER)
        # Note: we will configure frame borders later
        self.location_banner.config(highlightcolor=COLOR_BORDER, highlightthickness=1)
        self.location_banner.pack(fill="x", pady=(10, 0))
        
        lbl_loc_title = tk.Label(
            self.location_banner,
            text="📌 Monitored Location",
            font=("Segoe UI", 9),
            bg=COLOR_CARD,
            fg=COLOR_TEXT_SECONDARY
        )
        lbl_loc_title.pack(anchor="w", padx=15, pady=(8, 2))
        
        self.lbl_loc_val = tk.Label(
            self.location_banner,
            text="New Delhi, India",
            font=("Segoe UI Semibold", 12),
            bg=COLOR_CARD,
            fg=COLOR_TEXT_PRIMARY
        )
        self.lbl_loc_val.pack(anchor="w", padx=15, pady=(0, 8))

    def draw_card_background(self):
        self.dash_canvas.delete("all")
        
        # Draw rounded rectangle for the main card (width: 460, height: 260)
        # Canvas dimensions are automatically handled
        self.draw_rounded_rect(self.dash_canvas, 5, 5, 455, 255, 18, fill=COLOR_CARD, outline=COLOR_BORDER, width=1)
        
        # Draw placeholder text when loading
        if self.current_weather is None:
            self.dash_canvas.create_text(
                230, 130, 
                text="Loading live weather data...", 
                font=("Segoe UI Semibold", 12), 
                fill=COLOR_TEXT_SECONDARY,
                tags="loader"
            )
        else:
            w = self.current_weather
            city = self.config.get("city", "New Delhi")
            temp = w.get("temp", "--")
            desc = w.get("desc", "N/A")
            emoji = w.get("emoji", "🌡️")
            feels = w.get("temp_feels", "--")
            hum = w.get("humidity", "--")
            wind = w.get("wind_speed", "--")
            rain_prob = w.get("rain_prob", 0)
            
            # Weather Icon Emoji
            self.dash_canvas.create_text(
                70, 75,
                text=emoji,
                font=("Segoe UI", 70),
                tags="weather_ui"
            )
            
            # City Label
            self.dash_canvas.create_text(
                150, 50,
                text=city,
                font=("Segoe UI Semibold", 18),
                fill=COLOR_TEXT_PRIMARY,
                anchor="w",
                tags="weather_ui"
            )
            
            # Temperature
            self.dash_canvas.create_text(
                150, 105,
                text=f"{temp}°C",
                font=("Segoe UI Variable", 42, "bold"),
                fill=COLOR_TEXT_PRIMARY,
                anchor="w",
                tags="weather_ui"
            )
            
            # Weather Condition Description
            self.dash_canvas.create_text(
                150, 150,
                text=desc,
                font=("Segoe UI", 12),
                fill=COLOR_TEXT_SECONDARY,
                anchor="w",
                tags="weather_ui"
            )
            
            # Horizontal Separator line
            self.dash_canvas.create_line(
                30, 180, 430, 180,
                fill=COLOR_BORDER,
                tags="weather_ui"
            )
            
            # Grid columns for extra details
            # Col 1: Feels Like
            self.dash_canvas.create_text(60, 200, text="Feels Like", font=("Segoe UI", 9), fill=COLOR_TEXT_SECONDARY, tags="weather_ui")
            self.dash_canvas.create_text(60, 225, text=f"{feels}°C", font=("Segoe UI Semibold", 11), fill=COLOR_TEXT_PRIMARY, tags="weather_ui")
            
            # Col 2: Humidity
            self.dash_canvas.create_text(170, 200, text="Humidity", font=("Segoe UI", 9), fill=COLOR_TEXT_SECONDARY, tags="weather_ui")
            self.dash_canvas.create_text(170, 225, text=f"{hum}%", font=("Segoe UI Semibold", 11), fill=COLOR_TEXT_PRIMARY, tags="weather_ui")
            
            # Col 3: Wind
            self.dash_canvas.create_text(280, 200, text="Wind Speed", font=("Segoe UI", 9), fill=COLOR_TEXT_SECONDARY, tags="weather_ui")
            self.dash_canvas.create_text(280, 225, text=f"{wind} km/h", font=("Segoe UI Semibold", 11), fill=COLOR_TEXT_PRIMARY, tags="weather_ui")
            
            # Col 4: Rain Prob
            self.dash_canvas.create_text(390, 200, text="Rain Prob", font=("Segoe UI", 9), fill=COLOR_TEXT_SECONDARY, tags="weather_ui")
            self.dash_canvas.create_text(390, 225, text=f"{rain_prob}%", font=("Segoe UI Semibold", 11), fill=COLOR_TEXT_PRIMARY, tags="weather_ui")

    def draw_rounded_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x1+r, y1,
            x2-r, y1, x2-r, y1,
            x2, y1,
            x2, y1+r, x2, y1+r,
            x2, y2-r, x2, y2-r,
            x2, y2,
            x2-r, y2, x2-r, y2,
            x1+r, y2, x1+r, y2,
            x1, y2,
            x1, y2-r, x1, y2-r,
            x1, y1+r, x1, y1+r,
            x1, y1
        ]
        return canvas.create_polygon(points, **kwargs, smooth=True)

    def refresh_weather(self):
        # Disable window interaction slightly, draw loading text
        self.dash_canvas.delete("weather_ui")
        self.dash_canvas.create_text(
            230, 130, 
            text="Fetching live weather details...", 
            font=("Segoe UI Semibold", 12), 
            fill=COLOR_TEXT_SECONDARY,
            tags="loader"
        )
        self.lbl_loc_val.config(text=f"{self.config.get('city')}, Loading...")
        
        # Call fetch in a non-blocking thread
        def work():
            lat = self.config.get("latitude")
            lon = self.config.get("longitude")
            w = fetch_weather(lat, lon)
            
            # Safely pass to GUI Thread
            self.root.after(0, self.on_initial_fetch_complete, w)
            
        threading.Thread(target=work, daemon=True).start()

    def on_initial_fetch_complete(self, weather_data):
        self.dash_canvas.delete("loader")
        if weather_data:
            self.current_weather = weather_data
            self.lbl_loc_val.config(text=f"{self.config.get('city')}")
        else:
            self.lbl_loc_val.config(text=f"{self.config.get('city')} (Offline)")
            messagebox.showerror("Error", "Could not fetch weather data. Please check your internet connection.")
        self.draw_card_background()

    def on_weather_update_callback(self, weather_data):
        # Triggered by background scheduler thread
        def update():
            self.current_weather = weather_data
            self.draw_card_background()
            
            # If the desktop widget is active, update it
            if self.widget_window and self.widget_window.winfo_exists():
                self.update_widget_ui()
                
        self.root.after(0, update)

    # ==================== PAGE: SEARCH ====================
    def create_search_page(self):
        # Title
        lbl_title = tk.Label(
            self.page_search, 
            text="🔍 Search and Change Location", 
            font=("Segoe UI Semibold", 12), 
            bg=COLOR_BG, 
            fg=COLOR_TEXT_PRIMARY
        )
        lbl_title.pack(anchor="w", pady=(0, 10))
        
        # Search Entry & Go Frame
        entry_frame = tk.Frame(self.page_search, bg=COLOR_BG)
        entry_frame.pack(fill="x", pady=5)
        
        self.entry_city = tk.Entry(
            entry_frame,
            font=("Segoe UI", 11),
            bg=COLOR_CARD,
            fg=COLOR_TEXT_PRIMARY,
            insertbackground=COLOR_TEXT_PRIMARY,
            bd=1,
            relief="solid",
            highlightthickness=0
        )
        self.entry_city.pack(side="left", fill="both", expand=True, ipady=4, padx=(0, 10))
        self.entry_city.bind("<Return>", lambda event: self.perform_search())
        
        btn_go = tk.Button(
            entry_frame,
            text="Search",
            font=("Segoe UI Semibold", 10),
            command=self.perform_search
        )
        self.make_button_modern(btn_go, COLOR_ACCENT, COLOR_ACCENT_HOVER)
        btn_go.pack(side="right", fill="y", ipadx=10)
        
        # Search Results Scrollable Frame
        self.results_container = tk.Frame(self.page_search, bg=COLOR_BG)
        self.results_container.pack(fill="both", expand=True, pady=15)
        
        lbl_tip = tk.Label(
            self.results_container,
            text="Type a city name above (e.g. London, Mumbai, New York) and press Search.",
            font=("Segoe UI", 10),
            bg=COLOR_BG,
            fg=COLOR_TEXT_SECONDARY,
            wraplength=420
        )
        lbl_tip.pack(pady=40)

    def perform_search(self):
        query = self.entry_city.get().strip()
        if not query:
            return
            
        # Clean results frame
        for child in self.results_container.winfo_children():
            child.destroy()
            
        # Loading Indicator
        lbl_loading = tk.Label(
            self.results_container,
            text="Searching location...",
            font=("Segoe UI", 10),
            bg=COLOR_BG,
            fg=COLOR_TEXT_SECONDARY
        )
        lbl_loading.pack(pady=30)
        
        def search_thread():
            results = geocode_city(query)
            self.root.after(0, self.display_search_results, results)
            
        threading.Thread(target=search_thread, daemon=True).start()

    def display_search_results(self, results):
        for child in self.results_container.winfo_children():
            child.destroy()
            
        if not results:
            lbl_empty = tk.Label(
                self.results_container,
                text="No locations found. Make sure the name is typed correctly.",
                font=("Segoe UI Semibold", 10),
                bg=COLOR_BG,
                fg=COLOR_ALERT
            )
            lbl_empty.pack(pady=30)
            return
            
        # Draw list headers
        lbl_header = tk.Label(
            self.results_container,
            text="Select City:",
            font=("Segoe UI Semibold", 10),
            bg=COLOR_BG,
            fg=COLOR_TEXT_SECONDARY
        )
        lbl_header.pack(anchor="w", pady=(0, 5))
        
        # Scrollable list implementation
        canvas = tk.Canvas(self.results_container, bg=COLOR_BG, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.results_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLOR_BG)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=430)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate cities
        for idx, item in enumerate(results):
            full_name = f"{item['name']}"
            if item['admin1']:
                full_name += f", {item['admin1']}"
            full_name += f" ({item['country']})"
            
            # City Item Row frame
            row = tk.Frame(scrollable_frame, bg=COLOR_CARD, bd=1, relief="solid", highlightbackground=COLOR_BORDER)
            row.pack(fill="x", pady=4, ipady=5)
            
            lbl_city = tk.Label(
                row,
                text=full_name,
                font=("Segoe UI", 10),
                bg=COLOR_CARD,
                fg=COLOR_TEXT_PRIMARY,
                anchor="w"
            )
            lbl_city.pack(side="left", padx=15, fill="x", expand=True)
            
            btn_select = tk.Button(
                row,
                text="Select",
                font=("Segoe UI Semibold", 9),
                command=lambda location=item: self.select_city(location)
            )
            self.make_button_modern(btn_select, COLOR_ACCENT, COLOR_ACCENT_HOVER)
            btn_select.pack(side="right", padx=15, pady=5)

    def select_city(self, location):
        self.config["city"] = location["name"]
        self.config["latitude"] = location["lat"]
        self.config["longitude"] = location["lon"]
        save_config(self.config)
        
        self.scheduler.update_config()
        messagebox.showinfo("Success", f"Monitored location updated to {location['name']}!")
        self.show_page("dashboard")

    # ==================== PAGE: SETTINGS ====================
    def create_settings_page(self):
        # Main Title
        lbl_title = tk.Label(
            self.page_settings, 
            text="⚙️ Alert & Notification Preferences", 
            font=("Segoe UI Semibold", 12), 
            bg=COLOR_BG, 
            fg=COLOR_TEXT_PRIMARY
        )
        lbl_title.pack(anchor="w", pady=(0, 10))
        
        # Scrollable container for forms (so everything fits on smaller monitors)
        settings_canvas = tk.Canvas(self.page_settings, bg=COLOR_BG, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.page_settings, orient="vertical", command=settings_canvas.yview)
        form_frame = tk.Frame(settings_canvas, bg=COLOR_BG)
        
        form_frame.bind(
            "<Configure>",
            lambda e: settings_canvas.configure(scrollregion=settings_canvas.bbox("all"))
        )
        
        settings_canvas.create_window((0, 0), window=form_frame, anchor="nw", width=440)
        settings_canvas.configure(yscrollcommand=scrollbar.set)
        
        settings_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 1. Enable Notification Toggle
        self.var_enable_notif = tk.BooleanVar()
        chk_notif = tk.Checkbutton(
            form_frame, 
            text="Enable Live Weather Desktop Notifications",
            variable=self.var_enable_notif,
            font=("Segoe UI Semibold", 10),
            bg=COLOR_BG,
            fg=COLOR_TEXT_PRIMARY,
            selectcolor=COLOR_CARD,
            activebackground=COLOR_BG,
            activeforeground=COLOR_TEXT_PRIMARY
        )
        chk_notif.pack(anchor="w", pady=(5, 10))
        
        # 2. Update Interval Dropdown
        interval_frame = tk.Frame(form_frame, bg=COLOR_BG)
        interval_frame.pack(fill="x", pady=8)
        
        lbl_interval = tk.Label(
            interval_frame,
            text="Notification Interval:",
            font=("Segoe UI", 10),
            bg=COLOR_BG,
            fg=COLOR_TEXT_SECONDARY
        )
        lbl_interval.pack(side="left", padx=(0, 10))
        
        self.cbo_interval = ttk.Combobox(
            interval_frame,
            values=["5 Minutes", "15 Minutes", "30 Minutes", "1 Hour", "2 Hours"],
            state="readonly",
            width=15
        )
        self.cbo_interval.pack(side="left")
        
        # Separator line
        sep1 = tk.Frame(form_frame, height=1, bg=COLOR_BORDER)
        sep1.pack(fill="x", pady=15)
        
        # Alert Thresholds Headers
        lbl_alerts_title = tk.Label(
            form_frame,
            text="Trigger Custom Warning Alerts for:",
            font=("Segoe UI Semibold", 11),
            bg=COLOR_BG,
            fg=COLOR_TEXT_PRIMARY
        )
        lbl_alerts_title.pack(anchor="w", pady=(0, 10))
        
        # 3. High Temp Threshold
        ht_frame = tk.Frame(form_frame, bg=COLOR_BG)
        ht_frame.pack(fill="x", pady=6)
        lbl_ht = tk.Label(
            ht_frame,
            text="🔥 High Temperature Alert Threshold (°C):",
            font=("Segoe UI", 9),
            bg=COLOR_BG,
            fg=COLOR_TEXT_SECONDARY
        )
        lbl_ht.pack(side="left")
        
        self.entry_ht = tk.Entry(ht_frame, bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY, bd=1, relief="solid", width=8, justify="center")
        self.entry_ht.pack(side="right")
        
        # 4. Low Temp Threshold
        lt_frame = tk.Frame(form_frame, bg=COLOR_BG)
        lt_frame.pack(fill="x", pady=6)
        lbl_lt = tk.Label(
            lt_frame,
            text="❄️ Low Temperature Alert Threshold (°C):",
            font=("Segoe UI", 9),
            bg=COLOR_BG,
            fg=COLOR_TEXT_SECONDARY
        )
        lbl_lt.pack(side="left")
        
        self.entry_lt = tk.Entry(lt_frame, bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY, bd=1, relief="solid", width=8, justify="center")
        self.entry_lt.pack(side="right")
        
        # 5. Rain alert checkbox
        self.var_rain_alert = tk.BooleanVar()
        chk_rain = tk.Checkbutton(
            form_frame, 
            text="🌧️ Alert if Rain, Snow or Storms are imminent",
            variable=self.var_rain_alert,
            font=("Segoe UI", 10),
            bg=COLOR_BG,
            fg=COLOR_TEXT_PRIMARY,
            selectcolor=COLOR_CARD,
            activebackground=COLOR_BG,
            activeforeground=COLOR_TEXT_PRIMARY
        )
        chk_rain.pack(anchor="w", pady=6)
        
        # 6. Wind alert checkbox + threshold
        wind_control_frame = tk.Frame(form_frame, bg=COLOR_BG)
        wind_control_frame.pack(fill="x", pady=6)
        
        self.var_wind_alert = tk.BooleanVar()
        chk_wind = tk.Checkbutton(
            wind_control_frame, 
            text="💨 Alert if Wind speed exceeds (km/h):",
            variable=self.var_wind_alert,
            font=("Segoe UI", 10),
            bg=COLOR_BG,
            fg=COLOR_TEXT_PRIMARY,
            selectcolor=COLOR_CARD,
            activebackground=COLOR_BG,
            activeforeground=COLOR_TEXT_PRIMARY
        )
        chk_wind.pack(side="left")
        
        self.entry_wind = tk.Entry(wind_control_frame, bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY, bd=1, relief="solid", width=8, justify="center")
        self.entry_wind.pack(side="right")
        
        # Separator line
        sep2 = tk.Frame(form_frame, height=1, bg=COLOR_BORDER)
        sep2.pack(fill="x", pady=15)
        
        # 7. Action buttons
        actions_frame = tk.Frame(form_frame, bg=COLOR_BG)
        actions_frame.pack(fill="x", pady=10)
        
        btn_test = tk.Button(
            actions_frame,
            text="🔔 Test Notification",
            font=("Segoe UI Semibold", 10),
            command=self.trigger_test_notification
        )
        self.make_button_modern(btn_test, COLOR_CARD, COLOR_BORDER)
        btn_test.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        btn_save = tk.Button(
            actions_frame,
            text="💾 Save Settings",
            font=("Segoe UI Semibold", 10),
            command=self.save_settings
        )
        self.make_button_modern(btn_save, COLOR_ACCENT, COLOR_ACCENT_HOVER)
        btn_save.pack(side="right", fill="x", expand=True, padx=(5, 0))

    def load_settings_values(self):
        # Enable notifications checkbox
        self.var_enable_notif.set(self.config.get("enable_notifications", True))
        
        # Interval ComboBox
        mins = self.config.get("interval_minutes", 30)
        mapping = {5: "5 Minutes", 15: "15 Minutes", 30: "30 Minutes", 60: "1 Hour", 120: "2 Hours"}
        self.cbo_interval.set(mapping.get(mins, "30 Minutes"))
        
        # High and Low Temp entries
        self.entry_ht.delete(0, tk.END)
        self.entry_ht.insert(0, str(self.config.get("temp_high_threshold", 35.0)))
        
        self.entry_lt.delete(0, tk.END)
        self.entry_lt.insert(0, str(self.config.get("temp_low_threshold", 15.0)))
        
        # Rain checkbox
        self.var_rain_alert.set(self.config.get("rain_alert_enabled", True))
        
        # Wind checkbox and entry
        self.var_wind_alert.set(self.config.get("wind_alert_enabled", False))
        self.entry_wind.delete(0, tk.END)
        self.entry_wind.insert(0, str(self.config.get("wind_threshold_kmh", 40.0)))

    def save_settings(self):
        try:
            # Parse Interval
            interval_str = self.cbo_interval.get()
            interval_map = {
                "5 Minutes": 5,
                "15 Minutes": 15,
                "30 Minutes": 30,
                "1 Hour": 60,
                "2 Hours": 120
            }
            self.config["interval_minutes"] = interval_map.get(interval_str, 30)
            
            # Parse Temperatures
            self.config["temp_high_threshold"] = float(self.entry_ht.get().strip())
            self.config["temp_low_threshold"] = float(self.entry_lt.get().strip())
            
            # Parse checkboxes
            self.config["enable_notifications"] = self.var_enable_notif.get()
            self.config["rain_alert_enabled"] = self.var_rain_alert.get()
            
            # Parse Wind Speed
            self.config["wind_alert_enabled"] = self.var_wind_alert.get()
            self.config["wind_threshold_kmh"] = float(self.entry_wind.get().strip())
            
            save_config(self.config)
            self.scheduler.update_config()
            messagebox.showinfo("Success", "Settings saved successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid numerical threshold. Please enter valid numbers (e.g. 35.5, 10).")

    def trigger_test_notification(self):
        # Forces a check and shows a test notification based on current coordinates
        self.scheduler.check_now()

    # ==================== COMPACT DESKTOP FLOATING WIDGET ====================
    def run_in_background(self):
        # Hide the main window
        self.root.withdraw()
        
        # Show system notification about background operation
        city = self.config.get("city", "New Delhi")
        send_toast(
            "Running in Background",
            f"Weather monitor is active for {city}. Double-click the floating sticker to restore."
        )
        
        # Create Toplevel borderless window
        self.widget_window = tk.Toplevel(self.root)
        self.widget_window.title("Weather Widget")
        self.widget_window.overrideredirect(True)
        self.widget_window.attributes("-topmost", True)
        self.widget_window.configure(bg=COLOR_BG)
        
        # Size and Placement: Place in the bottom right corner of the primary screen
        w, h = 180, 75
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        # Windows taskbar is usually at the bottom, so offset by 50px
        x = screen_w - w - 20
        y = screen_h - h - 60
        self.widget_window.geometry(f"{w}x{h}+{x}+{y}")
        
        # Draw glassmorphism capsule on a canvas
        self.widget_canvas = tk.Canvas(self.widget_window, bg=COLOR_BG, bd=0, highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.widget_canvas.pack(fill="both", expand=True)
        
        # Dragging support bindings
        self.widget_canvas.bind("<Button-1>", self.start_drag)
        self.widget_canvas.bind("<B1-Motion>", self.drag_window)
        
        # Double-click restores application
        self.widget_canvas.bind("<Double-Button-1>", self.restore_from_background)
        
        # Render initial info
        self.update_widget_ui()

    def update_widget_ui(self):
        if not self.widget_window or not self.widget_window.winfo_exists():
            return
            
        self.widget_canvas.delete("all")
        
        # Render weather details
        city = self.config.get("city", "New Delhi")
        if len(city) > 12:
            city = city[:10] + ".."
            
        temp = "--"
        emoji = "🌡️"
        
        if self.current_weather:
            temp = self.current_weather.get("temp", "--")
            emoji = self.current_weather.get("emoji", "🌡️")
            
        # Draw Capsule visual elements
        # Emoji Icon
        self.widget_canvas.create_text(
            30, 36,
            text=emoji,
            font=("Segoe UI", 32),
            tags="widget_elem"
        )
        
        # Temp Text
        self.widget_canvas.create_text(
            75, 26,
            text=f"{temp}°C",
            font=("Segoe UI Semibold", 16),
            fill=COLOR_TEXT_PRIMARY,
            anchor="w",
            tags="widget_elem"
        )
        
        # City text
        self.widget_canvas.create_text(
            75, 48,
            text=city,
            font=("Segoe UI", 10),
            fill=COLOR_TEXT_SECONDARY,
            anchor="w",
            tags="widget_elem"
        )
        
        # Tiny exit button on top right of the widget
        # Clicking it exits the full application
        btn_close_widget = tk.Label(
            self.widget_canvas,
            text="✕",
            font=("Arial", 9),
            bg=COLOR_BG,
            fg=COLOR_TEXT_SECONDARY,
            cursor="hand2"
        )
        # Place widget label inside canvas
        self.widget_canvas.create_window(165, 12, window=btn_close_widget)
        btn_close_widget.bind("<Button-1>", lambda e: self.on_close())
        
        # Hover color change
        btn_close_widget.bind("<Enter>", lambda e: btn_close_widget.config(fg=COLOR_ALERT))
        btn_close_widget.bind("<Leave>", lambda e: btn_close_widget.config(fg=COLOR_TEXT_SECONDARY))

    def start_drag(self, event):
        self.widget_drag_x = event.x
        self.widget_drag_y = event.y

    def drag_window(self, event):
        deltax = event.x - self.widget_drag_x
        deltay = event.y - self.widget_drag_y
        x = self.widget_window.winfo_x() + deltax
        y = self.widget_window.winfo_y() + deltay
        self.widget_window.geometry(f"+{x}+{y}")

    def restore_from_background(self, event=None):
        if self.widget_window:
            self.widget_window.destroy()
            self.widget_window = None
            
        # Deiconify and show main dashboard
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    # ==================== SHUTDOWN HANDLERS ====================
    def on_close(self):
        # Stop background scheduler thread
        if hasattr(self, 'scheduler') and self.scheduler:
            self.scheduler.stop()
            
        if self.widget_window:
            self.widget_window.destroy()
            
        self.root.destroy()

if __name__ == "__main__":
    # Configure Tkinter root
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()
>>>>>>> b0a67e270fb13439c156a260e13b6ebe317dd4fc
