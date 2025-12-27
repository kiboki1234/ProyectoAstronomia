# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study

import numpy as np
from typing import List, Tuple, Optional
from ...core.types import FrameData, MaskData
from ...core.io_fits import write_fits
import os
from astropy.io import fits
from ...core.logging import get_logger

logger = get_logger()

class SyntheticGenerator:
    def __init__(self, shape: Tuple[int, int] = (1024, 1024), seed: int = 42):
        self.shape = shape
        self.rng = np.random.default_rng(seed)
    
    def generate_background(self, level: float = 100.0, noise: float = 5.0) -> np.ndarray:
        """Generates a noisy background."""
        return self.rng.normal(loc=level, scale=noise, size=self.shape)

    def add_stars(self, image: np.ndarray, num_stars: int = 50, flux_range: Tuple[float, float] = (500, 5000)) -> np.ndarray:
        """Adds simple point-source stars."""
        # This is a very simple star model (single pixel or small gaussian could be better, but keeping it simple for MVP)
        ys = self.rng.integers(0, self.shape[0], size=num_stars)
        xs = self.rng.integers(0, self.shape[1], size=num_stars)
        fluxes = self.rng.uniform(flux_range[0], flux_range[1], size=num_stars)
        
        for x, y, f in zip(xs, ys, fluxes):
            image[y, x] += f
        return image

    def add_streak(self, image: np.ndarray, mask: np.ndarray, intensity: float = 1000.0, width: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """Adds a single linear streak to image and mask."""
        x0, y0 = self.rng.integers(0, self.shape[1]), self.rng.integers(0, self.shape[0])
        x1, y1 = self.rng.integers(0, self.shape[1]), self.rng.integers(0, self.shape[0])
        
        # Simple line drawing (Bresenham-like or just sampling)
        length = int(np.hypot(x1 - x0, y1 - y0))
        if length == 0: return image, mask
        
        x, y = np.linspace(x0, x1, length), np.linspace(y0, y1, length)
        xi = x.astype(int)
        yi = y.astype(int)
        
        # Clip to bounds
        valid = (xi >= 0) & (xi < self.shape[1]) & (yi >= 0) & (yi < self.shape[0])
        xi, yi = xi[valid], yi[valid]
        
        # Add to image
        image[yi, xi] += intensity
        
        # Add to mask (dilate by width/2)
        # For MVP, just mask the exact line and maybe 1 pixel neighbors
        for i in range(-width // 2 + 1, width // 2 + 1):
             # Simple horizontal/vertical dilation approximation
             for dx in [0, 1]:
                 for dy in [0, 1]:
                     dx_shift, dy_shift = dx * i, dy * i
                     x_curr = np.clip(xi + dx_shift, 0, self.shape[1]-1)
                     y_curr = np.clip(yi + dy_shift, 0, self.shape[0]-1)
                     mask[y_curr, x_curr] = 1
                     
        return image, mask

    def generate_frame(self, filename: str = "synth.fits", num_streaks: int = 2) -> None:
        """Generates a full synthetic frame and saves it."""
        image = self.generate_background()
        image = self.add_stars(image)
        mask = np.zeros(self.shape, dtype=np.uint8)
        
        for _ in range(num_streaks):
            image, mask = self.add_streak(image, mask)
        
        # Header
        header = fits.Header()
        header['OBJECT'] = 'Synthetic'
        header['IS_SYNTH'] = True
        
        write_fits(filename, image, header)
        
        # Save truth mask too
        mask_filename = filename.replace(".fits", "_truth.fits")
        header['MASKTYPE'] = 'TRUTH'
        write_fits(mask_filename, mask, header)
        logger.info(f"Generated {filename} and {mask_filename}")

def generate_dataset(output_dir: str, n_frames: int = 5):
    """CLI helper to generate a batch."""
    os.makedirs(output_dir, exist_ok=True)
    gen = SyntheticGenerator()
    for i in range(n_frames):
        fname = os.path.join(output_dir, f"frame_{i:03d}.fits")
        gen.generate_frame(fname)
