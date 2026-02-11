from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.main import calculate_hourly_temperatures
from app.utils.fetch_weather import fetch_weather
from dotenv import load_dotenv
import os

load_dotenv()

api_website = os.getenv('API_WEBSITE')


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[api_website],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

class SimulationInput(BaseModel):
    city: str
    start_date: str
    end_date: str

@app.get("/")
def root():
    return {"message": "Simulation API is running!"}

@app.get("/simulate")
def simulate(
    city: str,
    start_date: str,
    end_date: str,
    heating_power: int,
    mat_toggle: bool):
    weather_df = fetch_weather(city, start_date, end_date)
    hourly_temps = calculate_hourly_temperatures(weather_df, heating_power, mat_toggle)
    hourly_temps["Timestamp"] = hourly_temps["Timestamp"].astype(str)
    response_data = hourly_temps.to_dict(orient="records")
    return {"status": "success", "data": response_data}
