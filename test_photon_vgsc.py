import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import pytest
from photon_vgsc import photon_energy_joule, optical_attenuation, temperature_rise_lumped, simulate_hh


def test_photon_energy_decreases_with_wavelength():
    assert photon_energy_joule(400) > photon_energy_joule(800)


def test_no_absorption_means_no_attenuation():
    out = optical_attenuation(550, 5.0, 0.01, 0.0)
    assert out["transmitted_irradiance_w_m2"] == pytest.approx(5.0)
    assert out["absorbed_fraction"] == pytest.approx(0.0)


def test_temperature_rise_nonnegative():
    rise = temperature_rise_lumped(2.0, 5.0, 0.001, 1000.0, 4000.0)
    assert rise >= 0


def test_hh_simulation_outputs_finite_values():
    out = simulate_hh(duration_ms=15, dt_ms=0.05)
    assert len(out["time_ms"]) == len(out["voltage_mV"])
    assert np.isfinite(out["voltage_mV"]).all()
    assert np.isfinite(out["ina_uA_cm2"]).all()
