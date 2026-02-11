import argparse
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import os
from simulation.model import simulate_greenhouse
from simulation.weather import get_weather

def run_simulation(config_path: str):
    with open(config_path, "r") as f:
        config = json.load(f)

    location = config.get("location", {"lat": 39.9, "lon": 116.4})
    start_date = config.get("start_date", "2025-11-01")
    end_date = config.get("end_date", "2025-11-02")
    params = config.get("parameters", {})

    print(f"[{datetime.now().isoformat()}] Running local simulation...")
    print(f"Location: {location}")
    print(f"Dates: {start_date} → {end_date}")

    # Ensure output directory exists regardless of how the script is invoked.
    os.makedirs("results", exist_ok=True)

    weather_df = get_weather(location, start_date, end_date)
    if weather_df is None or weather_df.empty:
        print(
            "\n⚠️  No weather data was returned. "
            "This usually means the Open-Meteo request failed (no internet, API outage, bad dates/location).\n"
            "The simulation will not run without weather inputs.\n"
        )

    result_df = simulate_greenhouse(weather_df, params)

    print(f"Simulation complete — {len(result_df)} hours simulated.")
    if result_df is None or result_df.empty or "Tin" not in result_df.columns:
        # Save an empty CSV with headers so users still get a file they can inspect.
        out_csv = f"results/{config.get('name', 'test_run')}_results.csv"
        (result_df if result_df is not None else pd.DataFrame()).to_csv(out_csv, index=False)
        print(f"Results saved to {out_csv}")
        print("Nothing to plot (no simulation rows). Exiting.")
        return

    print(f"Internal T range: {result_df['Tin'].min():.2f}–{result_df['Tin'].max():.2f} °C")

    out_csv = f"results/{config.get('name', 'test_run')}_results.csv"
    result_df.to_csv(out_csv, index=False)
    print(f"Results saved to {out_csv}")
    reference_df = None
    try:
        # Try a couple common locations for reference data (repo root and worker/data).
        ref_candidates = [
            os.path.join(os.path.dirname(__file__), "data", "reference_greenhouse_temps.csv"),
            os.path.join(os.path.dirname(__file__), "..", "data", "reference_greenhouse_temps.csv"),
        ]
        ref_path = next((p for p in ref_candidates if os.path.exists(p)), None)
        if ref_path:
            reference_df = pd.read_csv(ref_path)
            reference_df['datetime'] = pd.to_datetime(reference_df['datetime'])
            reference_df = reference_df[
                (reference_df['datetime'] >= pd.to_datetime(start_date)) &
                (reference_df['datetime'] <= pd.to_datetime(end_date))
            ]
            if len(reference_df) > 0:
                print(f"Loaded {len(reference_df)} reference data points for comparison")
    except Exception as e:
        print(f"Could not load reference data: {e}")

    plt.figure(figsize=(14,7))
    plt.plot(result_df['datetime'], result_df['Tin'], label='Simulated Air (Tin)', color='tab:red', linewidth=2, alpha=0.8)
    plt.plot(result_df['datetime'], result_df['T_mass'], label='Thermal Mass (T_mass)', color='tab:orange', linewidth=1.5, alpha=0.6)
    plt.plot(result_df['datetime'], result_df['Tout'], label='External (Tout)', color='tab:green', linewidth=1.5, alpha=0.6)
    
    if reference_df is not None and len(reference_df) > 0:
        plt.plot(reference_df['datetime'], reference_df['Tin_typical'], 
                label='Reference Typical', color='tab:purple', linewidth=2, 
                linestyle=':', marker='o', markersize=4, alpha=0.7)
        plt.fill_between(reference_df['datetime'], 
                        reference_df['Tin_min'], 
                        reference_df['Tin_max'],
                        alpha=0.15, 
                        color='tab:purple',
                        label='Reference Range (min-max)')
    
    setpoint = params.get('setpoint')
    if setpoint is not None:
        plt.axhline(y=setpoint, color='tab:blue', linestyle='--', linewidth=2, 
                   label=f'Threshold ({setpoint}°C)', alpha=0.7)
        
        below_threshold = result_df['Tin'] < setpoint
        if below_threshold.any():
            plt.fill_between(result_df['datetime'], 
                            result_df['Tin'], 
                            setpoint,
                            where=below_threshold,
                            alpha=0.3, 
                            color='tab:blue',
                            label='Heating Required')
    
    plt.xlabel("Datetime", fontsize=12)
    plt.ylabel("Temperature (°C)", fontsize=12)
    plt.title("Greenhouse Internal Temperatures - Simulation vs Reference", fontsize=14, fontweight='bold')
    plt.legend(loc='best', fontsize=9)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('results/plot.png', dpi=150)
    print(f"Plot saved to results/plot.png")
    
    if reference_df is not None and len(reference_df) > 0:
        comparison = pd.merge(
            result_df[['datetime', 'Tin']].rename(columns={'Tin': 'Tin_sim'}), 
            reference_df[['datetime', 'Tin_typical']], 
            on='datetime', 
            how='inner'
        )
        if len(comparison) > 0:
            diff = comparison['Tin_sim'] - comparison['Tin_typical']
            mae = diff.abs().mean()
            rmse = (diff ** 2).mean() ** 0.5
            print(f"\n--- Comparison with Reference Data ---")
            print(f"Mean Absolute Error (MAE): {mae:.2f}°C")
            print(f"Root Mean Square Error (RMSE): {rmse:.2f}°C")
            print(f"Mean Temperature Difference: {diff.mean():.2f}°C")
            print(f"Simulated Range: {comparison['Tin_sim'].min():.1f}–{comparison['Tin_sim'].max():.1f}°C")
            print(f"Reference Range: {comparison['Tin_typical'].min():.1f}–{comparison['Tin_typical'].max():.1f}°C")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run greenhouse simulation")
    parser.add_argument("--config", default="configs/default.json", help="Path to JSON config file")
    args = parser.parse_args()

    run_simulation(args.config)