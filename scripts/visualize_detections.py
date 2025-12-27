#!/usr/bin/env python
"""
Visualize detector output on sample images.

Shows:
1. Original image
2. Ground truth mask
3. Predicted mask
4. Overlay comparison
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from PIL import Image
import random

from orbitalskyshield.streak_detection.improved_detector import AdaptiveDetector
from orbitalskyshield.validation import parse_yolo_label


def visualize_detection(image_path, label_path, detector, output_path):
    """Create 4-panel visualization of detection."""
    # Load image
    img = Image.open(image_path)
    img_gray = np.array(img.convert('L'))
    
    # Load ground truth
    gt_mask = parse_yolo_label(label_path, img_gray.shape)
    
    # Run detector
    detection = detector.detect(img_gray)
    pred_mask = detection.mask
    
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(14, 14))
    
    # Original image
    axes[0, 0].imshow(img_gray, cmap='gray')
    axes[0, 0].set_title('Original Image', fontsize=14, fontweight='bold')
    axes[0, 0].axis('off')
    
    # Ground truth
    axes[0, 1].imshow(img_gray, cmap='gray')
    axes[0, 1].imshow(gt_mask, cmap='Reds', alpha=0.5)
    axes[0, 1].set_title(f'Ground Truth ({label_path.stem})', fontsize=14, fontweight='bold')
    axes[0, 1].axis('off')
    
    # Prediction
    axes[1, 0].imshow(img_gray, cmap='gray')
    axes[1, 0].imshow(pred_mask, cmap='Blues', alpha=0.5)
    axes[1, 0].set_title(f'Prediction (detected: {detection.meta["detected_lines"]} streaks)', 
                         fontsize=14, fontweight='bold')
    axes[1, 0].axis('off')
    
    # Overlay comparison
    # Green = True Positive, Red = False Negative, Blue = False Positive
    overlay = np.zeros((*img_gray.shape, 3), dtype=np.uint8)
    overlay[:,:,0] = img_gray  # R channel = image
    overlay[:,:,1] = img_gray  # G channel = image
    overlay[:,:,2] = img_gray  # B channel = image
    
    # True Positive (where both are 1) - Green
    tp_mask = (gt_mask > 0) & (pred_mask > 0)
    overlay[tp_mask] = [0, 255, 0]
    
    # False Negative (GT but not predicted) - Red
    fn_mask = (gt_mask > 0) & (pred_mask == 0)
    overlay[fn_mask] = [255, 0, 0]
    
    # False Positive (predicted but not GT) - Blue
    fp_mask = (gt_mask == 0) & (pred_mask > 0)
    overlay[fp_mask] = [0, 0, 255]
    
    axes[1, 1].imshow(overlay)
    axes[1, 1].set_title('Comparison (Green=TP, Red=FN, Blue=FP)', fontsize=14, fontweight='bold')
    axes[1, 1].axis('off')
    
    # Calculate metrics
    from orbitalskyshield.validation import compute_pixel_metrics, compute_iou
    iou = compute_iou(pred_mask, gt_mask)
    metrics = compute_pixel_metrics(pred_mask, gt_mask)
    
    # Add metrics text
    metrics_text = f"""
    IoU: {iou:.4f}
    Precision: {metrics['precision']:.4f}
    Recall: {metrics['recall']:.4f}
    F1: {metrics['f1_score']:.4f}
    """
    fig.text(0.5, 0.02, metrics_text, ha='center', fontsize=12, 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.suptitle(f'Detection Example: {image_path.name}', fontsize=16, fontweight='bold')
    plt.tight_layout(rect=[0, 0.05, 1, 0.98])
    
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()
    
    return iou, metrics


def main():
    # Setup
    dataset_dir = Path('data/real_data/StreaksYoloDataset/test')
    images_dir = dataset_dir / 'images'
    labels_dir = dataset_dir / 'labels'
    output_dir = Path('results/analysis/detections')
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Initialize detector
    detector = AdaptiveDetector(percentile_thresh=97.0, min_aspect_ratio=3.0)
    
    # Get all images
    image_files = sorted(list(images_dir.glob('*.jpeg')))
    
    if not image_files:
        print("No images found!")
        return
    
    # Select examples
    print(f"Found {len(image_files)} images")
    print("Selecting example images...")
    
    # Categories:
    examples = {
        'high_iou': None,
        'medium_iou': None,
        'low_iou': None,
        'false_positive': None,
        'true_negative': None
    }
    
    # Process a subset to find good examples
    random.seed(42)
    sample_images = random.sample(image_files, min(30, len(image_files)))
    
    results = []
    for img_path in sample_images:
        label_path = labels_dir / f"{img_path.stem}.txt"
        
        img_gray = np.array(Image.open(img_path).convert('L'))
        gt_mask = parse_yolo_label(label_path, img_gray.shape)
        detection = detector.detect(img_gray)
        
        from orbitalskyshield.validation import compute_iou
        iou = compute_iou(detection.mask, gt_mask)
        has_gt = gt_mask.sum() > 0
        has_pred = detection.mask.sum() > 0
        
        results.append({
            'path': img_path,
            'iou': iou,
            'has_gt': has_gt,
            'has_pred': has_pred
        })
    
    # Sort by IoU
    results.sort(key=lambda x: x['iou'], reverse=True)
    
    # Find examples
    for r in results:
        if examples['high_iou'] is None and r['iou'] > 0.1:
            examples['high_iou'] = r['path']
        elif examples['medium_iou'] is None and 0.01 < r['iou'] <= 0.1:
            examples['medium_iou'] = r['path']
        elif examples['low_iou'] is None and r['iou'] > 0 and r['iou'] <= 0.01:
            examples['low_iou'] = r['path']
        elif examples['false_positive'] is None and not r['has_gt'] and r['has_pred']:
            examples['false_positive'] = r['path']
        elif examples['true_negative'] is None and not r['has_gt'] and not r['has_pred']:
            examples['true_negative'] = r['path']
    
    # Fallbacks
    if examples['high_iou'] is None and results:
        examples['high_iou'] = results[0]['path']
    if examples['low_iou'] is None:
        examples['low_iou'] = sample_images[0]
    
    print(f"\n{'='*60}")
    print("CREATING DETECTION VISUALIZATIONS")
    print(f"{'='*60}\n")
    
    # Create visualizations for each category
    for category, img_path in examples.items():
        if img_path is None:
            continue
        
        label_path = labels_dir / f"{img_path.stem}.txt"
        output_path = output_dir / f"{category}_{img_path.stem}.png"
        
        print(f"📸 Processing {category}: {img_path.name}")
        iou, metrics = visualize_detection(img_path, label_path, detector, output_path)
        print(f"   IoU: {iou:.4f}, Precision: {metrics['precision']:.4f}, Recall: {metrics['recall']:.4f}\n")
    
    print(f"{'='*60}")
    print(f"✅ Visualizations complete! Saved to: {output_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
