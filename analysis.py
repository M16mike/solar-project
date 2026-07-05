import pandas as pd
import pvlib
from pvlib.pvsystem import PVSystem, Array, FixedMount
from pvlib.modelchain import ModelChain
from pvlib.location import Location

print("Initializing upgraded solar economic simulator...")

# --- CONFIGURABLE INPUTS ---
SYSTEM_PANEL_COUNT = 10     # Number of panels on the roof
ELECTRICITY_COST_KWH = 0.45 # Cost of electricity per kWh in USD (or local currency equivalent)
SYSTEM_INSTALL_COST = 3500  # Total upfront cost to buy and install the system
# ---------------------------

# 1. Define Location (Accra, Ghana)
latitude, longitude, tz, altitude = 5.65, -0.18, 'Africa/Accra', 65
site_location = Location(latitude, longitude, tz=tz, altitude=altitude, name='Accra Site')

# 2. Fetch Weather Data
print("Fetching weather data from online servers...")
try:
    # FIX: Explicitly extract the DataFrame (the first item in the tuple) and metadata
    pvgis_outputs = pvlib.iotools.get_pvgis_tmy(latitude, longitude, map_variables=True)
    weather_df = pvgis_outputs[0]  # Grab just the weather DataFrame out of the tuple
    
    # Force clean 2026 data timestamps to align with the model parameters
    weather_df.index = pd.date_range(start='2026-01-01 00:00', end='2026-12-31 23:00', freq='h', tz=tz)
    print("Weather data successfully downloaded!")
except Exception as e:
    print(f"Error fetching weather data: {e}")
    exit()

# 3. Import Hardware Specs
sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
cec_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
module_specs = sandia_modules['Canadian_Solar_CS6X_300M__2013_']
inverter_specs = cec_inverters['ABB__MICRO_0_25_I_OUTD_US_208__208V_']

# 4. Construct Scaled System Architecture
mount = FixedMount(surface_tilt=5.65, surface_azimuth=180)
# We multiply the single panel output metrics by our array size count using modules_per_string
array = Array(mount=mount, module_parameters=module_specs, modules_per_string=SYSTEM_PANEL_COUNT, temperature_model_parameters=pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass'])
system = PVSystem(arrays=[array], inverter_parameters=inverter_specs)

# 5. Execute Simulation
print("Calculating physics engine and scaled yields...")
mc = ModelChain(system, site_location, spectral_model='no_loss', losses_model='no_loss')
mc.run_model(weather_df)

# 6. Financial Analysis Calculations
total_system_annual_kwh = mc.results.ac.sum() / 1000
annual_savings = total_system_annual_kwh * ELECTRICITY_COST_KWH
payback_period = SYSTEM_INSTALL_COST / annual_savings if annual_savings > 0 else 0

# 7. Print Comprehensive Report
print("\n=============================================")
print("          SOLAR SYSTEM SYSTEM REPORT         ")
print("=============================================")
print(f" Total Array Size:        {SYSTEM_PANEL_COUNT} Panels ({SYSTEM_PANEL_COUNT * 0.3:.1f} kW)")
print(f" Annual Energy Production: {total_system_annual_kwh:,.2f} kWh")
print(f" Estimated Annual Savings: ${annual_savings:,.2f}")
print(f" Upfront System Cost:      ${SYSTEM_INSTALL_COST:,.2f}")
print(f" Break-Even Payback Time:  {payback_period:.1f} Years")
print("=============================================")
