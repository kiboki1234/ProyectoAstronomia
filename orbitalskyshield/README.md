# OrbitalSkyShield

**Satellite Streak Detection & Correction for Astronomy**

OrbitalSkyShield is an open-source tool designed to detect and mitigate satellite streaks in FITS images and estimate the Orbital Diffuse Contribution (ODC) to sky background.

## Features
- **Streak Detection**: Baseline algorithm using Hough Transform.
- **Metrics**: Per-frame severity scores and nightly aggregation.
- **Skyglow Estimation**: MVP estimation of ODC using robust background modeling.
- **Synthetic Data**: Built-in generator for testing.

## Installation

```bash
pip install -e .
```

## Quick Start

1. **Generate Synthetic Data**
   ```bash
   python -m orbitalskyshield.cli.main generate-synthetic --output-dir ./data/test_data --count 5
   ```

2. **Run Pipeline**
   ```bash
   python -m orbitalskyshield.cli.main run --input-dir ./data/test_data --output-dir ./data/output --verbose
   ```

3. **Check Results**
   Output will be in `./data/output`:
   - `masks/*.fits`: Binary masks of detected streaks.
   - `quality/*.json`: JSON reports for each frame.
   - `night_summary.json`: Aggregated statistics.
   - `odc_report.json`: Orbital Diffuse Contribution report.

## Configuration
See `config/default_config.yaml` for parameters.
