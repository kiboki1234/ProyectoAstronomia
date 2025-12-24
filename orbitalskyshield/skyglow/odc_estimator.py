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
    def __init__(self, bootstrap_samples: int = 100):
        self.bootstrap_samples = bootstrap_samples

    def estimate(self, frames: List[FrameData], masks: List[MaskData]) -> Dict[str, Any]:
        """
        Estimates the Orbital Diffuse Contribution (ODC) for a set of frames.
        
        MVP approach:
        1. Calculate background levels for all frames (masking out streaks).
        2. In a real scenario, we would compare this against a model of natural sky brightness (moon, airmass).
        3. For MVP, we assume the 'ODC' is a fraction of the residual if we don't have a physical model yet.
           OR, more simply, we just report the distribution of backgrounds and flag high-streak nights.
           
        Let's implement a placeholder 'Excess Model':
        - Assume lowest 10% of backgrounds represent "natural" sky (darkest).
        - ODC is the mean excess of the rest over this baseline? 
        - This is very scientific-specific, but for the MVP per spec:
          "modelar “residuo” agregado por noche"
        """
        backgrounds = []
        for f, m in zip(frames, masks):
            bg = estimate_background_robust(f.data, m.mask)
            if not np.isnan(bg):
                backgrounds.append(bg)
        
        if not backgrounds:
            return {"error": "No valid background data"}
            
        bg_array = np.array(backgrounds)
        
        # Simple heuristic for MVP:
        # Baseline = 5th percentile (assumed "cleanest" sky)
        baseline = np.percentile(bg_array, 5)
        # Current = Median
        current_median = np.median(bg_array)
        
        # Excess
        excess = max(0, current_median - baseline)
        odc_percent = (excess / baseline * 100) if baseline > 0 else 0.0
        
        # Bootstrap for CI
        # Resample backgrounds, compute ODC% for each
        if self.bootstrap_samples > 0:
            rng = np.random.default_rng(42)
            resampled_odcs = []
            for _ in range(self.bootstrap_samples):
                sample = rng.choice(bg_array, size=len(bg_array), replace=True)
                b_line = np.percentile(sample, 5)
                c_med = np.median(sample)
                exc = max(0, c_med - b_line)
                resampled_odcs.append((exc / b_line * 100) if b_line > 0 else 0.0)
            
            ci95 = [float(np.percentile(resampled_odcs, 2.5)), float(np.percentile(resampled_odcs, 97.5))]
        else:
            ci95 = [0.0, 0.0]

        return {
            "odc_percent": float(odc_percent),
            "odc_ci95": ci95,
            "baseline_level": float(baseline),
            "median_level": float(current_median),
            "method": "mvp_percentile_baseline"
        }
