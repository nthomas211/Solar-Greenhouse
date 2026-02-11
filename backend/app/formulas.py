These formulas have been defined from the previous group
# This file writes them as python function fron the equations
# so that we can use them for the simulation against real time
# temperatures. 

import numpy as np

def daytime_temp(T_external, solar_gain, thermal_mass, U_value, area, T_internal_prev):
    heat_loss = U_value * area * (T_external - T_internal_prev)
    T_internal = T_external + (solar_gain - heat_loss) / thermal_mass
    return T_internal

# t_int(prev_hour_temp) + ((Q_thermal - Q_loss)/total_thermal_mass)
def nighttime_temp(T_internal_prev, Q_thermal, U_value, area, T_external, thermal_mass, dt=3600):
    """Approximates nighttime internal temperature using a single-step heat transfer equation."""
    Q_loss = U_value * area * (T_internal_prev - T_external)  # Heat loss in watts
    dT = (-Q_loss + Q_thermal) * dt / thermal_mass  # Temperature change over dt seconds
    return T_internal_prev + dT  # Update temperature


#def solar_gain_func(solar_gain, hour):
#    return solar_gain * np.sin(np.pi * (hour - 6) / 12) # mimics angle of sun

def thermal_mass_calculation(V_volume_layer, P_density, C_heat_capacity):
    return V_volume_layer * P_density * C_heat_capacity

# https://www.solarenergylocal.com/states/illinois/chicago/ to calculate solar gain i think
