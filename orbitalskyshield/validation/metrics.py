"""
Validation metrics for streak detection against ground truth.

This module provides tools to evaluate detector performance using
datasets with labeled ground truth (e.g., YOLO format).
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
import json

from ..core.logging import get_logger

logger = get_logger()


@dataclass
class DetectionMetrics:
    """Container for detection evaluation metrics."""
    iou: float
    precision: float
    recall: float
    f1_score: float
    true_positives: int
    false_positives: int
    false_negatives: int
    num_gt_streaks: int
    num_pred_streaks: int


def parse_yolo_label(label_path: Path, image_shape: Tuple[int, int]) -> np.ndarray:
    """
    Parse YOLO format label file to binary mask.
    
    YOLO format: class x_center y_center width height (normalized 0-1)
    
    Args:
        label_path: Path to .txt label file
        image_shape: (height, width) of the image
    
    Returns:
        Binary mask (numpy array)
    """
    h, w = image_shape
    mask = np.zeros((h, w), dtype=np.uint8)
    
    if not label_path.exists():
        return mask
    
    with open(label_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            
            # Parse normalized bbox
            class_id = int(parts[0])
            x_center = float(parts[1])
            y_center = float(parts[2])
            bbox_width = float(parts[3])
            bbox_height = float(parts[4])
            
            # Convert to pixel coordinates
            x_center_px = int(x_center * w)
            y_center_px = int(y_center * h)
            bbox_w_px = int(bbox_width * w)
            bbox_h_px = int(bbox_height * h)
            
            # Calculate bounding box corners
            x1 = max(0, x_center_px - bbox_w_px // 2)
            y1 = max(0, y_center_px - bbox_h_px // 2)
            x2 = min(w, x_center_px + bbox_w_px // 2)
            y2 = min(h, y_center_px + bbox_h_px // 2)
            
            # Fill mask region
            mask[y1:y2, x1:x2] = 1
    
    return mask


def compute_iou(mask_pred: np.ndarray, mask_gt: np.ndarray) -> float:
    """
    Compute Intersection over Union (IoU) for binary masks.
    
    Args:
        mask_pred: Predicted mask (binary)
        mask_gt: Ground truth mask (binary)
    
    Returns:
        IoU score (0-1)
    """
    intersection = np.logical_and(mask_pred > 0, mask_gt > 0).sum()
    union = np.logical_or(mask_pred > 0, mask_gt > 0).sum()
    
    if union == 0:
        # Both masks empty - perfect match
        return 1.0 if intersection == 0 else 0.0
    
    return float(intersection) / float(union)


def compute_pixel_metrics(mask_pred: np.ndarray, mask_gt: np.ndarray) -> Dict[str, float]:
    """
    Compute pixel-wise classification metrics.
    
    Args:
        mask_pred: Predicted mask (binary)
        mask_gt: Ground truth mask (binary)
    
    Returns:
        Dictionary with TP, FP, FN, TN counts and precision/recall/f1
    """
    pred_binary = (mask_pred > 0).astype(bool)
    gt_binary = (mask_gt > 0).astype(bool)
    
    tp = np.logical_and(pred_binary, gt_binary).sum()
    fp = np.logical_and(pred_binary, ~gt_binary).sum()
    fn = np.logical_and(~pred_binary, gt_binary).sum()
    tn = np.logical_and(~pred_binary, ~gt_binary).sum()
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        'true_positives': int(tp),
        'false_positives': int(fp),
        'false_negatives': int(fn),
        'true_negatives': int(tn),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1)
    }


def evaluate_single_frame(
    mask_pred: np.ndarray,
    mask_gt: np.ndarray,
    num_gt_streaks: int = 0,
    num_pred_streaks: int = 0
) -> DetectionMetrics:
    """
    Evaluate a single frame's detection against ground truth.
    
    Args:
        mask_pred: Predicted mask
        mask_gt: Ground truth mask
        num_gt_streaks: Number of streaks in ground truth (from metadata)
        num_pred_streaks: Number of detected streaks (from detector)
    
    Returns:
        DetectionMetrics object
    """
    iou = compute_iou(mask_pred, mask_gt)
    pixel_metrics = compute_pixel_metrics(mask_pred, mask_gt)
    
    return DetectionMetrics(
        iou=iou,
        precision=pixel_metrics['precision'],
        recall=pixel_metrics['recall'],
        f1_score=pixel_metrics['f1_score'],
        true_positives=pixel_metrics['true_positives'],
        false_positives=pixel_metrics['false_positives'],
        false_negatives=pixel_metrics['false_negatives'],
        num_gt_streaks=num_gt_streaks,
        num_pred_streaks=num_pred_streaks
    )


def aggregate_metrics(metrics_list: List[DetectionMetrics]) -> Dict[str, float]:
    """
    Aggregate metrics across multiple frames.
    
    Args:
        metrics_list: List of DetectionMetrics from individual frames
    
    Returns:
        Dictionary with aggregated statistics
    """
    if not metrics_list:
        return {}
    
    ious = [m.iou for m in metrics_list]
    precisions = [m.precision for m in metrics_list]
    recalls = [m.recall for m in metrics_list]
    f1s = [m.f1_score for m in metrics_list]
    
    total_tp = sum(m.true_positives for m in metrics_list)
    total_fp = sum(m.false_positives for m in metrics_list)
    total_fn = sum(m.false_negatives for m in metrics_list)
    
    # Global precision/recall (micro-average)
    global_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    global_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    global_f1 = 2 * global_precision * global_recall / (global_precision + global_recall) \
                if (global_precision + global_recall) > 0 else 0.0
    
    return {
        'num_frames': len(metrics_list),
        'mean_iou': float(np.mean(ious)),
        'std_iou': float(np.std(ious)),
        'median_iou': float(np.median(ious)),
        'mean_precision': float(np.mean(precisions)),
        'mean_recall': float(np.mean(recalls)),
        'mean_f1': float(np.mean(f1s)),
        'global_precision': float(global_precision),
        'global_recall': float(global_recall),
        'global_f1': float(global_f1),
        'total_tp': int(total_tp),
        'total_fp': int(total_fp),
        'total_fn': int(total_fn)
    }


def generate_validation_report(
    metrics_list: List[DetectionMetrics],
    detector_name: str,
    dataset_name: str,
    output_path: Optional[Path] = None
) -> Dict:
    """
    Generate comprehensive validation report.
    
    Args:
        metrics_list: List of frame-level metrics
        detector_name: Name of the detector being evaluated
        dataset_name: Name of the validation dataset
        output_path: Optional path to save JSON report
    
    Returns:
        Report dictionary
    """
    aggregated = aggregate_metrics(metrics_list)
    
    report = {
        'detector': detector_name,
        'dataset': dataset_name,
        'summary': aggregated,
        'per_frame_details': [
            {
                'iou': m.iou,
                'precision': m.precision,
                'recall': m.recall,
                'f1_score': m.f1_score,
                'num_gt_streaks': m.num_gt_streaks,
                'num_pred_streaks': m.num_pred_streaks
            }
            for m in metrics_list
        ]
    }
    
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Validation report saved to {output_path}")
    
    return report
