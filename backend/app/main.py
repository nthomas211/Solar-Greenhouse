import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import matplotlib.pyplot as plt
from app.consts import *
from app.formulas import *
from app.utils.fetch_weather import fetch_weather

# Constants
SOLAR_GAIN = SOLAR_RADIATION * GREENHOUSE_AREA * TRANSMISSION_EFFICIENCY  # W
# HEATING_POWER = 0 #200  # W
THERMAL_MASS = 193370  # J/K
U_DAY = 3.0  # W/m^2-K
U_NIGHT = 1.19  # W/m^2-K
AREA = GREENHOUSE_AREA  # m^2 (assuming area for heat loss calculation)


def calculate_hourly_temperatures(weather_data, heating_power, mat_toggle):
    temperatures = []
    T_internal = None
    for _, row in weather_data.iterrows():
        timestamp = row["timestamp"]

        T_external = row["temp"]

        if T_internal is None:
           T_internal = T_external

        hour = timestamp.hour
        #is_daytime = row["is_daytime"]
        is_daytime = 6 <= hour < 18
        # add the angle of sun to greenhouse
        solar_gain = SOLAR_GAIN * np.sin(np.pi * (hour - 6) / 12) if is_daytime else 0

        if is_daytime:
            T_internal = daytime_temp(T_external, solar_gain, THERMAL_MASS, U_DAY, AREA, T_internal)
        else:
            Q_thermal = heating_power
            U_value_toggle = U_NIGHT if mat_toggle else U_DAY # U_DAY represents without the mat
            T_internal = nighttime_temp(T_internal, Q_thermal, U_value_toggle, AREA, T_external, THERMAL_MASS)

        temperatures.append((timestamp, T_internal, T_external, is_daytime))

    return pd.DataFrame(temperatures,
                        columns=['Timestamp', 'Internal Temperature (°C)', 'External Temperature (°C)', 'Is Daytime'])


'''
def celsius_to_fahrenheit(df):
    df['Internal Temperature (°F)'] = df['Internal Temperature (°C)'] * 9/5 + 32
    df['External Temperature (°F)'] = df['External Temperature (°C)'] * 9/5 + 32
    return df


def main():
    city = str(input("Enter city name: "))
    start_date = "2025-03-30"
    end_date = "2025-04-1"
    initial_temp = 20

    weather_df = fetch_weather(city, start_date, end_date)
    # weather_df = parse_weather_data(weather_data)

    print("Running Sim...")
    hourly_temps = calculate_hourly_temperatures(weather_df)
    hourly_temps = celsius_to_fahrenheit(hourly_temps)

    # Plot the results with data points
    plt.figure(figsize=(10, 5))

    # Shade night times
    for i in range(len(hourly_temps) - 1):
        if not hourly_temps.iloc[i]['Is Daytime']:
            plt.axvspan(hourly_temps.iloc[i]['Timestamp'], hourly_temps.iloc[i + 1]['Timestamp'],
                        color='gray', alpha=0.3)

    plt.plot(hourly_temps["Timestamp"], hourly_temps["Internal Temperature (°F)"], label="Internal Temp (°F)",
             color="r", marker="o")
    plt.plot(hourly_temps["Timestamp"], hourly_temps["External Temperature (°F)"], label="External Temp (°F)",
             color="b", marker="x")

    plt.xlabel("Time")
    plt.ylabel("Temperature (°F)")
    plt.title("Internal and External Temperature Over Time (°F)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid()

    # Format x-axis with time labels
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))

    # Add data labels to each tick
    for x, y in zip(hourly_temps["Timestamp"], hourly_temps["Internal Temperature (°F)"]):
        plt.text(x, y + 0.5, f"{y:.1f}", ha="right", va="bottom", fontsize=8, color="black")
    for x, y in zip(hourly_temps["Timestamp"], hourly_temps["External Temperature (°F)"]):
        plt.text(x, y - 0.5, f"{y:.1f}", ha="left", va="top", fontsize=8, color="blue")

    plt.show()

# create a graph of minimum nighttime temperature between the solstices of the greenhouse
# X axis day, Y axis minimum nighttime temperature September 21 - March 21 per night

if __name__ == "__main__":
    main()
'''
