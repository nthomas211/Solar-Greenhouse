import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from weather import get_weather
import model

app = FastAPI()

# This allows your React app to talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "backend is running"}

@app.post("/run-simulation")
def run_simulation(params: dict):

    # temporary hardcoded params for testing
    params = {
        "name": "test_run",
        "location": { "lat": 41.8781, "lon": -87.6298 },
        "start_date": "2026-02-10",
        "end_date": "2026-02-14",
        "parameters": {
            "A_glass": 50.0,
            "tau_glass": 0.85,
            "fraction_solar_to_air": 0.3,
            "U_day": 2.0,
            "U_night": 0.25,
            "ACH": 0.5,
            "V": 100.0,
            "A_floor": 50.0,
            "thermal_mass_kg": 40000.0,
            "cp_mass": 4186.0,
            "A_mass": 40.0,
            "h_am": 5.0,
            "heater_max_w": 5000.0,
            "heating_rate_factor": 0.3,
            "T_init": 15.0,
            "T_mass_init": 15.0,
            "T_soil_init": 15.0,
            "setpoint": 10.0
        }
    }

    # get wheather data
    weather_df = get_weather(params["location"], params["start_date"], params["end_date"])

    # simulate greenhouse with inputs
    result_df = model.simulate_greenhouse(weather_df, params["parameters"])

    return result_df.to_dict(orient="records")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)