# These values should be remained UNCHANGED unless necessary.
# We will also include preset values here i.e. density and heat capacity for materials.

DEFAULT_LOCATION = "Chicago"

#DEFAULT_GHI = 150
SOLAR_RADIATION = 4000
GREENHOUSE_AREA = 393
TRANSMISSION_EFFICIENCY=0.6
#SOLAR_GAIN = SOLAR_RADIATION * GREENHOUSE_AREA * TRANSMISSION_EFFICIENCY # Fix this
SOLAR_GAIN = None

# Previous group defined heating power (W)
WATER_CIRCULATION_HEATING = 7000
THERMAL_ROCK_BED_STORAGE = 7000
EFFICIENCY = 0.8
HEATING_POWER = (WATER_CIRCULATION_HEATING + THERMAL_ROCK_BED_STORAGE) * EFFICIENCY 

### MATERIAL PRESETS ###
# density recorded in kg/m^3
# heat capacity recorded in J/(kg*K)

ETFE_R = 0.51
TEFLON_R = 0.0118
POLYETHYLENE_R = 0.63
MYLAR_R = 0.00155

# CONCRETE
CONCRETE_DENSITY = 2300 # "normal" concrete
CONCRETE_HEAT_CAPACITY = 1000