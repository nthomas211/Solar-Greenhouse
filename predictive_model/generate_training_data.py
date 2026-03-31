"""
Greenhouse Training Data Generator
------------------------------------
Fetches real historical weather from Open-Meteo (no API key needed),
runs the greenhouse sim across thousands of random param combinations,
and saves results to TinyDB with checkpointing.

Requirements:
    pip install tinydb pandas numpy requests

Usage:
    python generate_training_data.py

Place model.py in the same directory before running.
"""

import os
import json
import requests
import numpy as np
import pandas as pd
from tinydb import TinyDB, Query
from multiprocessing import Pool
from datetime import datetime

# ── Import your sim ───────────────────────────────────────────────────────────
from model import simulate_greenhouse


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG — tweak these before running
# ─────────────────────────────────────────────────────────────────────────────

N_RUNS          = 5000      # total param combinations to generate
YEAR            = "2024"    # full year of weather data (2024 is fully archived)
DB_PATH         = "training_data.json"
CHECKPOINT_FILE = "checkpoint.json"
SEED            = 42

# Locations covering a range of climates
# All cold-climate since this is a Chinese passive solar greenhouse
LOCATIONS = [
    {"name": "Chicago",      "lat": 41.8781, "lon": -87.6298},
    {"name": "Minneapolis",  "lat": 44.9778, "lon": -93.2650},
    {"name": "Boston",       "lat": 42.3601, "lon": -71.0589},
    {"name": "Denver",       "lat": 39.7392, "lon": -104.9903},
    {"name": "Seattle",      "lat": 47.6062, "lon": -122.3321},
    {"name": "Portland",     "lat": 45.5051, "lon": -122.6750},
    {"name": "Detroit",      "lat": 42.3314, "lon": -83.0458},
    {"name": "Salt Lake City","lat": 40.7608, "lon": -111.8910},
]


# ─────────────────────────────────────────────────────────────────────────────
# WEATHER FETCHING
# ─────────────────────────────────────────────────────────────────────────────

def fetch_weather(lat: float, lon: float, year: str) -> pd.DataFrame:
    """
    Fetch a full year of hourly weather from Open-Meteo archive.
    Returns a DataFrame with columns: datetime, Tout, G, RH
    No API key required.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude":  lat,
        "longitude": lon,
        "start_date": f"{year}-01-01",
        "end_date":   f"{year}-12-31",
        "hourly": [
            "temperature_2m",       # Tout (°C)
            "shortwave_radiation",  # G    (W/m²)
            "relative_humidity_2m", # RH   (%)
        ],
        "timezone": "auto",
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    hourly = resp.json()["hourly"]

    df = pd.DataFrame({
        "datetime": pd.to_datetime(hourly["time"]),
        "Tout": hourly["temperature_2m"],
        "G":    hourly["shortwave_radiation"],
        "RH":  [v / 100.0 for v in hourly["relative_humidity_2m"]],  # % → 0-1
    })

    # Drop any rows with missing data
    df = df.dropna().reset_index(drop=True)
    return df


def fetch_all_weather() -> dict:
    """
    Fetch weather for all locations upfront and cache in memory.
    Prints progress so you know it's working.
    """
    weather_cache = {}
    for loc in LOCATIONS:
        print(f"  Fetching weather for {loc['name']}...")
        try:
            df = fetch_weather(loc["lat"], loc["lon"], YEAR)
            weather_cache[loc["name"]] = df
            print(f"    ✓ {len(df)} hourly rows")
        except Exception as e:
            print(f"    ✗ Failed: {e}")
    return weather_cache


# ─────────────────────────────────────────────────────────────────────────────
# PARAMETER RANDOMISATION
# ─────────────────────────────────────────────────────────────────────────────

def random_params(rng: np.random.Generator) -> dict:
    """
    Sample a random but physically plausible set of greenhouse design params.
    Ranges are kept realistic for a Chinese passive solar greenhouse.
    """
    A_floor = rng.uniform(20, 200)
    # Volume is loosely derived from floor area (height 2-4m)
    V = A_floor * rng.uniform(2.0, 4.0)

    setpoint = rng.choice([None, 5.0, 8.0, 10.0, 12.0, 15.0, 18.0])

    return {
        # ── Geometry ─────────────────────────────────────────────
        "A_glass":               rng.uniform(15, 180),
        "A_floor":               A_floor,
        "V":                     V,
        "A_mass":                rng.uniform(10, 80),

        # ── Glass & envelope ─────────────────────────────────────
        "tau_glass":             rng.uniform(0.60, 0.95),
        "U_day":                 rng.uniform(1.0,  5.0),
        "U_night":               rng.uniform(0.10, 0.80),
        "emissivity":            rng.uniform(0.7,  0.95),

        # ── Construction ─────────────────────────────────────────
        "ACH":                   rng.uniform(0.1, 2.0),
        "fraction_solar_to_air": rng.uniform(0.3, 0.7),

        # ── Thermal mass ─────────────────────────────────────────
        "thermal_mass_kg":       rng.uniform(500, 50000),
        "h_am":                  rng.uniform(1.0, 6.0),
        "cp_mass":               rng.uniform(2000, 4200),  # varies: rock, water, concrete

        # ── Soil ─────────────────────────────────────────────────
        "soil_C":                rng.uniform(1e6, 6e6),
        "soil_U":                rng.uniform(0.2, 1.0),

        # ── Heating ──────────────────────────────────────────────
        "heater_max_w":          float(rng.choice([0, 1000, 2000, 3000, 5000, 8000, 10000])),
        "setpoint":              setpoint,

        # ── Cloud / radiation ────────────────────────────────────
        "cloud_factor":          rng.uniform(0.2, 0.8),
        "lw_radiation_scale":    rng.uniform(0.5, 0.9),

        # ── Initial state ────────────────────────────────────────
        # Vary so the model sees diverse starting conditions
        "T_init":                rng.uniform(2, 20),
        "T_mass_init":           rng.uniform(2, 20),
        "T_soil_init":           rng.uniform(2, 18),
    }


# ─────────────────────────────────────────────────────────────────────────────
# SINGLE RUN (called by each worker process)
# ─────────────────────────────────────────────────────────────────────────────

def run_single(args: tuple) -> dict | None:
    """
    Run the sim for one param set + weather combo.
    Returns a record dict or None if the run failed.
    """
    run_id, params, weather_df = args

    try:
        result_df = simulate_greenhouse(weather_df, params)

        if result_df.empty:
            return None

        # Serialise params — replace None setpoint with -1 for storage
        stored_params = {
            k: (v if v is not None else -1)
            for k, v in params.items()
        }

        # Summary stats — these become inputs/outputs for the inverse model
        record = {
            "run_id":    run_id,
            "params":    stored_params,
            "outputs": {
                "avg_Tin":          float(result_df["Tin"].mean()),
                "min_Tin":          float(result_df["Tin"].min()),
                "max_Tin":          float(result_df["Tin"].max()),
                "std_Tin":          float(result_df["Tin"].std()),
                "avg_Q_heater":     float(result_df["Q_heater"].mean()),
                "total_Q_heater":   float(result_df["Q_heater"].sum()),
                "avg_T_mass":       float(result_df["T_mass"].mean()),
                "avg_T_soil":       float(result_df["T_soil"].mean()),
                "hours_below_5c":   int((result_df["Tin"] < 5).sum()),
                "hours_below_0c":   int((result_df["Tin"] < 0).sum()),
            },
        }
        return record

    except Exception as e:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# CHECKPOINT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def load_checkpoint() -> int:
    """Returns the last completed run_id, or -1 if no checkpoint exists."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            return json.load(f).get("last_run_id", -1)
    return -1


def save_checkpoint(run_id: int):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"last_run_id": run_id, "timestamp": str(datetime.now())}, f)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    n_cores = os.cpu_count()
    print(f"\n{'='*55}")
    print(f"  Greenhouse Training Data Generator")
    print(f"  Cores available : {n_cores}")
    print(f"  Target runs     : {N_RUNS}")
    print(f"  Weather year    : {YEAR}")
    print(f"  Output DB       : {DB_PATH}")
    print(f"{'='*55}\n")

    # ── Step 1: Fetch weather for all locations ───────────────────
    print("Fetching weather data...")
    weather_cache = fetch_all_weather()
    location_names = list(weather_cache.keys())
    print(f"\n✓ Weather ready for {len(location_names)} locations\n")

    # ── Step 2: Check for existing checkpoint ────────────────────
    last_completed = load_checkpoint()
    start_from = last_completed + 1
    if start_from > 0:
        print(f"Resuming from run {start_from} (checkpoint found)\n")

    # ── Step 3: Build all jobs ────────────────────────────────────
    rng = np.random.default_rng(SEED)
    location_list = list(weather_cache.values())

    jobs = []
    for i in range(N_RUNS):
        params = random_params(rng)
        # Assign each run a location round-robin so all locations get coverage
        weather_df = location_list[i % len(location_list)]
        jobs.append((i, params, weather_df))

    # Skip already completed runs
    jobs = [j for j in jobs if j[0] >= start_from]
    print(f"Jobs to process: {len(jobs)}\n")

    # ── Step 4: Run in parallel with checkpointing ───────────────
    db = TinyDB(DB_PATH)
    completed = 0
    failed    = 0

    BATCH_SIZE = 200  # save checkpoint every N runs

    with Pool(processes=n_cores) as pool:
        for batch_start in range(0, len(jobs), BATCH_SIZE):
            batch = jobs[batch_start : batch_start + BATCH_SIZE]
            results = pool.map(run_single, batch)

            for result in results:
                if result is not None:
                    db.insert(result)
                    completed += 1
                else:
                    failed += 1

            last_id = batch[-1][0]
            save_checkpoint(last_id)

            total_done = batch_start + len(batch)
            print(
                f"  Progress: {total_done}/{len(jobs)} | "
                f"Saved: {completed} | "
                f"Failed: {failed}"
            )

    # ── Done ─────────────────────────────────────────────────────
    print(f"\n{'='*55}")
    print(f"  Complete!")
    print(f"  Saved  : {completed} records")
    print(f"  Failed : {failed} runs")
    print(f"  Output : {DB_PATH}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
