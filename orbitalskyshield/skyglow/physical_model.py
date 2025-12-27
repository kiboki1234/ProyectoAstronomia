# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study

"""
Physical sky brightness model for natural sky background estimation.

This module implements models from astronomical literature to predict
natural sky brightness accounting for:
- Lunar illumination (Krisciunas & Schaefer 1991)
- Atmospheric scattering (Rayleigh/Mie)
- Airmass effects
- Twilight contribution

This allows ODC (Orbital Diffuse Contribution) to be calculated as
the residual between observed and modeled natural sky brightness.
"""

import numpy as np
from typing import Dict, Optional
from datetime import datetime
import ephem  # PyEphem for astronomical calculations

from ..core.logging import get_logger

logger = get_logger()


def lunar_phase_angle(date: datetime, observer_lat: float, observer_lon: float) -> float:
    """
    Calculate lunar phase angle for given date and location.
    
    Args:
        date: Observation datetime (UTC)
        observer_lat: Observer latitude (degrees)
        observer_lon: Observer longitude (degrees)
    
    Returns:
        Phase angle in degrees (0=new, 180=full)
    """
    obs = ephem.Observer()
    obs.lat = str(observer_lat)
    obs.lon = str(observer_lon)
    obs.date = date
    
    moon = ephem.Moon()
    moon.compute(obs)
    
    # Phase angle (0-180 degrees)
    phase_angle = float(moon.moon_phase) * 180.0
    return phase_angle


def lunar_altitude(date: datetime, observer_lat: float, observer_lon: float) -> float:
    """
    Calculate lunar altitude above horizon.
    
    Args:
        date: Observation datetime (UTC)
        observer_lat: Observer latitude (degrees)
        observer_lon: Observer longitude (degrees)
    
    Returns:
        Altitude in degrees (negative if below horizon)
    """
    obs = ephem.Observer()
    obs.lat = str(observer_lat)
    obs.lon = str(observer_lon)
    obs.date = date
    
    moon = ephem.Moon()
    moon.compute(obs)
    
    return np.degrees(float(moon.alt))


def sun_altitude(date: datetime, observer_lat: float, observer_lon: float) -> float:
    """
    Calculate solar altitude (for twilight contribution).
    
    Args:
        date: Observation datetime (UTC)
        observer_lat: Observer latitude (degrees)
        observer_lon: Observer longitude (degrees)
    
    Returns:
        Altitude in degrees (negative if below horizon)
    """
    obs = ephem.Observer()
    obs.lat = str(observer_lat)
    obs.lon = str(observer_lon)
    obs.date = date
    
    sun = ephem.Sun()
    sun.compute(obs)
    
    return np.degrees(float(sun.alt))


def krisciunas_schaefer_lunar_brightness(
    moon_altitude: float,
    moon_phase_angle: float,
    zenith_distance: float,
    extinction: float = 0.25
) -> float:
    """
    Calculate lunar sky brightness contribution.
    
    Based on Krisciunas & Schaefer (1991) model.
    
    Args:
        moon_altitude: Moon altitude in degrees
        moon_phase_angle: Moon phase angle (0=new, 180=full)
        zenith_distance: Zenith distance of observation point (degrees)
        extinction: Atmospheric extinction coefficient (mag/airmass)
    
    Returns:
        Sky brightness in mag/arcsec² (V-band equivalent)
    """
    if moon_altitude < -10:
        # Moon well below horizon, no contribution
        return 22.0  # Dark sky value
    
    # Convert to radians
    rho = np.radians(zenith_distance)
    alpha = np.radians(moon_phase_angle)
    h_moon = np.radians(moon_altitude)
    
    # Lunar illuminance function (Krisciunas & Schaefer eq. 20-21)
    I_star = 10**(-0.4 * (3.84 + 0.026 * np.abs(alpha) + 4e-9 * alpha**4))
    
    # Airmass for moon
    X_moon = 1.0 / (np.sin(h_moon) + 0.025 * np.exp(-11 * np.sin(h_moon)))
    
    # Scattering function
    f_rho = 10**5.36 * (1.06 + np.cos(rho)**2)
    
    # Moon brightness contribution
    B_moon = f_rho * I_star * 10**(-0.4 * extinction * X_moon) * (1 - 10**(-0.4 * extinction * 1/np.cos(rho)))
    
    # Convert to magnitude
    if B_moon > 0:
        m_moon = -2.5 * np.log10(B_moon) + 21.58  # Calibration constant
    else:
        m_moon = 22.0
    
    return m_moon


def rayleigh_scattering_brightness(
    zenith_distance: float,
    altitude_m: float = 2400.0
) -> float:
    """
    Calculate Rayleigh scattering contribution (natural airglow).
    
    Args:
        zenith_distance: Zenith distance in degrees
        altitude_m: Observatory altitude in meters
    
    Returns:
        Sky brightness in mag/arcsec²
    """
    # Airmass calculation
    z_rad = np.radians(zenith_distance)
    airmass = 1.0 / np.cos(z_rad) if z_rad < np.radians(70) else 5.0
    
    # Altitude correction (pressure reduces with altitude)
    pressure_ratio = np.exp(-altitude_m / 8000.0)  # Scale height ~8km
    
    # Rayleigh baseline at zenith (mag/arcsec²)
    # Typical dark site: ~22 mag/arcsec² at zenith
    rayleigh_zenith = 22.0
    
    # Airmass dependence (gets brighter near horizon)
    rayleigh_sky = rayleigh_zenith - 2.5 * np.log10(airmass * pressure_ratio)
    
    return rayleigh_sky


def twilight_brightness(sun_altitude: float) -> float:
    """
    Calculate twilight contribution to sky brightness.
    
    Args:
        sun_altitude: Sun altitude in degrees (negative = below horizon)
    
    Returns:
        Sky brightness in mag/arcsec² (very bright if sun is up)
    """
    if sun_altitude > -6:
        # Civil twilight or brighter
        return 10.0  # Very bright
    elif sun_altitude > -12:
        # Nautical twilight
        return 16.0
    elif sun_altitude > -18:
        # Astronomical twilight
        return 19.0
    else:
        # Dark sky
        return 22.0  # No twilight contribution


def natural_sky_brightness(
    date: datetime,
    observer_lat: float,
    observer_lon: float,
    zenith_distance: float,
    altitude_m: float = 2400.0,
    extinction: float = 0.25
) -> Dict[str, float]:
    """
    Calculate total natural sky brightness from all sources.
    
    This is the core function that combines all physical models.
    
    Args:
        date: Observation datetime (UTC)
        observer_lat: Observer latitude (degrees)
        observer_lon: Observer longitude (degrees)
        zenith_distance: Pointing zenith distance (degrees)
        altitude_m: Observatory altitude (meters above sea level)
        extinction: Atmospheric extinction coefficient
    
    Returns:
        Dictionary with components and total sky brightness
    """
    # Calculate celestial positions
    moon_alt = lunar_altitude(date, observer_lat, observer_lon)
    moon_phase = lunar_phase_angle(date, observer_lat, observer_lon)
    sun_alt = sun_altitude(date, observer_lat, observer_lon)
    
    # Individual components
    lunar_contrib = krisciunas_schaefer_lunar_brightness(
        moon_alt, moon_phase, zenith_distance, extinction
    )
    
    rayleigh_contrib = rayleigh_scattering_brightness(zenith_distance, altitude_m)
    
    twilight_contrib = twilight_brightness(sun_alt)
    
    # Combine contributions (in flux space, then convert to mag)
    # mag -> flux: flux = 10^(-0.4 * mag)
    flux_lunar = 10**(-0.4 * lunar_contrib)
    flux_rayleigh = 10**(-0.4 * rayleigh_contrib)
    flux_twilight = 10**(-0.4 * twilight_contrib)
    
    total_flux = flux_lunar + flux_rayleigh + flux_twilight
    
    # flux -> mag
    total_sky_brightness = -2.5 * np.log10(total_flux)
    
    return {
        'total_sky_brightness': float(total_sky_brightness),
        'lunar_component': float(lunar_contrib),
        'rayleigh_component': float(rayleigh_contrib),
        'twilight_component': float(twilight_contrib),
        'moon_altitude': float(moon_alt),
        'moon_phase_angle': float(moon_phase),
        'sun_altitude': float(sun_alt),
        'zenith_distance': float(zenith_distance),
        'model_version': 'v1.0_krisciunas_schaefer'
    }


def estimate_odc_from_observed(
    observed_sky_brightness: float,
    natural_model: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate ODC as residual between observed and modeled natural sky.
    
    Args:
        observed_sky_brightness: Measured sky brightness (mag/arcsec²)
        natural_model: Output from natural_sky_brightness()
    
    Returns:
        Dictionary with ODC estimate and metadata
    """
    natural_brightness = natural_model['total_sky_brightness']
    
    # ODC in magnitude difference
    # Positive value means observed is brighter than natural (contamination)
    odc_mag = natural_brightness - observed_sky_brightness
    
    # Convert to percentage flux increase
    # flux_observed / flux_natural = 10^(0.4 * odc_mag)
    flux_ratio = 10**(0.4 * odc_mag)
    odc_percent = (flux_ratio - 1.0) * 100.0
    
    return {
        'odc_magnitude_diff': float(odc_mag),
        'odc_percent_flux': float(odc_percent),
        'observed_brightness': float(observed_sky_brightness),
        'natural_brightness': float(natural_brightness),
        'excess_due_to_odc': odc_percent > 5.0,  # Flag significant contamination
        'model_components': natural_model
    }
