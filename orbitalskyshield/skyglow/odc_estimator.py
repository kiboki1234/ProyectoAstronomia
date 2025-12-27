from typing import List, Dict, Any, Tuple
import numpy as np
from ..core.types import FrameData, MaskData
from ..core.logging import get_logger

logger = get_logger()

def estimate_background_robust(image: np.ndarray, mask: np.ndarray) -> float:
    """
    Estimates background level using masked median.
    """
    if mask is None:
        valid_pixels = image
    else:
        valid_pixels = image[mask == 0]
    
    if valid_pixels.size == 0:
        return np.nan
        
    return float(np.median(valid_pixels))

class ODCEstimator:
    def __init__(self, bootstrap_samples: int = 100, use_physical_model: bool = True):
        self.bootstrap_samples = bootstrap_samples
        self.use_physical_model = use_physical_model

    def estimate(self, frames: List[FrameData], masks: List[MaskData]) -> Dict[str, Any]:
        """
        Estimates the Orbital Diffuse Contribution (ODC) for a set of frames.
        
        Enhanced version uses physical sky brightness model when metadata available.
        Falls back to simple percentile method if no metadata.
        
        Args:
            frames: List of FrameData objects
            masks: List of MaskData objects (for masking streaks)
        
        Returns:
            Dictionary with ODC estimate and components
        """
        backgrounds = []
        frames_with_metadata = []
        
        for f, m in zip(frames, masks):
            bg = estimate_background_robust(f.data, m.mask)
            if not np.isnan(bg):
                backgrounds.append(bg)
                
                # Try to get metadata for physical model
                if self.use_physical_model:
                    try:
                        from ..core.fits_metadata import get_observation_context
                        context = get_observation_context(f.path)
                        if context['has_metadata'] and context['date']:
                            frames_with_metadata.append({
                                'background': bg,
                                'context': context,
                                'path': f.path
                            })
                    except Exception as e:
                        logger.debug(f"Could not extract metadata from {f.path}: {e}")
        
        if not backgrounds:
            return {"error": "No valid background data"}
            
        bg_array = np.array(backgrounds)
        
        # Method 1: Simple percentile baseline (always computed as fallback)
        baseline = np.percentile(bg_array, 5)
        current_median = np.median(bg_array)
        excess_simple = max(0, current_median - baseline)
        odc_percent_simple = (excess_simple / baseline * 100) if baseline > 0 else 0.0
        
        result = {
            'num_frames': len(backgrounds),
            'odc_percent': float(odc_percent_simple),
            'baseline_level': float(baseline),
            'median_level': float(current_median),
            'method': 'percentile_baseline'
        }
        
        # Method 2: Physical model (if metadata available)
        if self.use_physical_model and len(frames_with_metadata) > 0:
            try:
                from ..skyglow.physical_model import (
                    natural_sky_brightness,
                    estimate_odc_from_observed
                )
                
                # Use first frame with good metadata as representative
                representative = frames_with_metadata[0]
                ctx = representative['context']
                
                # Calculate natural sky brightness
                natural_model = natural_sky_brightness(
                    date=ctx['date'],
                    observer_lat=ctx['observer_lat'],
                    observer_lon=ctx['observer_lon'],
                    zenith_distance=ctx['zenith_distance'],
                    altitude_m=ctx['altitude_m']
                )
                
                # Convert background (ADU) to rough magnitude estimate
                # Simplified conversion; proper calibration in Phase 4
                bg_min, bg_max = np.percentile(bg_array, [5, 95])
                if bg_max > bg_min:
                    normalized_bg = 22 - 4 * (current_median - bg_min) / (bg_max - bg_min)
                else:
                    normalized_bg = 20.0
                
                # Calculate ODC
                odc_result = estimate_odc_from_observed(
                    observed_sky_brightness=normalized_bg,
                    natural_model=natural_model
                )
                
                result.update({
                    'physical_model': {
                        'odc_percent_flux': odc_result['odc_percent_flux'],
                        'odc_magnitude_diff': odc_result['odc_magnitude_diff'],
                        'observed_brightness_mag': normalized_bg,
                        'natural_brightness_mag': natural_model['total_sky_brightness'],
                        'lunar_component_mag': natural_model['lunar_component'],
                        'rayleigh_component_mag': natural_model['rayleigh_component'],
                        'moon_altitude': natural_model['moon_altitude'],
                        'moon_phase_angle': natural_model['moon_phase_angle'],
                        'sun_altitude': natural_model['sun_altitude']
                    },
                    'method': 'physical_model_with_percentile_fallback',
                    'frames_with_metadata': len(frames_with_metadata)
                })
                
                logger.info(f"Physical ODC model: {odc_result['odc_percent_flux']:.2f}% flux increase")
                
            except Exception as e:
                logger.warning(f"Physical model failed, using percentile method: {e}")
        
        # Bootstrap for confidence intervals (on simple method)
        if self.bootstrap_samples > 0:
            rng = np.random.default_rng(42)
            resampled_odcs = []
            for _ in range(self.bootstrap_samples):
                sample = rng.choice(bg_array, size=len(bg_array), replace=True)
                b_line = np.percentile(sample, 5)
                c_med = np.median(sample)
                exc = max(0, c_med - b_line)
                resampled_odcs.append((exc / b_line * 100) if b_line > 0 else 0.0)
            
            ci95 = [float(np.percentile(resampled_odcs, 2.5)), 
                   float(np.percentile(resampled_odcs, 97.5))]
            result['odc_ci95'] = ci95
        else:
            result['odc_ci95'] = [0.0, 0.0]

        return result
