import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from weather import get_weather
import model

# from pymongo import MongoClient

# client = MongoClient("mongodb://localhost:27017/")
# db = client["greenhouse"]
# simulated = db["simulated_runs"]

from tinydb import TinyDB

db = TinyDB('simulations.json')
simulated = db.table('simulated_runs')

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
    weather_df = get_weather(params["location"], params["start_date"], params["end_date"])
    result_df = model.simulate_greenhouse(weather_df, params["parameters"])
    result_df["datetime"] = result_df["datetime"].astype(str)

    rows = result_df.to_dict(orient="records")

    # insert works almost the same as pymongo
    simulated.insert({
        "name": params["name"],
        "run_at": str(datetime.now()),
        "location": params["location"],
        "start_date": params["start_date"],  # ← add this
        "end_date": params["end_date"],       # ← and this
        "parameters": params["parameters"],
        "rows": rows
    })

    return {
        "status": "ok",
        "rows": rows
    }

@app.get("/history")
def get_history():
    runs = simulated.all()
    sorted_runs = sorted(runs, key=lambda x: x.get("start_date", ""), reverse=True)
    return {
        "status": "ok",
        "runs": [
            {
                "id": r.doc_id,
                "name": r["name"],
                "run_at": r["run_at"],
                "location": r["location"],
                "start_date": r["start_date"],
                "end_date": r["end_date"],
            }
            for r in sorted_runs
        ]
    }

@app.get("/history/{run_id}")
def get_run(run_id: int):
    run = simulated.get(doc_id=run_id)
    if not run:
        return {"status": "error", "message": "Run not found"}
    return {"status": "ok", "run": run}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)