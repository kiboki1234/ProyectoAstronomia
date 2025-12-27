#!/usr/bin/env python
# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study

"""
Validate detector performance against ground truth dataset.

This script evaluates the baseline or ML detector on a labeled dataset
(YOLO format) and generates a comprehensive validation report.
"""

import argparse
from pathlib import Path
import json
from tqdm import tqdm
from PIL import Image
import numpy as np

from orbitalskyshield.validation import (
    parse_yolo_label,
    evaluate_single_frame,
    generate_validation_report
)
from orbitalskyshield.core.logging import get_logger

logger = get_logger()


def main():
    parser = argparse.ArgumentParser(
        description="Validate streak detector against ground truth dataset"
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        required=True,
        help="Path to dataset directory (should contain images/ and labels/)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/validation",
        help="Directory to save validation results"
    )
    parser.add_argument(
        "--detector",
        type=str,
        default="baseline",
        choices=["baseline", "improved", "adaptive"],
        help="Detector to evaluate"
    )
    parser.add_argument(
        "--threshold-sigma",
        type=float,
        default=5.0,
        help="Threshold sigma for baseline detector"
    )
    parser.add_argument(
        "--percentile",
        type=float,
        default=98.0,
        help="Percentile threshold for adaptive detector"
    )
    parser.add_argument(
        "--min-aspect-ratio",
        type=float,
        default=3.0,
        help="Minimum aspect ratio for streak detection"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Maximum number of samples to process (for testing)"
    )
    
    args = parser.parse_args()
    
    # Setup paths
    dataset_dir = Path(args.dataset_dir)
    images_dir = dataset_dir / "images"
    labels_dir = dataset_dir / "labels"
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not images_dir.exists():
        logger.error(f"Images directory not found: {images_dir}")
        return
    
    if not labels_dir.exists():
        logger.error(f"Labels directory not found: {labels_dir}")
        return
    
    # Initialize detector
    logger.info(f"Initializing {args.detector} detector...")
    if args.detector == "baseline":
        from orbitalskyshield.streak_detection.baseline_detector import BaselineDetector
        detector = BaselineDetector(
            threshold_sigma=args.threshold_sigma,
            line_width=3
        )
    elif args.detector == "improved":
        from orbitalskyshield.streak_detection.improved_detector import ImprovedDetector
        detector = ImprovedDetector(
            threshold_sigma=args.threshold_sigma,
            min_aspect_ratio=args.min_aspect_ratio
        )
    elif args.detector == "adaptive":
        from orbitalskyshield.streak_detection.improved_detector import AdaptiveDetector
        detector = AdaptiveDetector(
            percentile_thresh=args.percentile,
            min_aspect_ratio=args.min_aspect_ratio
        )
    else:
        raise NotImplementedError(f"Detector {args.detector} not implemented yet")
    
    # Get image files
    image_files = sorted(list(images_dir.glob("*.jpeg")) + 
                        list(images_dir.glob("*.jpg")) + 
                        list(images_dir.glob("*.png")))
    
    if args.max_samples:
        image_files = image_files[:args.max_samples]
    
    logger.info(f"Found {len(image_files)} images to process")
    
    # Process each image
    metrics_list = []
    failed_files = []
    
    for img_path in tqdm(image_files, desc="Validating"):
        try:
            # Load image
            img = Image.open(img_path)
            img_array = np.array(img.convert('L'))  # Convert to grayscale
            
            # Get corresponding label
            label_path = labels_dir / f"{img_path.stem}.txt"
            
            # Parse ground truth mask
            mask_gt = parse_yolo_label(label_path, img_array.shape)
            
            # Count GT streaks (number of lines in label file)
            num_gt_streaks = 0
            if label_path.exists():
                with open(label_path, 'r') as f:
                    num_gt_streaks = len([line for line in f if line.strip()])
            
            # Run detector
            detection_result = detector.detect(img_array)
            mask_pred = detection_result.mask
            num_pred_streaks = detection_result.meta.get('detected_lines', 0)
            
            # Evaluate
            frame_metrics = evaluate_single_frame(
                mask_pred,
                mask_gt,
                num_gt_streaks=num_gt_streaks,
                num_pred_streaks=num_pred_streaks
            )
            
            metrics_list.append(frame_metrics)
            
        except Exception as e:
            logger.error(f"Failed to process {img_path.name}: {e}")
            failed_files.append(str(img_path))
    
    # Generate report
    logger.info("Generating validation report...")
    report = generate_validation_report(
        metrics_list=metrics_list,
        detector_name=f"{args.detector}_sigma{args.threshold_sigma}",
        dataset_name=dataset_dir.name,
        output_path=output_dir / "validation_report.json"
    )
    
    # Print summary to console
    summary = report['summary']
    print("\n" + "="*60)
    print("VALIDATION RESULTS")
    print("="*60)
    print(f"Dataset: {dataset_dir.name}")
    print(f"Detector: {args.detector}")
    print(f"Num frames: {summary['num_frames']}")
    print(f"Failed: {len(failed_files)}")
    print("-"*60)
    print(f"Mean IoU:       {summary['mean_iou']:.4f} ± {summary['std_iou']:.4f}")
    print(f"Median IoU:     {summary['median_iou']:.4f}")
    print(f"Global Precision: {summary['global_precision']:.4f}")
    print(f"Global Recall:    {summary['global_recall']:.4f}")
    print(f"Global F1:        {summary['global_f1']:.4f}")
    print("-"*60)
    print(f"Total TP: {summary['total_tp']}")
    print(f"Total FP: {summary['total_fp']}")
    print(f"Total FN: {summary['total_fn']}")
    print("="*60)
    
    # Save failed files list
    if failed_files:
        with open(output_dir / "failed_files.txt", 'w') as f:
            f.write("\n".join(failed_files))
    
    logger.info(f"Validation complete. Report saved to {output_dir}/validation_report.json")


if __name__ == "__main__":
    main()
