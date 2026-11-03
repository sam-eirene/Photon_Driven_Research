# Photon-VGSC Research Studio

A computational research prototype for investigating a proposed relationship between optical exposure and voltage-gated sodium-channel (VGSC) function.

## Scientific scope and limitations

- The Beer-Lambert module is a simplified homogeneous, non-scattering optical model.
- The temperature module is a lumped energy-balance estimate, not a validated bioheat model.
- The electrophysiology module uses generic classical Hodgkin-Huxley-style parameters. These are **not mosquito-specific VGSC measurements**.
- There is no photon-to-channel coupling term because a credible, validated mechanism and parameters have not yet been established.
- No output establishes mosquito mortality, reduced biting, or vector-control effectiveness.

## Installation (Windows / Anaconda)

```bash
conda create -n photonvgsc python=3.11 -y
conda activate photonvgsc
python -m pip install -r requirements.txt
streamlit run app.py
```

The browser will open the research dashboard. If it does not, use the local URL printed in the terminal.

## Run tests

```bash
pytest -q
```

## Files

- `app.py`: Streamlit graphical interface
- `photon_vgsc.py`: numerical functions and baseline electrophysiology model
- `tests/test_photon_vgsc.py`: basic automated tests
- `requirements.txt`: dependencies

## Suggested scientific workflow

1. Validate optical parameters for the actual experimental geometry and material.
2. Review evidence for candidate light-sensitive molecules or other intermediaries.
3. Obtain species- and channel-specific data from published sources or approved experiments.
4. Fit and validate the channel model against independent electrophysiology data.
5. Predefine controls for heating, handling, light-only behavioural responses and measurement artefacts.
6. Only pursue mosquito-response experiments after the channel-level results justify them and appropriate approvals are obtained.
7. Label simulated, published and newly collected experimental data distinctly.
