# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study


import os
from astropy.io import fits
import sys

def check_header(filepath):
    try:
        with fits.open(filepath) as hdul:
            header = hdul[0].header
            print(f"Checking {filepath}...")
            
            # List of keywords we care about for ODC
            keywords = ['DATE-OBS', 'DATE', 'MJD-OBS', 'LATITUDE', 'LONGITUDE', 'SITELAT', 'SITELONG', 'RA', 'DEC', 'EXPTIME']
            
            found_any = False
            for key in keywords:
                if key in header:
                    print(f"  [FOUND] {key}: {header[key]}")
                    found_any = True
                else:
                    # Check for partial matches
                   pass
            
            if not found_any:
                print("  [WARNING] No standard time/location keywords found.")
            
            print("  Dumping ALL Header Keys:")
            for key in header.keys():
                print(f"    {key} = {header[key]}")

    except Exception as e:
        print(f"Error reading {filepath}: {e}")

if __name__ == "__main__":
    target_file = r"d:\proyectosPersonales\ProyectoAstronomia\data\fits_dataset\13.fits"
    if os.path.exists(target_file):
        check_header(target_file)
    else:
        print(f"File not found: {target_file}")
