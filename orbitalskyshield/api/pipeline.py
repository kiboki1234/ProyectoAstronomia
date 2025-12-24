import os
import glob
import json
import yaml
from typing import List, Tuple
from ..core.types import FrameData, MaskData, FrameQuality, NightReport
from ..core.io_fits import read_fits, write_fits
from ..streak_detection.baseline_detector import BaselineDetector
from ..metrics.frame_metrics import compute_frame_metrics
from ..metrics.night_metrics import aggregate_night_metrics
from ..skyglow.odc_estimator import ODCEstimator
from ..core.logging import get_logger

logger = get_logger()

class OSSPipeline:
    def __init__(self, config_path: str = None):
        self.config = {}
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        
        # Initialize components based on config
        det_conf = self.config.get("detection", {})
        self.detector = BaselineDetector(
            threshold_sigma=det_conf.get("threshold_sigma", 5.0),
            line_width=det_conf.get("line_width", 3)
        )
        self.odc_estimator = ODCEstimator(
            bootstrap_samples=self.config.get("odc", {}).get("bootstrap_samples", 100)
        )

    def process_frame(self, frame_path: str) -> Tuple[FrameData, MaskData, FrameQuality]:
        """Process a single frame."""
        frame = read_fits(frame_path)
        mask = self.detector.detect(frame.data)
        quality = compute_frame_metrics(frame, mask)
        return frame, mask, quality

    def run_on_folder(self, input_dir: str, output_dir: str):
        """Run pipeline on a folder."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        mask_dir = os.path.join(output_dir, "masks")
        quality_dir = os.path.join(output_dir, "quality")
        os.makedirs(mask_dir, exist_ok=True)
        os.makedirs(quality_dir, exist_ok=True)

        fits_files = sorted(glob.glob(os.path.join(input_dir, "*.fits")))
        logger.info(f"Found {len(fits_files)} FITS files in {input_dir}")
        
        all_qualities = []
        all_frames = [] # Keep in memory ONLY if needed for ODC and fits in ram. For MVP ok.
        all_masks = []
        
        for fpath in fits_files:
            # Skip truth files or masks if present in same dir
            if "_truth" in fpath or "mask" in fpath:
                continue
                
            logger.info(f"Processing {os.path.basename(fpath)}...")
            try:
                frame, mask, quality = self.process_frame(fpath)
                
                # Save outputs
                basename = os.path.basename(fpath)
                mask_out = os.path.join(mask_dir, basename.replace(".fits", "_mask.fits"))
                quality_out = os.path.join(quality_dir, basename.replace(".fits", "_quality.json"))
                
                # Write mask
                # Add metadata to header
                mask_header = frame.header.copy()
                mask_header['OSS_MASK'] = True
                write_fits(mask_out, mask.mask, header=mask_header)
                
                # Write quality
                with open(quality_out, 'w') as f:
                    json.dump(quality.to_dict(), f, indent=2)
                
                all_qualities.append(quality)
                all_frames.append(frame)
                all_masks.append(mask)
                
            except Exception as e:
                logger.error(f"Failed to process {fpath}: {e}")

        # Aggregate Night Report
        dataset_id = os.path.basename(os.path.normpath(input_dir))
        night_report = aggregate_night_metrics(all_qualities, dataset_id)
        
        with open(os.path.join(output_dir, "night_summary.json"), 'w') as f:
            # Simple dict dump for dataclass
            # converting to dict via ... vars() or helper? 
            # dataclasses.asdict is standard but let's just do manual for safety or use helper
            import dataclasses
            json.dump(dataclasses.asdict(night_report), f, indent=2)

        # ODC Report
        odc_report = self.odc_estimator.estimate(all_frames, all_masks)
        odc_report["dataset_id"] = dataset_id
        
        with open(os.path.join(output_dir, "odc_report.json"), 'w') as f:
            json.dump(odc_report, f, indent=2)

        logger.info("Pipeline run complete.")
