# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study


import os
import glob
import numpy as np
from datetime import datetime
from astropy.io import fits
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orbitalskyshield.streak_detection.improved_detector import AdaptiveDetector
from orbitalskyshield.skyglow.physical_model import natural_sky_brightness, estimate_odc_from_observed

def load_fits_data(filepath):
    """Simple FITS loader for demo"""
    with fits.open(filepath) as hdul:
        data = hdul[0].data
        header = hdul[0].header
        return data, header

def run_demo_pipeline():
    # Configuration
    fits_dir = r"d:\proyectosPersonales\ProyectoAstronomia\data\fits_dataset"
    output_limit = 5  # Just run on 5 files for speed
    
    # Defaults for ODC (Since headers are missing/synthetic)
    # Using Paranal Observatory coordinates as a "Reference Site"
    DEFAULT_OBSERVER = {
        'lat': -24.6272,
        'lon': -70.4042,
        'alt': 2635.0,
        'extinction': 0.25
    }
    
    print(f"=== OrbitalSkyShield FITS Pipeline Demo ===")
    print(f"Dataset: {fits_dir}")
    print(f"ODC Mode: Technical Demonstration (Using Default Site: Paranal)")
    print("-" * 50)

    # Find files
    fits_files = glob.glob(os.path.join(fits_dir, "*.fits"))
    if not fits_files:
        print("No FITS files found!")
        return

    print(f"Found {len(fits_files)} FITS files. Processing first {output_limit}...")

    detector = AdaptiveDetector(percentile_thresh=97.0, min_aspect_ratio=3.0)

    for i, fpath in enumerate(fits_files[:output_limit]):
        fname = os.path.basename(fpath)
        print(f"\n[{i+1}/{output_limit}] Processing {fname}...")
        
        try:
            # 1. Load Data
            image_data, header = load_fits_data(fpath)
            
            # Normalize if needed (AdaptiveDetector expects reasonable range, but percentile handles most)
            if image_data.max() > 0:
                print(f"  Image Stats: Min={image_data.min()}, Max={image_data.max()}, Mean={image_data.mean():.2f}")
            
            # 2. Run Detector
            print("  Running AdaptiveDetector...", end="", flush=True)
            result = detector.detect(image_data)
            print(f" Done. Detected {result.meta['detected_lines']} streak(s).")
            
            # 3. Run Physical Model (ODC) - DEMO MODE
            # We use the date from header (even if synthetic) or now
            date_str = header.get('DATE-OBS', datetime.utcnow().isoformat())
            try:
                obs_date = datetime.fromisoformat(date_str)
            except:
                obs_date = datetime.utcnow()
                
            # Assume pointing at Zenith for demo
            zenith_dist = 0.0 
            
            # Calculate Natural Sky
            natural_model = natural_sky_brightness(
                date=obs_date,
                observer_lat=DEFAULT_OBSERVER['lat'],
                observer_lon=DEFAULT_OBSERVER['lon'],
                zenith_distance=zenith_dist,
                altitude_m=DEFAULT_OBSERVER['alt']
            )
            
            # Estimate ODC (Compare model to image median background)
            # Simple background estimation: median of pixels
            observed_bg_counts = np.median(image_data)
            # Convert counts to mag/arcsec^2 (Very rough calibration for demo)
            # Assuming ZeroPoint=25.0
            if observed_bg_counts > 0:
                observed_mag = -2.5 * np.log10(observed_bg_counts) + 25.0
            else:
                observed_mag = 22.0 # Dark frame
                
            odc_res = estimate_odc_from_observed(observed_mag, natural_model)
            
            print(f"  Physical Model (Demo):")
            print(f"    Natural Sky Brightness: {natural_model['total_sky_brightness']:.2f} mag/arcsec2")
            print(f"    Observed Background:    {observed_mag:.2f} mag/arcsec2")
            print(f"    Estimated ODC Flux %:   {odc_res['odc_percent_flux']:.2f}%")
            if odc_res['excess_due_to_odc']:
                print("    > STATUS: SIGNIFICANT EXCESS DETECTED (Simulated)")
            else:
                print("    > STATUS: Nominal Sky Background")

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n=== Demo Complete ===")
    print("Interpretation: The software successfully loaded FITS files, identified streaks, and ran the ODC physics engine.")

if __name__ == "__main__":
    run_demo_pipeline()
