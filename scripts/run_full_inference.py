# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study


import os
import glob
import time
import csv
import sys
import numpy as np
from datetime import datetime
from astropy.io import fits

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orbitalskyshield.streak_detection.improved_detector import AdaptiveDetector
from orbitalskyshield.core.logging import get_logger

logger = get_logger()

def load_fits_data(filepath):
    """Simple FITS loader avoiding astropy caching issues"""
    try:
        with fits.open(filepath) as hdul:
            data = hdul[0].data
            # Handle if data is in extension
            if data is None and len(hdul) > 1:
                data = hdul[1].data
            return data
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def run_full_inference():
    fits_dir = r"d:\proyectosPersonales\ProyectoAstronomia\data\fits_dataset"
    output_csv = "inference_results.csv"
    
    print(f"=== OrbitalSkyShield Full Inference Run ===")
    print(f"Input Directory: {fits_dir}")
    print(f"Output CSV: {output_csv}")
    
    # 1. Gather files
    fits_files = glob.glob(os.path.join(fits_dir, "*.fits"))
    if not fits_files:
        print("No FITS files found.")
        return

    total_files = len(fits_files)
    print(f"Found {total_files} files to process.")
    
    # 2. Initialize Detector
    detector = AdaptiveDetector(percentile_thresh=97.0, min_streak_length=30)
    
    # 3. Process Loop
    results = []
    start_time_total = time.time()
    
    print("Starting processing... (This may take a few minutes)")
    
    with open(output_csv, 'w', newline='') as csvfile:
        fieldnames = ['filename', 'detected_streaks', 'proc_time_ms', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, fpath in enumerate(fits_files):
            fname = os.path.basename(fpath)
            t0 = time.time()
            status = "OK"
            streaks = 0
            
            try:
                # Load
                img_data = load_fits_data(fpath)
                
                if img_data is None:
                    status = "LOAD_ERROR"
                else:
                    # Detect
                    # Ensure float and handle NaNs if any
                    img_data = img_data.astype(float)
                    img_data = np.nan_to_num(img_data)
                    
                    res = detector.detect(img_data)
                    streaks = res.meta.get('detected_lines', 0)
                    
            except Exception as e:
                status = f"ERROR: {str(e)}"
                print(f"Failed on {fname}: {e}")
            
            t1 = time.time()
            dt_ms = (t1 - t0) * 1000.0
            
            # Log to CSV immediately
            row = {
                'filename': fname,
                'detected_streaks': streaks,
                'proc_time_ms': f"{dt_ms:.2f}",
                'status': status
            }
            writer.writerow(row)
            results.append(row)
            
            # Progress print every 50 files or 10%
            if (i+1) % 50 == 0 or (i+1) == total_files:
                avg_time = (time.time() - start_time_total) / (i+1)
                remaining = (total_files - (i+1)) * avg_time
                print(f"[{i+1}/{total_files}] Processed. Last: {str(dt_ms)[:5]}ms. Found {streaks} streaks. (ETA: {remaining:.1f}s)")

    # 4. Summary
    total_time = time.time() - start_time_total
    total_streaks = sum(r['detected_streaks'] for r in results)
    ok_files = sum(1 for r in results if r['status'] == 'OK')
    
    print("\n" + "="*40)
    print(f"INFERENCE COMPLETE")
    print(f"Total Files: {total_files}")
    print(f"Successful:  {ok_files}")
    print(f"Total Streaks Detected: {total_streaks}")
    print(f"Total Time:  {total_time:.2f}s ({total_time/total_files*1000:.2f} ms/file avg)")
    print("="*40)

if __name__ == "__main__":
    run_full_inference()
