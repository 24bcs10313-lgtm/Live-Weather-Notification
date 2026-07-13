import requests

# WMO Weather Codes mapping to human-friendly description and emoji
WMO_CODES = {
    0: ("Clear Sky", "☀️", "🌙"),
    1: ("Mainly Clear", "🌤️", "🌙"),
    2: ("Partly Cloudy", "⛅", "⛅"),
    3: ("Overcast", "☁️", "☁️"),
    45: ("Foggy", "🌫️", "🌫️"),
    48: ("Depositing Rime Fog", "🌫️", "🌫️"),
    51: ("Light Drizzle", "🌧️", "🌧️"),
    53: ("Moderate Drizzle", "🌧️", "🌧️"),
    55: ("Dense Drizzle", "🌧️", "🌧️"),
    56: ("Light Freezing Drizzle", "🌨️", "🌨️"),
    57: ("Dense Freezing Drizzle", "🌨️", "🌨️"),
    61: ("Slight Rain", "🌦️", "🌦️"),
    63: ("Moderate Rain", "🌧️", "🌧️"),
    65: ("Heavy Rain", "🌧️", "🌧️"),
    66: ("Light Freezing Rain", "🌨️", "🌨️"),
    67: ("Heavy Freezing Rain", "🌨️", "🌨️"),
    71: ("Slight Snowfall", "❄️", "❄️"),
    73: ("Moderate Snowfall", "❄️", "❄️"),
    75: ("Heavy Snowfall", "❄️", "❄️"),
    77: ("Snow Grains", "❄️", "❄️"),
    80: ("Slight Showers", "🌦️", "🌦️"),
    81: ("Moderate Showers", "🌦️", "🌦️"),
    82: ("Violent Showers", "🌧️", "🌧️"),
    85: ("Slight Snow Showers", "🌨️", "🌨️"),
    86: ("Heavy Snow Showers", "🌨️", "🌨️"),
    95: ("Thunderstorm", "⛈️", "⛈️"),
    96: ("Thunderstorm with Hail", "⛈️", "⛈️"),
    99: ("Heavy Thunderstorm with Hail", "⛈️", "⛈️")
}

def get_weather_desc(code, is_day=1):
    desc_tuple = WMO_CODES.get(code, ("Unknown", "🌡️", "🌡️"))
    desc = desc_tuple[0]
    emoji = desc_tuple[1] if is_day else desc_tuple[2]
    return desc, emoji

def geocode_city(city_name):
    """
    Search coordinates for a given city name using requests.
    """
    if not city_name or len(city_name.strip()) < 2:
        return []
    
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city_name.strip(),
        "count": 5,
        "language": "en",
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        
        parsed_results = []
        for r in results:
            parsed_results.append({
                "name": r.get("name"),
                "country": r.get("country", ""),
                "admin1": r.get("admin1", ""), # state/province
                "lat": r.get("latitude"),
                "lon": r.get("longitude")
            })
        return parsed_results
    except Exception as e:
        print(f"Geocoding error: {e}")
        return []

def fetch_weather(lat, lon):
    """
    Fetch current weather and daily summary for coordinates using requests.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,snowfall,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto"
    }
    
    try:
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current", {})
        daily = data.get("daily", {})
        
        weather_code = current.get("weather_code", 0)
        is_day = current.get("is_day", 1)
        desc, emoji = get_weather_desc(weather_code, is_day)
        
        temp_max = daily.get("temperature_2m_max", [None])[0]
        temp_min = daily.get("temperature_2m_min", [None])[0]
        rain_prob = daily.get("precipitation_probability_max", [0])[0]
        
        weather_info = {
            "temp": current.get("temperature_2m"),
            "temp_feels": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "precipitation": current.get("precipitation"),
            "rain": current.get("rain"),
            "showers": current.get("showers"),
            "snowfall": current.get("snowfall"),
            "weather_code": weather_code,
            "is_day": is_day,
            "desc": desc,
            "emoji": emoji,
            "temp_max": temp_max if temp_max is not None else current.get("temperature_2m"),
            "temp_min": temp_min if temp_min is not None else current.get("temperature_2m"),
            "rain_prob": rain_prob
        }
        return weather_info
    except Exception as e:
        print(f"Weather fetch error: {e}")
        return None
