import requests
from sense_hat import SenseHat
from weather_icons import icon_map # Assuming weather_icons.py is in the same directory and imports its icon_map based on OpenWeatherMap codes
import time
from datetime import datetime
import os
import csv
import config

sense = SenseHat()

URL = f"http://api.openweathermap.org/data/2.5/weather?q={config.CITY}&appid={config.API_KEY}&units=imperial"

headers = {
    "User-Agent": "Mozilla/5.0 (Raspberry Pi; SenseHAT Script)"
}

try:
    response = requests.get(URL, headers=headers)
    print("Status:", response.status_code)
    print("Raw:", response.text)

    data = response.json()

    if response.status_code != 200:
        raise Exception(f"API error: {data.get('message', 'Unknown error')}")

    # Display fields
    weather = data["weather"][0]["description"].capitalize()
    temp = round(data["main"]["temp"])
    humidity = data["main"]["humidity"]

    # Extract weather icon code (e.g., "01d", "10d")
    weather_code = data["weather"][0]["icon"]

    # Display weather summary - City, Condition, Temp, Humidity
    message = "Current Weather:"
    sense.show_message(message, scroll_speed=0.05, text_colour=[0, 255, 127])
    time.sleep(1)
    sense.clear()

    # Display icon if available
    if weather_code in icon_map:
        sense.set_pixels(icon_map[weather_code])
        time.sleep(7)
        sense.clear()
        time.sleep(1)
    else:
        sense.show_message("No icon!", scroll_speed=0.05, text_colour=[255, 0, 0])

    # Display weather summary - City, Condition, Temp, Humidity
    message = f"{config.CITY}: Conditions {weather}, Temp: {temp}F, RH: {humidity}%"
    sense.show_message(message, scroll_speed=0.05, text_colour=[0, 255, 127])

    # Expanded CSV fields
    feels_like = round(data["main"]["feels_like"])
    temp_min = round(data["main"]["temp_min"])
    temp_max = round(data["main"]["temp_max"])
    pressure = data["main"]["pressure"]
    visibility = data.get("visibility", None)
    wind_speed = data["wind"].get("speed", None)
    wind_deg = data["wind"].get("deg", None)
    wind_gust = data["wind"].get("gust", None)
    cloud_cover = data["clouds"].get("all", None)
    sunrise = data["sys"].get("sunrise", None)
    sunset = data["sys"].get("sunset", None)

    # CSV logging block
    log_path = "/home/jiri/logs/weather-lombard.csv"
    
    timestamp = datetime.now().isoformat()

    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    write_header = not os.path.exists(log_path)

    with open(log_path, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow([
                "timestamp", "city", "weather", "temp_f", "humidity",
                "feels_like_f", "temp_min_f", "temp_max_f", "pressure",
                "visibility_m", "wind_speed_mph", "wind_deg", "wind_gust_mph",
                "cloud_cover_pct", "sunrise_unix", "sunset_unix"
            ])
        writer.writerow([
            timestamp, config.CITY, weather, temp, humidity,
            feels_like, temp_min, temp_max, pressure,
            visibility, wind_speed, wind_deg, wind_gust,
            cloud_cover, sunrise, sunset
        ])

except Exception as e:
    sense.show_message("Weather fetch failed", text_colour=[255, 0, 0])
    print("Error:", e)

time.sleep(2)
sense.clear()
