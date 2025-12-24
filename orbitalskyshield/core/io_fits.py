import os
import numpy as np
from astropy.io import fits
from .types import FrameData
from .logging import get_logger
from typing import Optional

logger = get_logger()

def read_fits(path: str) -> FrameData:
    """
    Reads a FITS file and returns a FrameData object.
    
    Args:
        path: Absolute path to the FITS file.
        
    Returns:
        FrameData object containing data, header, and metadata.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the file is not a valid FITS file.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    try:
        with fits.open(path) as hdul:
            # Assuming the science image is in the primary HDU or the first extension if primary is empty
            # This logic mimics common astronomical packages
            hdu = hdul[0]
            if hdu.data is None and len(hdul) > 1:
                hdu = hdul[1]
            
            if hdu.data is None:
                 raise ValueError(f"No image data found in FITS file: {path}")

            data = hdu.data.astype(float) # Ensure float for processing
            header = hdu.header.copy() # Copy header to avoid closed file issues
            
            # Extract timestamp if available
            timestamp = header.get("DATE-OBS") or header.get("DATE")
            
            return FrameData(
                data=data,
                header=header,
                path=path,
                timestamp_utc=str(timestamp) if timestamp else None
            )
            
    except Exception as e:
        logger.error(f"Error reading FITS file {path}: {e}")
        raise

def write_fits(path: str, data: np.ndarray, header: Optional[fits.Header] = None, overwrite: bool = True) -> None:
    """
    Writes data to a FITS file.
    
    Args:
        path: Output path.
        data: Image data.
        header: Optional header to write.
        overwrite: Overwrite existing file.
    """
    handoff_header = header.copy() if header else fits.Header()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    
    hdu = fits.PrimaryHDU(data=data, header=handoff_header)
    try:
        hdu.writeto(path, overwrite=overwrite)
        logger.info(f"Saved FITS to {path}")
    except Exception as e:
        logger.error(f"Failed to write FITS to {path}: {e}")
        raise
