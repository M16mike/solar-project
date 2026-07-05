import pandas as pd
import pvlib
from pvlib.pvsystem import PVSystem, Array, FixedMount
from pvlib.modelchain import ModelChain
from pvlib.location import Location

print("Initializing solar simulator...")

# 1. Define Location (Accra, Ghana)
latitude, longitude, tz, altitude = 5.65, -0.18, 'Africa/Accra', 65
site_location = Location(latitude, longitude, tz=tz, altitude=altitude, name='Accra Site')

# 2. Fetch Weather Data via PVGIS API
print("Fetching weather data from online servers... (this may take a moment)")
try:
    pvgis_data = pvlib.iotools.get_pvgis_tmy(latitude, longitude, map_variables=True)
    weather_df = pvgis_data[0]  # FIX: Correctly extract the DataFrame from the API package
    
    # Force clean 2026 data timestamps to align with the model parameters
    weather_df.index = pd.date_range(start='2026-01-01 00:00', end='2026-12-31 23:00', freq='h', tz=tz)
    print("Weather data successfully downloaded!")
except Exception as e:
    print(f"Error fetching weather data: {e}")
    exit()

# 3. Import Solar Panel and Inverter Specifications
print("Loading hardware profiles...")
sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
cec_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
module_specs = sandia_modules['Canadian_Solar_CS6X_300M__2013_']
inverter_specs = cec_inverters['ABB__MICRO_0_25_I_OUTD_US_208__208V_']

# 4. Construct System Architecture
mount = FixedMount(surface_tilt=5.65, surface_azimuth=180)
array = Array(mount=mount, module_parameters=module_specs, temperature_model_parameters=pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass'])
system = PVSystem(arrays=[array], inverter_parameters=inverter_specs)


# 5. Execute Simulation
print("Calculating physics engine and energy yields...")
mc = ModelChain(system, site_location, spectral_model='no_loss', losses_model='no_loss')
mc.run_model(weather_df)

# 6. Print Results
total_annual_kwh = mc.results.ac.sum() / 1000
print("\n=== SIMULATION RESULTS ===")
print(f"Total Predicted Annual Energy Yield: {total_annual_kwh:,.2f} kWh")
print("===========================")
