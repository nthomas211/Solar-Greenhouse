"""
Inverse Design Model — Training Script
Solar Greenhouse Simulator
──────────────────────────────────────────────────────────────────────────────
Takes greenhouse performance targets + local climate context and predicts
plausible design parameter RANGES (10th–90th percentile) for each param.

Inputs (8):
    avg_Tin          – target average indoor temperature (°C)
    min_Tin          – target minimum indoor temperature (°C)
    hours_below_5c   – acceptable hours per year below 5°C
    hours_below_0c   – acceptable hours per year below 0°C
    total_Q_heater   – total heating energy budget (Wh, 0 = no heater)
    avg_Tout         – average outdoor temperature at location (°C)
    min_Tout         – minimum outdoor temperature at location (°C)
    avg_solar        – average solar radiation at location (W/m²)

Outputs (9 params × 2 bounds = 18):
    A_floor, V, A_glass, A_mass, tau_glass,
    U_day, U_night, thermal_mass_kg, ACH
    → each predicted as (low, high) range via quantile regression

Usage:
    pip install torch scikit-learn joblib numpy pandas requests
    python train_inverse_model.py

The best model checkpoint is saved automatically during training.
A predict() helper at the bottom can be imported directly by your backend.
"""

import json
import numpy as np
import pandas as pd
import requests
import joblib
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split
from sklearn.preprocessing import StandardScaler


# ──────────────────────────────────────────────────────────────────────────────
# CONFIG — adjust paths and hyperparameters here
# ──────────────────────────────────────────────────────────────────────────────

DB_PATH           = "training_data.json"   # output from generate_training_data.py
MODEL_OUT         = "inverse_model.pt"     # saved model weights
SCALER_X_OUT      = "scaler_X.pkl"        # saved input scaler
SCALER_Y_OUT      = "scaler_Y.pkl"        # saved output scaler
WEATHER_CACHE     = "weather_stats_cache.json"

SEED              = 42
BATCH_SIZE        = 64
EPOCHS            = 300
LR                = 1e-3                   # learning rate
WEIGHT_DECAY      = 1e-4                   # L2 regularization (helps overfitting)
HIDDEN_DIMS       = [128, 256, 256, 128]   # neurons per hidden layer
DROPOUT           = 0.2                    # dropout rate (0 = off, 0.5 = heavy)
PATIENCE          = 25                     # early stopping: stop if no improvement for N epochs

Q_LOW             = 0.10                   # lower bound quantile (10th percentile)
Q_HIGH            = 0.90                   # upper bound quantile (90th percentile)

YEAR              = "2024"


# Locations must match generate_training_data.py exactly
# (order matters — run_id % len(LOCATIONS) maps each run to a location)
LOCATIONS = [
    {"name": "Chicago",       "lat": 41.8781, "lon": -87.6298},
    {"name": "Minneapolis",   "lat": 44.9778, "lon": -93.2650},
    {"name": "Boston",        "lat": 42.3601, "lon": -71.0589},
    {"name": "Denver",        "lat": 39.7392, "lon": -104.9903},
    {"name": "Seattle",       "lat": 47.6062, "lon": -122.3321},
    {"name": "Portland",      "lat": 45.5051, "lon": -122.6750},
    {"name": "Detroit",       "lat": 42.3314, "lon": -83.0458},
    {"name": "Salt Lake City","lat": 40.7608, "lon": -111.8910},
]

# Columns the model uses — order matters, do not rearrange
INPUT_COLS = [
    "avg_Tin", "min_Tin", "hours_below_5c", "hours_below_0c",
    "total_Q_heater", "avg_Tout", "min_Tout", "avg_solar",
]

OUTPUT_COLS = [
    "A_floor", "V", "A_glass", "A_mass",
    "tau_glass", "U_day", "U_night",
    "thermal_mass_kg", "ACH",
]


# ──────────────────────────────────────────────────────────────────────────────
# STEP 1 — WEATHER STATS
# Compute avg/min outdoor temp and avg solar for each location.
# Results are cached so this only runs once (takes ~30s on first run).
# ──────────────────────────────────────────────────────────────────────────────

def fetch_weather_stats(lat: float, lon: float, year: str) -> dict:
    """Pull a full year of hourly data and return summary stats."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": f"{year}-01-01",
        "end_date":   f"{year}-12-31",
        "hourly": ["temperature_2m", "shortwave_radiation"],
        "timezone": "auto",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    hourly = resp.json()["hourly"]

    temps = np.array(hourly["temperature_2m"], dtype=float)
    solar = np.array(hourly["shortwave_radiation"], dtype=float)

    # Drop NaN rows
    valid_t = temps[~np.isnan(temps)]
    valid_s = solar[~np.isnan(solar)]

    return {
        "avg_Tout":  float(np.mean(valid_t)),
        "min_Tout":  float(np.min(valid_t)),
        "avg_solar": float(np.mean(valid_s)),
    }


def get_location_stats() -> dict:
    """
    Load weather stats from cache if available, otherwise fetch and cache them.
    Returns a dict keyed by location index (as string): {"0": {...}, "1": {...}, ...}
    """
    if Path(WEATHER_CACHE).exists():
        print(f"Loading weather stats from cache ({WEATHER_CACHE})")
        with open(WEATHER_CACHE) as f:
            return json.load(f)

    print("Fetching weather stats for all locations (this runs once and is cached)...")
    stats = {}
    for i, loc in enumerate(LOCATIONS):
        print(f"  {loc['name']}...", end=" ", flush=True)
        try:
            s = fetch_weather_stats(loc["lat"], loc["lon"], YEAR)
            stats[str(i)] = s
            print(f"avg_Tout={s['avg_Tout']:.1f}°C  min_Tout={s['min_Tout']:.1f}°C  avg_solar={s['avg_solar']:.1f} W/m²")
        except Exception as e:
            print(f"FAILED ({e}) — using fallback values")
            # Reasonable cold-climate fallbacks so training still works
            stats[str(i)] = {"avg_Tout": 8.0, "min_Tout": -18.0, "avg_solar": 140.0}

    with open(WEATHER_CACHE, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Weather stats cached → {WEATHER_CACHE}\n")
    return stats


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2 — DATA LOADING
# Reads training_data.json, joins weather stats, and assembles a DataFrame.
# ──────────────────────────────────────────────────────────────────────────────

def load_data(db_path: str, location_stats: dict) -> pd.DataFrame:
    with open(db_path) as f:
        raw = json.load(f)

    # TinyDB stores records under a "_default" table key
    table = raw.get("_default", raw)

    records = []
    skipped = 0
    for rec in table.values():
        try:
            params  = rec["params"]
            outputs = rec["outputs"]
            run_id  = rec["run_id"]

            loc_idx = str(run_id % len(LOCATIONS))
            weather = location_stats[loc_idx]

            row = {
                # ── Model inputs (performance targets + climate) ──────────
                "avg_Tin":         outputs["avg_Tin"],
                "min_Tin":         outputs["min_Tin"],
                "hours_below_5c":  outputs["hours_below_5c"],
                "hours_below_0c":  outputs["hours_below_0c"],
                "total_Q_heater":  outputs["total_Q_heater"],
                "avg_Tout":        weather["avg_Tout"],
                "min_Tout":        weather["min_Tout"],
                "avg_solar":       weather["avg_solar"],

                # ── Model outputs (design parameters to predict) ──────────
                "A_floor":         params["A_floor"],
                "V":               params["V"],
                "A_glass":         params["A_glass"],
                "A_mass":          params["A_mass"],
                "tau_glass":       params["tau_glass"],
                "U_day":           params["U_day"],
                "U_night":         params["U_night"],
                "thermal_mass_kg": params["thermal_mass_kg"],
                "ACH":             params["ACH"],
            }
            records.append(row)
        except (KeyError, TypeError):
            skipped += 1

    df = pd.DataFrame(records).dropna().reset_index(drop=True)
    print(f"Loaded {len(df)} records  ({skipped} skipped due to missing fields)")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 3 — DATASET
# Wraps numpy arrays in a PyTorch Dataset so DataLoader can batch them.
# ──────────────────────────────────────────────────────────────────────────────

class GreenhouseDataset(Dataset):
    def __init__(self, X: np.ndarray, Y: np.ndarray):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.Y = torch.tensor(Y, dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.Y[idx]


# ──────────────────────────────────────────────────────────────────────────────
# STEP 4 — MODEL
# Shared MLP backbone with two output heads:
#   head_low  → predicts the Q_LOW  (10th percentile) of each param
#   head_high → predicts the Q_HIGH (90th percentile) of each param
# ──────────────────────────────────────────────────────────────────────────────

class InverseDesignModel(nn.Module):
    def __init__(self, in_dim: int, out_dim: int, hidden_dims: list, dropout: float):
        super().__init__()

        # Build backbone layers
        layers = []
        prev_dim = in_dim
        for h in hidden_dims:
            layers += [
                nn.Linear(prev_dim, h),
                nn.BatchNorm1d(h),   # normalizes activations → faster, more stable training
                nn.ReLU(),
                nn.Dropout(dropout), # randomly zeros neurons → reduces overfitting
            ]
            prev_dim = h

        self.backbone  = nn.Sequential(*layers)
        self.head_low  = nn.Linear(prev_dim, out_dim)  # predicts lower bounds
        self.head_high = nn.Linear(prev_dim, out_dim)  # predicts upper bounds

    def forward(self, x):
        features = self.backbone(x)
        return self.head_low(features), self.head_high(features)


# ──────────────────────────────────────────────────────────────────────────────
# STEP 5 — QUANTILE LOSS
# Standard pinball/quantile loss. Forces pred_low to underestimate and
# pred_high to overestimate at the specified quantile level.
# This is what gives us honest ranges rather than just point estimates.
# ──────────────────────────────────────────────────────────────────────────────

def quantile_loss(pred: torch.Tensor, target: torch.Tensor, q: float) -> torch.Tensor:
    err = target - pred
    # If err > 0 (pred is too low):  penalize by q      (we want pred_low to be low)
    # If err < 0 (pred is too high): penalize by (1-q)  (we want pred_high to be high)
    return torch.mean(torch.where(err >= 0, q * err, (q - 1) * err))


# ──────────────────────────────────────────────────────────────────────────────
# STEP 6 — TRAINING LOOP
# ──────────────────────────────────────────────────────────────────────────────

def run_training(model, train_loader, val_loader, optimizer, epochs, patience):
    best_val_loss = float("inf")
    no_improve    = 0

    print(f"{'Epoch':>6}  {'Train Loss':>12}  {'Val Loss':>10}")
    print("─" * 35)

    for epoch in range(1, epochs + 1):
        # ── Training pass ────────────────────────────────────────────────────
        model.train()
        train_loss = 0.0
        for X_batch, Y_batch in train_loader:
            optimizer.zero_grad()
            pred_low, pred_high = model(X_batch)
            loss = (
                quantile_loss(pred_low,  Y_batch, Q_LOW) +
                quantile_loss(pred_high, Y_batch, Q_HIGH)
            )
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        train_loss /= len(train_loader)

        # ── Validation pass ──────────────────────────────────────────────────
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for X_batch, Y_batch in val_loader:
                pred_low, pred_high = model(X_batch)
                loss = (
                    quantile_loss(pred_low,  Y_batch, Q_LOW) +
                    quantile_loss(pred_high, Y_batch, Q_HIGH)
                )
                val_loss += loss.item()
        val_loss /= len(val_loader)

        # Print progress every 10 epochs
        if epoch % 10 == 0 or epoch == 1:
            print(f"{epoch:>6}  {train_loss:>12.5f}  {val_loss:>10.5f}")

        # ── Save best model + early stopping ─────────────────────────────────
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            no_improve    = 0
            torch.save(model.state_dict(), MODEL_OUT)
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"\n  Early stopping at epoch {epoch}.")
                break

    print(f"\n  Best validation loss: {best_val_loss:.5f}")
    print(f"  Model checkpoint saved → {MODEL_OUT}")
    return best_val_loss


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    print("\n" + "=" * 55)
    print("  Inverse Design Model — Training")
    print("=" * 55 + "\n")

    # ── Load and prepare data ─────────────────────────────────────────────────
    location_stats = get_location_stats()
    df = load_data(DB_PATH, location_stats)

    X_raw = df[INPUT_COLS].values.astype(np.float32)
    Y_raw = df[OUTPUT_COLS].values.astype(np.float32)

    # Normalize inputs and outputs to zero mean, unit variance.
    # This is critical — thermal_mass_kg is in the tens of thousands while
    # tau_glass is between 0 and 1. Without scaling, the loss would be
    # dominated entirely by the large-valued params.
    scaler_X = StandardScaler()
    scaler_Y = StandardScaler()
    X = scaler_X.fit_transform(X_raw)
    Y = scaler_Y.fit_transform(Y_raw)

    joblib.dump(scaler_X, SCALER_X_OUT)
    joblib.dump(scaler_Y, SCALER_Y_OUT)
    print(f"Scalers saved → {SCALER_X_OUT}, {SCALER_Y_OUT}\n")

    # ── Train / val / test split ──────────────────────────────────────────────
    dataset = GreenhouseDataset(X, Y)
    n       = len(dataset)
    n_train = int(0.70 * n)
    n_val   = int(0.15 * n)
    n_test  = n - n_train - n_val

    train_ds, val_ds, test_ds = random_split(
        dataset,
        [n_train, n_val, n_test],
        generator=torch.Generator().manual_seed(SEED),
    )

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False)

    print(f"Dataset split:  train={n_train}  val={n_val}  test={n_test}\n")

    # ── Build model and optimizer ─────────────────────────────────────────────
    model = InverseDesignModel(
        in_dim      = len(INPUT_COLS),
        out_dim     = len(OUTPUT_COLS),
        hidden_dims = HIDDEN_DIMS,
        dropout     = DROPOUT,
    )

    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model parameters: {total_params:,}\n")

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr           = LR,
        weight_decay = WEIGHT_DECAY,
    )

    # ── Train ─────────────────────────────────────────────────────────────────
    run_training(model, train_loader, val_loader, optimizer, EPOCHS, PATIENCE)

    # ── Final test evaluation ─────────────────────────────────────────────────
    model.load_state_dict(torch.load(MODEL_OUT))
    model.eval()
    test_loss = 0.0
    with torch.no_grad():
        for X_batch, Y_batch in test_loader:
            pred_low, pred_high = model(X_batch)
            loss = (
                quantile_loss(pred_low,  Y_batch, Q_LOW) +
                quantile_loss(pred_high, Y_batch, Q_HIGH)
            )
            test_loss += loss.item()
    test_loss /= len(test_loader)

    print(f"\n  Test loss:  {test_loss:.5f}")
    print("\n" + "=" * 55)
    print("  Done!")
    print("=" * 55 + "\n")


# ──────────────────────────────────────────────────────────────────────────────
# INFERENCE HELPER
# Import this function in your Flask/FastAPI backend to serve predictions.
#
# Example:
#   from train_inverse_model import predict
#   ranges = predict(avg_Tin=15, min_Tin=5, ..., avg_solar=180)
#   # → {"A_floor": (42.3, 89.1), "V": (98.0, 210.4), ...}
# ──────────────────────────────────────────────────────────────────────────────

def predict(
    avg_Tin:         float,
    min_Tin:         float,
    hours_below_5c:  float,
    hours_below_0c:  float,
    total_Q_heater:  float,
    avg_Tout:        float,
    min_Tout:        float,
    avg_solar:       float,
    model_path:      str = MODEL_OUT,
    scaler_x_path:   str = SCALER_X_OUT,
    scaler_y_path:   str = SCALER_Y_OUT,
) -> dict:
    """
    Run inference and return recommended design parameter ranges.

    Returns:
        {
            "A_floor":         (low, high),
            "V":               (low, high),
            "A_glass":         (low, high),
            "A_mass":          (low, high),
            "tau_glass":       (low, high),
            "U_day":           (low, high),
            "U_night":         (low, high),
            "thermal_mass_kg": (low, high),
            "ACH":             (low, high),
        }
    """
    scaler_X = joblib.load(scaler_x_path)
    scaler_Y = joblib.load(scaler_y_path)

    model = InverseDesignModel(
        in_dim      = len(INPUT_COLS),
        out_dim     = len(OUTPUT_COLS),
        hidden_dims = HIDDEN_DIMS,
        dropout     = DROPOUT,
    )
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    x_raw = np.array([[
        avg_Tin, min_Tin, hours_below_5c, hours_below_0c,
        total_Q_heater, avg_Tout, min_Tout, avg_solar,
    ]], dtype=np.float32)

    x = torch.tensor(scaler_X.transform(x_raw), dtype=torch.float32)

    with torch.no_grad():
        pred_low_scaled, pred_high_scaled = model(x)

    low  = scaler_Y.inverse_transform(pred_low_scaled.numpy())[0]
    high = scaler_Y.inverse_transform(pred_high_scaled.numpy())[0]

    return {
        col: (round(float(lo), 2), round(float(hi), 2))
        for col, lo, hi in zip(OUTPUT_COLS, low, high)
    }


if __name__ == "__main__":
    main()
