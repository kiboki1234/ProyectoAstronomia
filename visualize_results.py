import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
import glob
import os
import random

def visualize(input_dir, output_dir, num_samples=3):
    frames = sorted(glob.glob(os.path.join(input_dir, "*.fits")))
    # Filter out truth files
    frames = [f for f in frames if "truth" not in f]
    
    if not frames:
        print("No frames found.")
        return

    selected = random.sample(frames, min(len(frames), num_samples))
    
    fig, axes = plt.subplots(len(selected), 3, figsize=(15, 5 * len(selected)))
    if len(selected) == 1: axes = [axes] # Handle single row case

    for i, frame_path in enumerate(selected):
        basename = os.path.basename(frame_path)
        mask_path = os.path.join(output_dir, "masks", basename.replace(".fits", "_mask.fits"))
        
        # Read Frame
        with fits.open(frame_path) as hdu:
            img = hdu[0].data
            
        # Read Mask
        mask = None
        if os.path.exists(mask_path):
            with fits.open(mask_path) as hdu:
                mask = hdu[0].data
        
        # Plot Image
        ax_img = axes[i][0]
        # Use log scale or robust percentiles for better visualization
        vmin, vmax = np.percentile(img, [1, 99])
        ax_img.imshow(img, cmap='gray', origin='lower', vmin=vmin, vmax=vmax)
        ax_img.set_title(f"Input: {basename}")
        ax_img.axis('off')
        
        # Plot Mask
        ax_mask = axes[i][1]
        if mask is not None:
            ax_mask.imshow(mask, cmap='Reds', origin='lower', interpolation='nearest')
            ax_mask.set_title("Detected Mask")
        else:
            ax_mask.text(0.5, 0.5, "No Mask Found", ha='center')
        ax_mask.axis('off')
        
        # Plot Overlay
        ax_overlay = axes[i][2]
        ax_overlay.imshow(img, cmap='gray', origin='lower', vmin=vmin, vmax=vmax)
        if mask is not None:
            # Create RGBA for transparency
            # Mask where 1 -> Red with alpha 0.5
            colored_mask = np.zeros(mask.shape + (4,))
            colored_mask[mask > 0] = [1, 0, 0, 0.3] # Red, 30% opacity
            ax_overlay.imshow(colored_mask, origin='lower')
        ax_overlay.set_title("Overlay")
        ax_overlay.axis('off')

    plt.tight_layout()
    out_file = "results_preview.png"
    plt.savefig(out_file)
    print(f"Visualization saved to {os.path.abspath(out_file)}")

if __name__ == "__main__":
    visualize("./data/test_data", "./data/output")
