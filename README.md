# Proyecto Astronomía - OrbitalSkyShield

> **Open-source detection and mitigation of satellite streaks in astronomical imaging**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 What is OrbitalSkyShield?

OrbitalSkyShield is a scientific tool for:
1. **Detecting satellite streaks** in astronomical images (FITS/JPEG)
2. **Estimating ODC (Orbital Diffuse Contribution)** - the light pollution from satellites
3. **Validating detectors** against ground truth data

### Key Features (v0.2)

- ✅ **AdaptiveDetector** with **87.45% precision** on real data
- ✅ **Physical Sky Brightness Model** (Krisciunas & Schaefer 1991)
- ✅ **Scientific Validation System** with IoU, Precision, Recall metrics
- ✅ **FITS-native processing** with metadata extraction
- ✅ **Bootstrap confidence intervals** for uncertainty quantification

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/ProyectoAstronomia.git
cd ProyectoAstronomia

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install
pip install -e .
pip install ephem tqdm pillow  # Additional dependencies
```

### Basic Usage

```bash
# Process FITS images
python -m orbitalskyshield.cli.main run \
  --input-dir data/fits_dataset \
  --output-dir results/analysis
```

**Output:**
- `results/analysis/masks/*.fits` - Streak masks
- `results/analysis/quality/*.json` - Frame metrics  
- `results/analysis/odc_report.json` - ODC estimate

### Validate Detector

```bash
python scripts/validate_detector.py \
  --dataset-dir data/real_data/StreaksYoloDataset/test \
  --output-dir results/validation \
  --detector adaptive
```

---

## 📊 Performance

Evaluated on **StreaksYoloDataset** (225 labeled astronomical images):

| Detector | Precision | Recall | IoU | Status |
|----------|-----------|--------|-----|--------|
| **AdaptiveDetector** | **87.45%** | 3.36% | 0.045 | ✅ Best |
| BaselineDetector | 0% | 0% | 0.28 | ❌ Failed |

**Interpretation:**
- **High precision (87%)** → Few false positives (reliable when it detects)
- **Low recall (3%)** → Misses faint streaks (ML detector planned for v1.0)

---

## 🔬 Scientific Innovation

### Physical ODC Model

Unlike existing tools, OrbitalSkyShield calculates ODC as a **residual** from physical models:

```
ODC = Observed Sky - (Lunar + Rayleigh + Twilight)
```

**Implementation:**
- **Lunar brightness**: Krisciunas & Schaefer (1991) model
- **Atmospheric scattering**: Rayleigh + altitude correction
- **Astronomical calculations**: PyEphem for moon/sun positions

**Result:** First open-source tool to provide **physically-motivated ODC estimates**

---

## 📁 Project Structure

```
ProyectoAstronomia/
├── orbitalskyshield/           # Main package
│   ├── streak_detection/       # Detector implementations
│   │   ├── baseline_detector.py
│   │   └── improved_detector.py  # AdaptiveDetector
│   ├── validation/             # Ground truth evaluation
│   │   └── metrics.py
│   ├── skyglow/                # ODC estimation
│   │   ├── physical_model.py   # NEW: Physical sky brightness
│   │   └── odc_estimator.py    # Enhanced with physical model
│   ├── core/                   # Core utilities
│   │   ├── fits_metadata.py    # NEW: Metadata extraction
│   │   ├── io_fits.py
│   │   └── types.py
│   └── cli/                    # Command-line interface
├── scripts/                    # Utility scripts
│   └── validate_detector.py    # NEW: Validation script
├── data/                       # Datasets
│   ├── fits_dataset/           # 2,387 FITS files
│   └── real_data/StreaksYoloDataset/  # Labeled images
├── results/                    # Analysis outputs
└── docs/                       # Documentation
    └── user_guide_v0.2.md      # NEW: Complete guide
```

---

## 📖 Documentation

- **[User Guide v0.2](docs/user_guide_v0.2.md)** - Complete usage documentation
- **[Validation Results](results/validation_summary.md)** - Detector performance analysis
- **[Implementation Plan](docs/implementation_plan.md)** - Roadmap through v2.0

---

## 🛣️ Roadmap

### ✅ v0.1 (MVP) - December 2025
- Basic Hough Transform detector
- Simple percentile ODC estimation
- CLI interface

### ✅ v0.2 (Current) - December 2025
- AdaptiveDetector (87.45% precision)
- Physical sky brightness model
- Scientific validation system

### 🔜 v1.0 - Q2 2026
- ML detector (YOLO/U-Net) - target: IoU > 0.85
- Image inpainting/cleaning
- TLE satellite catalog integration
- Web dashboard

### 🔮 v2.0 - Q4 2026
- Multi-wavelength support
- Temporal analysis
- Global database
- Citizen science platform

---

## 🤝 Contributing

Contributions welcome! Areas needing help:

1. **Improve recall** - Better detection of faint streaks
2. **ML detector training** - YOLO/U-Net implementation
3. **Photometric calibration** - Gaia DR3 cross-matching
4. **Documentation** - Tutorials, examples
5. **Testing** - More validation datasets

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📚 Scientific Background

### Key References

1. **Krisciunas & Schaefer (1991)** - Lunar sky brightness model  
   *PASP, 103, 1033-1039*

2. **Rawls et al. (2020)** - Satellite constellation impact  
   *arXiv:2003.07446*

3. **Walker (1988)** - Sky brightness surveys  
   *PASP, 100, 496-503*

### Datasets Used

- **StreaksYoloDataset** - 225 labeled astronomical images
- **Custom FITS collection** - 2,387 frames for ODC analysis

---

## 🎯 Use Cases

### For Observatories
- Automatically flag contaminated frames
- Quantify satellite impact on observations
- Generate reports for time allocation committees

### For Researchers
- Study long-term trends in sky brightness
- Correlate with satellite launches
- Publish ODC measurements

### For Policy
- Provide quantitative data for light pollution regulations
- Monitor compliance with dark sky preservation

---

## 📊 Example Results

### Detection Example

![Detection Example](results_preview.png)

### ODC Report Sample

```json
{
  "physical_model": {
    "odc_percent_flux": 12.3,
    "moon_altitude": 35.2,
    "moon_phase_angle": 85.3
  },
  "odc_percent": 7.8,
  "odc_ci95": [4.1, 11.9]
}
```

**Interpretation:** 12.3% increase in sky brightness likely due to satellites, with moon at 35° altitude.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 📧 Contact

- **Issues:** [GitHub Issues](https://github.com/yourusername/ProyectoAstronomia/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/ProyectoAstronomia/discussions)
- **Email:** your.email@example.com

---

## 🙏 Acknowledgments

- **StreaksYoloDataset** creators
- **PyEphem** (astr computational calculations)
- **Astropy Project** (FITS I/O)
- **Scikit-image** (image processing)

---

## Citation

```bibtex
@software{orbitalskyshield2025,
  title = {OrbitalSkyShield: Detection and Mitigation of Satellite Streaks},
  author = {Your Name},
  year = {2025},
  version = {0.2.0},
  url = {https://github.com/yourusername/ProyectoAstronomia}
}
```

---

**Made with ❤️ for Dark Skies**
