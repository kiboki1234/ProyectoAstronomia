# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study


import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.visualization import ZScaleInterval

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orbitalskyshield.streak_detection.improved_detector import AdaptiveDetector

def save_evidence(filename, output_name, title_suffix):
    fits_path = os.path.join(r"d:\proyectosPersonales\ProyectoAstronomia\data\fits_dataset", filename)
    output_dir = "docs/figures"
    
    if not os.path.exists(fits_path):
        print(f"File {filename} not found.")
        return

    # Load Data
    with fits.open(fits_path) as hdul:
        data = hdul[0].data
        if data is None and len(hdul) > 1:
            data = hdul[1].data
    
    # Run Detector
    detector = AdaptiveDetector(percentile_thresh=97.0, min_streak_length=30)
    data = np.nan_to_num(data.astype(float))
    result = detector.detect(data)
    
    # Prepare Plot
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    
    # Original Image (ZScale for better visibility of faint stars/streaks)
    interval = ZScaleInterval()
    vmin, vmax = interval.get_limits(data)
    
    axes[0].imshow(data, cmap='gray', vmin=vmin, vmax=vmax, origin='lower')
    axes[0].set_title(f"Original Image: {filename}", fontsize=14)
    axes[0].axis('off')
    
    # Detected Mask Overlay
    axes[1].imshow(data, cmap='gray', vmin=vmin, vmax=vmax, origin='lower')
    # Create red overlay for mask
    mask_overlay = np.zeros((*data.shape, 4))
    mask_overlay[result.mask > 0] = [1, 0, 0, 0.5] # Red, 50% opacity
    
    axes[1].imshow(mask_overlay, origin='lower')
    axes[1].set_title(f"Detection: {result.meta['detected_lines']} Streaks ({title_suffix})", fontsize=14)
    axes[1].axis('off')
    
    plt.tight_layout()
    save_path = os.path.join(output_dir, output_name)
    plt.savefig(save_path, dpi=200)
    plt.close()
    print(f"Saved evidence to {save_path}")

def run_all():
    # 1. Extreme Case
    save_evidence("1167.fits", "evidence_extreme_1167.png", "Extreme Contamination")
    
    # 2. High Case
    save_evidence("1636.fits", "evidence_high_1636.png", "High Density")
    
    # 3. Typical Case
    save_evidence("0.fits", "evidence_typical_0.png", "Typical Streak")

if __name__ == "__main__":
    run_all()
