import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('OPENWEATHERAPI_KEY')
base_url = "http://api.weatherapi.com/v1/history.json"

def fetch_weather(city, start, end):
    params = {
        "key": api_key,
        "q": city,
        "dt": start,
        "end_dt": end,
        "aqi": "no",
        "alerts": "no"
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    return parse_weather_data(data)

def parse_weather_data(data):
    hourly_data = []
    for forecast_day in data['forecast']['forecastday']:
        
        sunrise_str = forecast_day["astro"]["sunrise"]
        sunset_str = forecast_day["astro"]["sunset"]
        sunrise = datetime.strptime(sunrise_str, "%I:%M %p").time()
        sunset = datetime.strptime(sunset_str, "%I:%M %p").time()

        for hour_data in forecast_day["hour"]:
            timestamp = datetime.strptime(hour_data["time"], "%Y-%m-%d %H:%M")
            temp = hour_data["temp_c"]
            
            current_time = timestamp.time()
            is_daytime = sunrise <= current_time < sunset
            
            hourly_data.append({
                "timestamp": timestamp,
                "temp": temp,
                "is_daytime": is_daytime
            })
            
    return pd.DataFrame(hourly_data)