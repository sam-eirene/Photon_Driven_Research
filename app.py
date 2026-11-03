import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from photon_vgsc import (
    optical_attenuation, temperature_rise_lumped, simulate_hh,
    photon_energy_joule, load_experimental_csv
)

st.set_page_config(page_title="Photon-VGSC Research Studio", layout="wide")
st.title("Photon-VGSC Research Studio")
st.caption("Computational feasibility prototype | Not a validated mosquito-control device")

st.warning(
    "Scientific limitation: photon-driven modulation of Anopheles VGSCs is an unverified "
    "hypothesis. The optical model is simplified, and the electrophysiology module uses "
    "generic classical Hodgkin–Huxley parameters rather than measured mosquito-channel data. "
    "Simulated output must not be interpreted as evidence of mosquito control."
)

tab1, tab2, tab3, tab4 = st.tabs([
    "Photon transport", "Thermal estimate", "Baseline electrophysiology", "Data analysis"
])

with tab1:
    st.subheader("Simplified Beer–Lambert optical attenuation")
    c1, c2 = st.columns(2)
    wavelength = c1.slider("Wavelength (nm)", 300, 1000, 550)
    irradiance = c2.number_input("Incident irradiance (W/m²)", min_value=0.0, value=10.0)
    depth_mm = c1.number_input("Path depth (mm)", min_value=0.0, value=1.0)
    mu = c2.number_input("Absorption coefficient (m⁻¹)", min_value=0.0, value=100.0)
    result = optical_attenuation(wavelength, irradiance, depth_mm / 1000, mu)
    a, b, c = st.columns(3)
    a.metric("Photon energy", f"{result['photon_energy_j']:.3e} J")
    b.metric("Transmitted irradiance", f"{result['transmitted_irradiance_w_m2']:.4g} W/m²")
    c.metric("Absorbed fraction", f"{100*result['absorbed_fraction']:.2f}%")
    z_mm = np.linspace(0, max(depth_mm, 0.001), 150)
    transmitted = irradiance * np.exp(-mu * z_mm / 1000)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=z_mm, y=transmitted, mode="lines", name="Transmitted irradiance"))
    fig.update_layout(xaxis_title="Depth (mm)", yaxis_title="Irradiance (W/m²)")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Homogeneous non-scattering medium assumption; not a mosquito body optical model.")

with tab2:
    st.subheader("Lumped temperature-rise estimate")
    st.write("This idealised energy-balance calculation ignores spatial gradients and detailed cooling.")
    c1, c2, c3 = st.columns(3)
    absorbed = c1.number_input("Absorbed irradiance (W/m²)", min_value=0.0, value=1.0)
    exposure = c2.number_input("Exposure duration (s)", min_value=0.0, value=1.0)
    thickness = c3.number_input("Absorbing thickness (mm)", min_value=0.01, value=1.0)
    c4, c5, c6 = st.columns(3)
    density = c4.number_input("Density (kg/m³)", min_value=1.0, value=1000.0)
    heat_capacity = c5.number_input("Specific heat (J/kg/K)", min_value=1.0, value=4000.0)
    loss_pct = c6.slider("Fraction of energy lost", 0, 100, 0)
    delta = temperature_rise_lumped(absorbed, exposure, thickness/1000, density,
                                    heat_capacity, loss_pct/100)
    st.metric("Estimated ΔT", f"{delta:.6g} °C")
    st.caption("A first-order estimate only; it is not a safety assessment or a validated bioheat model.")

with tab3:
    st.subheader("Baseline generic Hodgkin–Huxley electrophysiology")
    c1, c2, c3 = st.columns(3)
    duration = c1.slider("Duration (ms)", 10, 100, 30)
    current = c2.slider("Stimulus current (µA/cm²)", 0.0, 30.0, 10.0)
    dt = c3.select_slider("Time step (ms)", options=[0.01, 0.025, 0.05, 0.1], value=0.025)
    sim = simulate_hh(duration_ms=float(duration), dt_ms=float(dt),
                      stimulus_uA_cm2=float(current))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sim["time_ms"], y=sim["voltage_mV"], name="Membrane voltage"))
    fig.update_layout(xaxis_title="Time (ms)", yaxis_title="Voltage (mV)")
    st.plotly_chart(fig, use_container_width=True)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=sim["time_ms"], y=sim["ina_uA_cm2"], name="Sodium current"))
    fig2.update_layout(xaxis_title="Time (ms)", yaxis_title="Sodium current (µA/cm²)")
    st.plotly_chart(fig2, use_container_width=True)
    st.info(sim["note"] + " A validated mosquito channel model requires species-specific experimental parameters.")

with tab4:
    st.subheader("Explore experimental or synthetic CSV data")
    st.write("Upload a CSV containing measurements. Example columns: sample_id, condition, time_s, current_pA, temperature_C.")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded:
        try:
            df = load_experimental_csv(uploaded)
            st.write("Rows:", len(df), "| Columns:", len(df.columns))
            st.dataframe(df.head(100), use_container_width=True)
            numeric = df.select_dtypes(include=np.number).columns.tolist()
            if numeric:
                xcol = st.selectbox("X-axis", numeric, index=0)
                ycol = st.selectbox("Y-axis", numeric, index=min(1, len(numeric)-1))
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df[xcol], y=df[ycol], mode="markers", name="Observations"))
                fig.update_layout(xaxis_title=xcol, yaxis_title=ycol)
                st.plotly_chart(fig, use_container_width=True)
            st.download_button("Download cleaned copy", df.to_csv(index=False).encode("utf-8"),
                               "experimental_data_copy.csv", "text/csv")
        except Exception as exc:
            st.error(f"Could not read CSV: {exc}")
    else:
        st.write("No experimental data loaded. You can create a clearly labelled synthetic test file:")
        demo = pd.DataFrame({
            "sample_id": [f"S{i:02d}" for i in range(1, 11)],
            "condition": ["control"]*5 + ["exposure_candidate"]*5,
            "time_s": [0, 10, 20, 30, 40]*2,
            "current_pA_simulated": [1.0, 1.1, 0.9, 1.05, 0.95, 1.02, 1.08, 0.98, 1.04, 0.96],
        })
        st.dataframe(demo, use_container_width=True)
        st.download_button("Download synthetic example CSV", demo.to_csv(index=False).encode("utf-8"),
                           "synthetic_example_not_real_data.csv", "text/csv")

st.divider()
st.markdown("**Next research stage:** validate the optical assumptions, obtain mosquito-specific channel parameters from reliable literature or laboratory recordings, preregister the analysis plan, and test mechanisms with qualified collaborators.")
