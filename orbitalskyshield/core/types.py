# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
import numpy as np
from astropy.io import fits

@dataclass
class FrameData:
    data: np.ndarray  # 2D image data
    header: fits.Header
    path: str
    timestamp_utc: Optional[str] = None

@dataclass
class MaskData:
    mask: np.ndarray  # Binary mask (bool or uint8, 1=bad, 0=good)
    meta: Dict[str, Any]

@dataclass
class FrameQuality:
    file: str
    timestamp_utc: str
    streak_area_fraction: float
    num_streaks: int
    severity_score: float
    flags: List[str]
    detector_info: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "timestamp_utc": self.timestamp_utc,
            "streak_area_fraction": self.streak_area_fraction,
            "num_streaks": self.num_streaks,
            "severity_score": self.severity_score,
            "flags": self.flags,
            "detector": self.detector_info
        }

@dataclass
class NightReport:
    dataset_id: str
    n_frames: int
    affected_frames: int
    median_streak_area_fraction: float
    p95_streak_area_fraction: float
    severity_histogram: Dict[str, int]
