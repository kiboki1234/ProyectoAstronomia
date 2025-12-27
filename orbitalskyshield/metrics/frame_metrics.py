# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study

import numpy as np
from ..core.types import FrameData, MaskData, FrameQuality

def compute_frame_metrics(frame: FrameData, mask_data: MaskData) -> FrameQuality:
    """
    Computes metrics for a single frame based on the detection mask.
    """
    total_pixels = frame.data.size
    affected_pixels = np.sum(mask_data.mask > 0)
    streak_area_fraction = affected_pixels / total_pixels if total_pixels > 0 else 0.0
    
    num_streaks = mask_data.meta.get("detected_lines", 0)
    
    # Simple severity score: mainly based on area fraction for now
    # Could be augmented by brightness of streaks relative to background in v0.2
    severity_score = min(streak_area_fraction * 10, 1.0) # Heuristic scaling
    
    flags = []
    if num_streaks > 0:
        flags.append("STREAK_DETECTED")
    if streak_area_fraction > 0.05:
        flags.append("HIGH_CONTAMINATION")
        
    return FrameQuality(
        file=os.path.basename(frame.path),
        timestamp_utc=frame.timestamp_utc or "UNKNOWN",
        streak_area_fraction=float(streak_area_fraction),
        num_streaks=num_streaks,
        severity_score=float(severity_score),
        flags=flags,
        detector_info=mask_data.meta
    )

import os
