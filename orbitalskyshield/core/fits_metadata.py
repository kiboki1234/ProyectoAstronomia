# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study

"""
FITS metadata extraction utilities.

Extracts observational parameters from FITS headers needed for
physical sky brightness modeling.
"""

import numpy as np
from typing import Dict, Optional
from datetime import datetime
from astropy.io import fits
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, get_sun, get_moon
import astropy.units as u

from ..core.logging import get_logger

logger = get_logger()


def extract_observation_metadata(fits_path: str) -> Dict:
    """
    Extract relevant metadata from FITS header.
    
    Attempts to extract:
    - Observation datetime
    - Observer location (lat, lon, altitude)
    - Pointing direction (RA, Dec, Alt, Az)
    - Exposure time
    - Filter
    - Airmass
    
    Args:
        fits_path: Path to FITS file
    
    Returns:
        Dictionary with extracted metadata
    """
    with fits.open(fits_path) as hdul:
        header = hdul[0].header
        
        metadata = {}
        
        # Datetime
        metadata['date_obs'] = header.get('DATE-OBS', None)
        if metadata['date_obs']:
            try:
                metadata['datetime'] = Time(metadata['date_obs']).datetime
            except:
                metadata['datetime'] = None
        else:
            metadata['datetime'] = None
        
        # Observer location
        metadata['site_lat'] = header.get('SITELAT', header.get('LATITUDE', None))
        metadata['site_lon'] = header.get('SITELONG', header.get('LONGITUD', None))
        metadata['site_elev'] = header.get('SITEELEV', header.get('ELEVATIO', 0.0))
        
        # Pointing
        metadata['ra'] = header.get('RA', header.get('OBJCTRA', None))
        metadata['dec'] = header.get('DEC', header.get('OBJCTDEC', None))
        metadata['azimuth'] = header.get('AZIMUTH', header.get('AZ', None))
        metadata['altitude'] = header.get('ALTITUDE', header.get('ALT', None))
        
        # Zenith distance (if not  in header, calculate from altitude)
        if metadata['altitude'] is not None:
            metadata['zenith_distance'] = 90.0 - float(metadata['altitude'])
        else:
            metadata['zenith_distance'] = None
        
        # Airmass
        metadata['airmass'] = header.get('AIRMASS', None)
        if metadata['airmass'] is None and metadata['zenith_distance'] is not None:
            # Calculate airmass from zenith distance (simple secant formula)
            z_rad = np.radians(metadata['zenith_distance'])
            if z_rad < np.radians(70):
                metadata['airmass'] = 1.0 / np.cos(z_rad)
            else:
                metadata['airmass'] = None
        
        # Exposure
        metadata['exptime'] = header.get('EXPTIME', header.get('EXPOSURE', None))
        
        # Filter
        metadata['filter'] = header.get('FILTER', header.get('FILTNAM', 'Unknown'))
        
    return metadata


def calculate_zenith_distance(
    fits_path: str,
    default_lat: float = 0.0,
    default_lon: float = 0.0
) -> Optional[float]:
    """
    Calculate zenith distance from FITS header or use pointing center.
    
    Args:
        fits_path: Path to FITS file
        default_lat: Default latitude if not in header
        default_lon: Default longitude if not in header
    
    Returns:
        Zenith distance in degrees, or None if cannot be determined
    """
    metadata = extract_observation_metadata(fits_path)
    
    # If directly in header
    if metadata['zenith_distance'] is not None:
        return metadata['zenith_distance']
    
    # Try to calculate from RA/Dec
    if metadata['datetime'] and metadata['ra'] and metadata['dec']:
        try:
            obs_time = Time(metadata['datetime'])
            site_lat = metadata['site_lat'] if metadata['site_lat'] else default_lat
            site_lon = metadata['site_lon'] if metadata['site_lon'] else default_lon
            site_elev = metadata['site_elev'] if metadata['site_elev'] else 0.0
            
            location = EarthLocation(
                lat=site_lat*u.deg,
                lon=site_lon*u.deg,
                height=site_elev*u.m
            )
            
            altaz_frame = AltAz(obstime=obs_time, location=location)
            
            # Convert RA/Dec to Alt/Az
            # Note: This is simplified, actual implementation would need proper coordinate object
            # For now, return None and rely on header values
            logger.warning("RA/Dec to Alt/Az conversion not fully implemented, using header values")
            return None
            
        except Exception as e:
            logger.error(f"Failed to calculate zenith distance: {e}")
            return None
    
    # Default to zenith if all else fails
    logger.warning("Could not determine zenith distance, defaulting to 0 (zenith)")
    return 0.0


def get_observation_context(fits_path: str) -> Dict:
    """
    Get complete observational context for physical modeling.
    
    This is the main function to use for extracting all parameters
    needed by physical_model.natural_sky_brightness()
    
    Args:
        fits_path: Path to FITS file
    
    Returns:
        Dictionary with all parameters, with sensible defaults
    """
    metadata = extract_observation_metadata(fits_path)
    
    context = {
        'date': metadata.get('datetime'),
        'observer_lat': metadata.get('site_lat', 0.0),  # Default to equator
        'observer_lon': metadata.get('site_lon', 0.0),
        'altitude_m': metadata.get('site_elev', 0.0),
        'zenith_distance': metadata.get('zenith_distance', 0.0),
        'airmass': metadata.get('airmass', 1.0),
        'filter': metadata.get('filter', 'Unknown'),
        'exptime': metadata.get('exptime', 0.0),
        'has_metadata': any([
            metadata.get('datetime'),
            metadata.get('site_lat'),
            metadata.get('zenith_distance')
        ])
    }
    
    return context
