import streamlit as st
import pandas as pd
import pvlib
from pvlib.pvsystem import PVSystem, Array, FixedMount
from pvlib.modelchain import ModelChain
from pvlib.location import Location

# Set up browser page options
st.set_page_config(page_title="Solar Yield Engine", page_icon="☀️", layout="centered")

st.title("☀️ Solar Yield & Economic Analyzer")
st.markdown("Adjust the variables below to recalculate system performance in real-time.")

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.header("🔧 System Configurations")
panel_count = st.sidebar.slider("Number of Solar Panels", min_value=1, max_value=50, value=10)
install_cost = st.sidebar.number_input("Total Installation Cost ($)", min_value=500, max_value=50000, value=3500, step=500)
elec_cost = st.sidebar.slider("Electricity Rate ($/kWh)", min_value=0.05, max_value=1.00, value=0.45, step=0.01)

# 1. Location Settings (Accra, Ghana)
latitude, longitude, tz, altitude = 5.65, -0.18, 'Africa/Accra', 65
site_location = Location(latitude, longitude, tz=tz, altitude=altitude)

# 2. Compute Operations
@st.cache_data
def run_solar_simulation():
    pvgis_outputs = pvlib.iotools.get_pvgis_tmy(latitude, longitude, map_variables=True)
    df = pvgis_outputs
    df.index = pd.date_range(start='2026-01-01 00:00', end='2026-12-31 23:00', freq='h', tz=tz)
    return df

try:
    weather_df = run_solar_simulation()
    
    # Hardware specs
    sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
    cec_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
    module_specs = sandia_modules['Canadian_Solar_CS6X_300M__2013_']
    inverter_specs = cec_inverters['ABB__MICRO_0_25_I_OUTD_US_208__208V_']

    # Model Assembly
    mount = FixedMount(surface_tilt=5.65, surface_azimuth=180)
    array = Array(mount=mount, module_parameters=module_specs, modules_per_string=panel_count, temperature_model_parameters=pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass'])
    system = PVSystem(arrays=[array], inverter_parameters=inverter_specs)

    # Calculate
    mc = ModelChain(system, site_location, spectral_model='no_loss', losses_model='no_loss')
    mc.run_model(weather_df)

    # Metrics Calculations
    total_kwh = mc.results.ac.sum() / 1000
    annual_savings = total_kwh * elec_cost
    payback = install_cost / annual_savings if annual_savings > 0 else 0

    # --- DISPLAY METRICS DASHBOARD ---
    col1, col2, col3 = st.columns(3)
    col1.metric("System Capacity", f"{panel_count * 0.3:.1f} kW", f"{panel_count} Panels")
    col2.metric("Annual Generation", f"{total_kwh:,.1f} kWh")
    col3.metric("Payback Period", f"{payback:.1f} Years")

    st.success(f"💰 Financial Return: This configuration saves **${annual_savings:,.2f}** per year!")

    # Plot monthly data
    st.subheader("📊 Estimated Monthly Output Profiles")
    hourly_ac = mc.results.ac
    monthly_energy = hourly_ac.groupby(hourly_ac.index.month).sum() / 1000
    st.bar_chart(monthly_energy)

except Exception as e:
    st.error(f"Engine Exception Error: {e}")
