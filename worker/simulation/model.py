import pandas as pd
import numpy as np
from typing import Optional

RHO_AIR = 1.225
CP_AIR = 1005.0
SIGMA = 5.670374419e-8
LV = 2.45e6

def _sky_temperature_kelvin(T_out_C, cloud_factor=0.5):
    clear_sky_offset = 12.0
    cloudy_sky_offset = 3.0
    T_sky = T_out_C - (clear_sky_offset - (clear_sky_offset - cloudy_sky_offset) * cloud_factor)
    return T_sky + 273.15

def calculate_heat_to_threshold(T_air: float, T_mass: float, T_soil: float, 
                                 setpoint: Optional[float], C_air: float, C_mass: float, 
                                 C_soil: float, Tout: float, params: dict) -> float:

    if setpoint is None or T_air >= setpoint:
        return 0.0
    
    Q_air = C_air * max(0.0, setpoint - T_air)
    Q_mass = C_mass * max(0.0, setpoint - T_mass)
    Q_soil = C_soil * max(0.0, setpoint - T_soil)
    T_avg = (T_air + setpoint) / 2.0
    
    A_glass = params.get("A_glass", 50.0)
    U_day = params.get("U_day", 2.0)
    U_night = params.get("U_night", 0.25)
    hour = params.get("current_hour", 12)
    U_env = U_day if 6 <= hour <= 18 else U_night
    
    V = params.get("V", 100.0)
    ACH = params.get("ACH", 0.5)
    
    # Heat loss
    Q_loss_env = U_env * A_glass * (T_avg - Tout)
    
    # Ventilation heat loss
    m_dot = RHO_AIR * V * (ACH / 3600.0)
    Q_vent = m_dot * CP_AIR * (T_avg - Tout)
    
    heater_max_w = params.get("heater_max_w", 5000.0)
    if heater_max_w > 0:
        total_heat_needed = Q_air + Q_mass + Q_soil
        net_heating_power = heater_max_w - max(0, Q_loss_env + Q_vent)
        if net_heating_power > 0:
            estimated_time_s = total_heat_needed / net_heating_power
            Q_losses_during_heating = (Q_loss_env + Q_vent) * estimated_time_s
        else:
            Q_losses_during_heating = (Q_loss_env + Q_vent) * 3600.0
    else:
        Q_losses_during_heating = 0.0
    
    total_heat = Q_air + Q_mass + Q_soil + Q_losses_during_heating
    
    return max(0.0, total_heat)

def simulate_greenhouse(weather_df: pd.DataFrame, params: dict, dt=3600.0, substeps=60, T_bounds=(0, 50)):

    # Parameters & defaults
    A_glass = params.get("A_glass", 50.0)
    tau_glass = params.get("tau_glass", 0.85)
    U_day = params.get("U_day", 2.0)
    U_night = params.get("U_night", 0.25)
    ACH = params.get("ACH", 0.5)
    V = params.get("V", 100.0)
    A_floor = params.get("A_floor", 50.0)
    fraction_solar_to_air = params.get("fraction_solar_to_air", 0.5)
    cloud_factor = params.get("cloud_factor", 0.5)

    # Thermal mass
    mass_kg = params.get("thermal_mass_kg", 20000.0)
    cp_mass = params.get("cp_mass", 4186.0)
    C_mass = mass_kg * cp_mass

    soil_C_per_m2 = params.get("soil_C", 4e6)
    C_soil = soil_C_per_m2 * A_floor
    soil_U = params.get("soil_U", 0.5)

    heater_max_w = params.get("heater_max_w", 5000.0)
    evap_coeff = params.get("evap_coeff", 1e-8)

    # Initial temperatures (some point use weather from previous iteration? idk)
    T_air = float(params.get("T_init", 15.0))
    T_mass = float(params.get("T_mass_init", T_air))
    T_soil = float(params.get("T_soil_init", T_air))
    setpoint = params.get("setpoint", None)

    # Air properties
    rho_air = RHO_AIR
    cp_air = CP_AIR
    m_air = rho_air * V
    C_air = m_air * cp_air

    # Keep output schema consistent even if `weather_df` is empty.
    out_columns = [
        "datetime",
        "Tout",
        "Tin",
        "T_mass",
        "T_soil",
        "Q_heater",
        "Q_latent",
        "Q_to_threshold",
    ]

    out_rows = []

    for _, row in weather_df.iterrows():
        Tout = float(row.get("Tout", row.get("T_out", 0.0)))
        G = float(row.get("G", row.get("I", 0.0)))
        RH = float(row.get("RH", 0.5) or 0.5)
        hour = int(row["datetime"].hour) if "datetime" in row else 12

        if G > 100:
            U_env = U_day
        elif G < 10:
            U_env = U_night
        else:
            # Linear interpolation between U_night and U_day
            solar_factor = min(1.0, max(0.0, (G - 10) / 90))
            U_env = U_night + (U_day - U_night) * solar_factor
        
        dt_step = float(dt) / max(1, int(substeps))

        for _s in range(max(1, int(substeps))):
            # Solar gains
            Q_total_sw = G * A_glass * tau_glass
            Q_air_sw = Q_total_sw * fraction_solar_to_air
            Q_mass_sw = Q_total_sw * (1.0 - fraction_solar_to_air) * 0.6
            Q_soil_sw = Q_total_sw * (1.0 - fraction_solar_to_air) * 0.4

            # Heat losses
            Q_loss_env = U_env * A_glass * (T_air - Tout)
            m_dot = rho_air * V * (ACH / 3600.0)
            Q_vent = m_dot * cp_air * (T_air - Tout)

            # Longwave radiation
            T_air_K = np.clip(T_air + 273.15, 0, 1000)
            T_sky_K = np.clip(_sky_temperature_kelvin(Tout, cloud_factor), 0, 1000)
            emissivity = params.get("emissivity", 0.9)

            lw_scale = params.get("lw_radiation_scale", 0.7)
            Q_lw = lw_scale * emissivity * SIGMA * A_glass * (T_air_K**4 - T_sky_K**4)

            # Heat exchange with mass and soil
            h_am = params.get("h_am", 3.0)
            Q_am = h_am * params.get("A_mass", 20.0) * (T_mass - T_air)

            h_as = params.get("h_as", 1.0)
            Q_as = h_as * A_floor * (T_soil - T_air)

            # Latent heat (evaporation)
            T_air_safe = np.clip(T_air, -50, 50)
            es = 0.6108 * np.exp(17.27 * T_air_safe / (T_air_safe + 237.3))
            ea = RH * es
            VPD = max(es - ea, 0.0)
            evap_kg_m2_s = evap_coeff * VPD
            Q_lat = evap_kg_m2_s * LV * A_floor

            # Net heat flows
            Q_air_in = Q_air_sw + Q_am + Q_as - Q_loss_env - Q_vent - Q_lw - Q_lat
            Q_mass_in = Q_mass_sw - Q_am
            Q_soil_in = Q_soil_sw - Q_as - soil_U * A_floor * (T_soil - Tout)

            # Euler integration
            dT_air = (Q_air_in * dt_step) / C_air
            dT_mass = (Q_mass_in * dt_step) / C_mass
            dT_soil = (Q_soil_in * dt_step) / C_soil

            T_air += dT_air
            T_mass += dT_mass
            T_soil += dT_soil

            # --- Heater control (gradual) ---
            Q_heater = 0.0
            if setpoint is not None and T_air < setpoint:
                heating_rate_factor = params.get("heating_rate_factor", 0.4)
                power_needed = (setpoint - T_air) * (C_air + C_mass) * heating_rate_factor / dt_step
                Q_heater = np.clip(power_needed, 0, heater_max_w)
                T_air += (Q_heater * dt_step) / (C_air + C_mass)

            T_air = np.clip(T_air, *T_bounds)
            T_mass = np.clip(T_mass, *T_bounds)
            T_soil = np.clip(T_soil, *T_bounds)

        Q_to_threshold = 0.0
        if setpoint is not None and T_air < setpoint:
            calc_params = params.copy()
            calc_params["current_hour"] = hour
            Q_to_threshold = calculate_heat_to_threshold(
                T_air, T_mass, T_soil, setpoint, 
                C_air, C_mass, C_soil, Tout, calc_params
            )
        
        out_rows.append({
            "datetime": row["datetime"],
            "Tout": Tout,
            "Tin": T_air,
            "T_mass": T_mass,
            "T_soil": T_soil,
            "Q_heater": Q_heater,
            "Q_latent": Q_lat,
            "Q_to_threshold": Q_to_threshold,
        })

    if not out_rows:
        return pd.DataFrame(columns=out_columns)

    return pd.DataFrame(out_rows, columns=out_columns)