# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study

import numpy as np
from typing import Tuple
from skimage.transform import hough_line, hough_line_peaks
from skimage.feature import canny
from skimage.morphology import dilation, square
from ..core.types import MaskData
from ..core.logging import get_logger

logger = get_logger()

class BaselineDetector:
    def __init__(self, threshold_sigma: float = 5.0, line_width: int = 3):
        self.threshold_sigma = threshold_sigma
        self.line_width = line_width

    def detect(self, image: np.ndarray) -> MaskData:
        """
        Detects streaks in the image.
        Returns a MaskData object.
        """
        # 1. Simple Sigma Clipping to find bright features
        mean, std = np.mean(image), np.std(image)
        threshold = mean + self.threshold_sigma * std
        binary = image > threshold
        
        # 2. Canny Edge Detection to focus on edges (optional, but helps Hough)
        # For simplicity in MVP, we might just run Hough on the binary mask of bright objects
        # or use Canny on the original image.
        edges = canny(image, sigma=2.0, low_threshold=mean + 2*std, high_threshold=mean + 5*std)
        
        # 3. Hough Transform to find lines
        # tested_angles = np.linspace(-np.pi / 2, np.pi / 2, 360, endpoint=False)
        h, theta, d = hough_line(edges)
        
        mask = np.zeros(image.shape, dtype=np.uint8)
        num_streaks = 0 
        
        # 4. Extract peaks
        # Threshold for hough accumulator could be derived or fixed
        # This is a 'baseline' so we pick top peaks or those above a fraction of max
        if h.max() > 0:
            accum, angles, dists = hough_line_peaks(h, theta, d, threshold=0.3 * h.max())
            
            num_streaks = len(angles)
            
            # Reconstruct lines
            for _, angle, dist in zip(accum, angles, dists):
                y0 = (dist - 0 * np.cos(angle)) / np.sin(angle)
                y1 = (dist - image.shape[1] * np.cos(angle)) / np.sin(angle)
                
                # Draw line on mask
                # using a fast way: check distance of all pixels to the line
                # distance = |x*cos(theta) + y*sin(theta) - rho|
                y_indices, x_indices = np.indices(image.shape)
                distance_map = np.abs(x_indices * np.cos(angle) + y_indices * np.sin(angle) - dist)
                
                # Mask pixels within line_width/2
                mask[distance_map < self.line_width] = 1

        # 5. Metadata
        meta = {
            "method": "BaselineDetector_Hough",
            "threshold_sigma": self.threshold_sigma,
            "detected_lines": num_streaks
        }
        
        return MaskData(mask=mask, meta=meta)
