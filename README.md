# Daily Macro Dashboard

A Streamlit application to visualize and log your daily macronutrient intake.

## Features
- Dynamic food database driven by `data/foods.yaml`
- Interactive dashboard with transparent background
- Manually save your daily intake to a CSV log (one entry per day)
- "Trends" tab to visualize macros over time

## Installation
This project requires **Python 3.10–3.11**. Install the latest

dependencies in editable mode with:
```bash
pip install -e .
```
Newer Python versions may fail to install due to upstream dependencies.

## Usage
After installing in editable mode, launch the dashboard with the convenience
command:

```bash
macro-manager
```

The same behaviour is available via `python -m macro_manager` if you prefer.

## License
This project is licensed under the MIT License. See `LICENSE` for details.
