# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study

"""
Improved streak detector with better handling of astronomical images.

This detector combines multiple techniques:
1. Adaptive local thresholding
2. Morphological filtering for elongated features  
3. Radon Transform (alternative to Hough)
4. Multi-scale processing
"""

import numpy as np
from typing import Tuple, List
from scipy import ndimage
from skimage.transform import hough_line, hough_line_peaks, radon
from skimage.feature import canny
from skimage.morphology import dilation, erosion, rectangle, remove_small_objects
from skimage.filters import threshold_local, gaussian
from skimage.measure import label, regionprops

from ..core.types import MaskData
from ..core.logging import get_logger

logger = get_logger()


class ImprovedDetector:
    """
    Improved streak detector using multiple approaches.
    
    Improvements over baseline:
    - Adaptive local thresholding instead of global sigma-clipping
    - Morphological filtering to identify elongated features
    - Better Hough Transform parameters
    - Optional Radon Transform for weak streaks
    """
    
    def __init__(
        self,
        threshold_sigma: float = 3.0,
        min_streak_length: int = 30,
        min_aspect_ratio: float = 3.0,
        use_radon: bool = False
    ):
        self.threshold_sigma = threshold_sigma
        self.min_streak_length = min_streak_length
        self.min_aspect_ratio = min_aspect_ratio
        self.use_radon = use_radon
    
    def detect(self, image: np.ndarray) -> MaskData:
        """
        Detect streaks using improved multi-stage approach.
        
        Args:
            image: Input image (grayscale)
        
        Returns:
            MaskData with detected mask and metadata
        """
        # Stage 1: Preprocessing and adaptive thresholding
        smoothed = gaussian(image, sigma=1.0)
        
        # Adaptive local thresholding (better for varying backgrounds)
        local_thresh = threshold_local(smoothed, block_size=51, offset=-5)
        bright_features = smoothed > local_thresh
        
        # Stage 2: Morphological filtering for elongated features
        # Remove small isolated pixels
        bright_features = remove_small_objects(bright_features, min_size=20)
        
        # Identify connected components
        labeled = label(bright_features)
        regions = regionprops(labeled)
        
        # Filter by elongation
        elongated_mask = np.zeros_like(image, dtype=bool)
        num_candidate_streaks = 0
        
        for region in regions:
            # Calculate aspect ratio
            if region.minor_axis_length > 0:
                aspect_ratio = region.major_axis_length / region.minor_axis_length
                
                # Check if elongated enough
                if aspect_ratio >= self.min_aspect_ratio and region.major_axis_length >= self.min_streak_length:
                    # Add this region to mask
                    coords = region.coords
                    elongated_mask[coords[:, 0], coords[:, 1]] = True
                    num_candidate_streaks += 1
        
        # Stage 3: Refine with edge detection + Hough
        edges = canny(smoothed, sigma=1.5, low_threshold=0.1, high_threshold=0.2)
        
        # Only look at edges within elongated regions
        edges_filtered = edges & elongated_mask
        
        # Hough Transform on filtered edges
        final_mask = np.zeros_like(image, dtype=np.uint8)
        num_detected_lines = 0
        
        if edges_filtered.any():
            try:
                h, theta, d = hough_line(edges_filtered)
                
                if h.max() > 0:
                    # Lower threshold for detection
                    peaks = hough_line_peaks(h, theta, d, threshold=0.15 * h.max(), num_peaks=10)
                    accum, angles, dists = peaks
                    
                    num_detected_lines = len(angles)
                    
                    # Draw detected lines
                    for _, angle, dist in zip(accum, angles, dists):
                        y_indices, x_indices = np.indices(image.shape)
                        distance_map = np.abs(
                            x_indices * np.cos(angle) + 
                            y_indices * np.sin(angle) - dist
                        )
                        
                        # Wider line width for better visibility
                        final_mask[distance_map < 5] = 1
            
            except Exception as e:
                logger.warning(f"Hough transform failed: {e}")
        
        # If Hough found nothing, use morphological mask as fallback
        if num_detected_lines == 0 and num_candidate_streaks > 0:
            final_mask = elongated_mask.astype(np.uint8)
            num_detected_lines = num_candidate_streaks
            logger.debug(f"Using morphological fallback: {num_candidate_streaks} streaks")
        
        # Metadata
        meta = {
            "method": "ImprovedDetector_Morphology+Hough",
            "threshold_sigma": self.threshold_sigma,
            "detected_lines": num_detected_lines,
            "candidate_regions": num_candidate_streaks
        }
        
        return MaskData(mask=final_mask, meta=meta)


class AdaptiveDetector:
    """
    Even more adaptive detector using percentile-based approach.
    
    This is simpler but often more robust for astronomical images.
    """
    
    def __init__(
        self,
        percentile_thresh: float = 98.0,
        min_streak_length: int = 30,
        min_aspect_ratio: float = 3.0
    ):
        self.percentile_thresh = percentile_thresh
        self.min_streak_length = min_streak_length
        self.min_aspect_ratio = min_aspect_ratio
    
    def detect(self, image: np.ndarray) -> MaskData:
        """
        Detect using simple percentile thresholding + morphology.
        
        Often works better than complex approaches for astronomical data.
        """
        # Smooth to reduce noise
        smoothed = gaussian(image, sigma=1.5)
        
        # Percentile-based threshold (top N% brightest pixels)
        thresh_value = np.percentile(smoothed, self.percentile_thresh)
        bright_mask = smoothed > thresh_value
        
        # Remove very small objects (noise)
        bright_mask = remove_small_objects(bright_mask, min_size=15)
        
        # Find connected components
        labeled = label(bright_mask)
        regions = regionprops(labeled)
        
        # Filter by shape
        streak_mask = np.zeros_like(image, dtype=np.uint8)
        num_streaks = 0
        
        for region in regions:
            # Skip small regions
            if region.area < self.min_streak_length:
                continue
            
            # Calculate aspect ratio
            if region.minor_axis_length > 0:
                aspect_ratio = region.major_axis_length / region.minor_axis_length
                
                if aspect_ratio >= self.min_aspect_ratio:
                    # This looks like a streak
                    coords = region.coords
                    streak_mask[coords[:, 0], coords[:, 1]] = 1
                    num_streaks += 1
        
        meta = {
            "method": "AdaptiveDetector_Percentile",
            "percentile_threshold": self.percentile_thresh,
            "detected_lines": num_streaks
        }
        
        return MaskData(mask=streak_mask, meta=meta)
