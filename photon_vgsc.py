"""Core numerical models for Photon-VGSC Research Studio.

Research prototype only. Optical and electrophysiology parameters are illustrative.
The model does NOT establish that photons modulate mosquito VGSCs.
"""
from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp

PLANCK = 6.62607015e-34
LIGHT_SPEED = 299_792_458.0
BOLTZMANN = 1.380649e-23


def photon_energy_joule(wavelength_nm: float) -> float:
    """Energy per photon (J), using E = h*c/lambda."""
    if wavelength_nm <= 0:
        raise ValueError("Wavelength must be positive.")
    return PLANCK * LIGHT_SPEED / (wavelength_nm * 1e-9)


def optical_attenuation(wavelength_nm: float, irradiance_w_m2: float,
                        depth_m: float, absorption_coefficient_m1: float) -> dict:
    """Beer-Lambert attenuation in a homogeneous, non-scattering medium.

    This is a simplified optical approximation, not a mosquito anatomical model.
    """
    if wavelength_nm <= 0 or irradiance_w_m2 < 0 or depth_m < 0 or absorption_coefficient_m1 < 0:
        raise ValueError("Wavelength must be positive; other inputs cannot be negative.")
    transmitted = irradiance_w_m2 * np.exp(-absorption_coefficient_m1 * depth_m)
    absorbed = irradiance_w_m2 - transmitted
    energy = photon_energy_joule(wavelength_nm)
    return {
        "photon_energy_j": energy,
        "incident_photon_flux_m2_s": irradiance_w_m2 / energy,
        "transmitted_irradiance_w_m2": float(transmitted),
        "absorbed_irradiance_w_m2": float(absorbed),
        "absorbed_fraction": float(1 - np.exp(-absorption_coefficient_m1 * depth_m)),
    }


def temperature_rise_lumped(absorbed_irradiance_w_m2: float, exposure_s: float,
                             illuminated_thickness_m: float, density_kg_m3: float,
                             heat_capacity_j_kg_k: float, heat_loss_fraction: float = 0.0) -> float:
    """Adiabatic/lumped estimate of temperature rise with optional fractional loss.

    Assumes uniform absorption over the specified thickness. This is not a
    substitute for a validated bioheat or heat-transfer model.
    """
    if min(absorbed_irradiance_w_m2, exposure_s, illuminated_thickness_m,
           density_kg_m3, heat_capacity_j_kg_k) < 0:
        raise ValueError("Physical inputs cannot be negative.")
    if illuminated_thickness_m == 0 or density_kg_m3 == 0 or heat_capacity_j_kg_k == 0:
        raise ValueError("Thickness, density and heat capacity must be positive.")
    if not 0 <= heat_loss_fraction <= 1:
        raise ValueError("heat_loss_fraction must be between 0 and 1.")
    energy_per_area = absorbed_irradiance_w_m2 * exposure_s * (1 - heat_loss_fraction)
    mass_per_area = density_kg_m3 * illuminated_thickness_m
    return energy_per_area / (mass_per_area * heat_capacity_j_kg_k)


@dataclass
class ChannelParameters:
    """Illustrative generic Hodgkin-Huxley-style sodium current parameters."""
    g_na_mS_cm2: float = 120.0
    e_na_mV: float = 50.0
    cm_uF_cm2: float = 1.0
    g_leak_mS_cm2: float = 0.3
    e_leak_mV: float = -54.4
    g_k_mS_cm2: float = 36.0
    e_k_mV: float = -77.0


def _rates(v):
    """Classical HH rate functions; numerical safeguards handle removable singularities."""
    x = v + 40.0
    alpha_m = np.where(np.abs(x) < 1e-7, 1.0, 0.1 * x / (1 - np.exp(-x / 10.0)))
    x = v + 55.0
    alpha_n = np.where(np.abs(x) < 1e-7, 0.1, 0.01 * x / (1 - np.exp(-x / 10.0)))
    alpha_h = 0.07 * np.exp(-(v + 65.0) / 20.0)
    beta_m = 4.0 * np.exp(-(v + 65.0) / 18.0)
    beta_h = 1.0 / (1 + np.exp(-(v + 35.0) / 10.0))
    beta_n = 0.125 * np.exp(-(v + 65.0) / 80.0)
    return alpha_m, beta_m, alpha_h, beta_h, alpha_n, beta_n


def simulate_hh(duration_ms: float = 30.0, dt_ms: float = 0.025,
                stimulus_uA_cm2: float = 10.0, stimulus_start_ms: float = 5.0,
                stimulus_end_ms: float = 10.0,
                params: ChannelParameters | None = None) -> dict:
    """Simulate a baseline HH neuron with sodium, potassium and leak currents.

    Generic classical HH parameters are NOT fitted to Anopheles VGSC data.
    No photon effect is built into this model.
    """
    if duration_ms <= 0 or dt_ms <= 0:
        raise ValueError("Duration and time step must be positive.")
    if not (0 <= stimulus_start_ms <= stimulus_end_ms <= duration_ms):
        raise ValueError("Stimulus times must be within simulation duration.")
    p = params or ChannelParameters()
    t = np.arange(0, duration_ms + dt_ms / 2, dt_ms)

    def rhs(time, y):
        v, m, h, n = y
        am, bm, ah, bh, an, bn = _rates(v)
        ina = p.g_na_mS_cm2 * (m**3) * h * (v - p.e_na_mV)
        ik = p.g_k_mS_cm2 * (n**4) * (v - p.e_k_mV)
        il = p.g_leak_mS_cm2 * (v - p.e_leak_mV)
        i_stim = stimulus_uA_cm2 if stimulus_start_ms <= time <= stimulus_end_ms else 0.0
        return [
            (i_stim - ina - ik - il) / p.cm_uF_cm2,
            am * (1-m) - bm*m,
            ah * (1-h) - bh*h,
            an * (1-n) - bn*n,
        ]

    v0 = -65.0
    am, bm, ah, bh, an, bn = _rates(v0)
    y0 = [v0, am/(am+bm), ah/(ah+bh), an/(an+bn)]
    sol = solve_ivp(rhs, (0, duration_ms), y0, t_eval=t, max_step=dt_ms,
                    rtol=1e-6, atol=1e-8)
    if not sol.success:
        raise RuntimeError(sol.message)
    v, m, h, n = sol.y
    ina = p.g_na_mS_cm2 * m**3 * h * (v - p.e_na_mV)
    return {"time_ms": sol.t, "voltage_mV": v, "m": m, "h": h, "n": n,
            "ina_uA_cm2": ina,
            "note": "Generic HH baseline; not mosquito-specific and not photon-modulated."}


def load_experimental_csv(file) :
    """Load user-supplied data. Does not infer causal effects."""
    import pandas as pd
    df = pd.read_csv(file)
    if df.empty:
        raise ValueError("The CSV file contains no rows.")
    return df
