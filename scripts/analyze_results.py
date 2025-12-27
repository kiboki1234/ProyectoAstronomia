#!/usr/bin/env python
# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study

"""
Detailed analysis and visualization of validation results.

Creates:
1. Performance comparison charts
2. Per-image detection examples
3. Statistical analysis
4. Error analysis
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from PIL import Image
import matplotlib.patches as patches

# Set style
plt.style.use('seaborn-v0_8-darkgrid')


def load_validation_report(report_path):
    """Load validation report JSON."""
    with open(report_path, 'r') as f:
        return json.load(f)


def plot_detector_comparison(reports, output_dir):
    """Create comparison bar chart of detector performance."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Detector Performance Comparison', fontsize=16, fontweight='bold')
    
    detectors = list(reports.keys())
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']
    
    # IoU
    ax = axes[0, 0]
    ious = [reports[d]['summary']['mean_iou'] for d in detectors]
    iou_stds = [reports[d]['summary']['std_iou'] for d in detectors]
    bars = ax.bar(detectors, ious, yerr=iou_stds, capsize=5, color=colors[:len(detectors)])
    ax.set_ylabel('Mean IoU', fontsize=12)
    ax.set_title('Intersection over Union', fontsize=14, fontweight='bold')
    ax.set_ylim([0, max(ious) * 1.2 if max(ious) > 0 else 0.1])
    for bar, iou in zip(bars, ious):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{iou:.4f}', ha='center', va='bottom', fontsize=10)
    
    # Precision
    ax = axes[0, 1]
    precisions = [reports[d]['summary']['global_precision'] * 100 for d in detectors]
    bars = ax.bar(detectors, precisions, color=colors[:len(detectors)])
    ax.set_ylabel('Precision (%)', fontsize=12)
    ax.set_title('Precision (True Positives / All Detections)', fontsize=14, fontweight='bold')
    ax.set_ylim([0, 100])
    for bar, prec in zip(bars, precisions):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{prec:.2f}%', ha='center', va='bottom', fontsize=10)
    
    # Recall
    ax = axes[1, 0]
    recalls = [reports[d]['summary']['global_recall'] * 100 for d in detectors]
    bars = ax.bar(detectors, recalls, color=colors[:len(detectors)])
    ax.set_ylabel('Recall (%)', fontsize=12)
    ax.set_title('Recall (True Positives / All Ground Truth)', fontsize=14, fontweight='bold')
    ax.set_ylim([0, max(recalls) * 1.2 if max(recalls) > 0 else 10])
    for bar, rec in zip(bars, recalls):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{rec:.2f}%', ha='center', va='bottom', fontsize=10)
    
    # F1 Score
    ax = axes[1, 1]
    f1s = [reports[d]['summary']['global_f1'] for d in detectors]
    bars = ax.bar(detectors, f1s, color=colors[:len(detectors)])
    ax.set_ylabel('F1 Score', fontsize=12)
    ax.set_title('F1 Score (Harmonic Mean of P & R)', fontsize=14, fontweight='bold')
    ax.set_ylim([0, max(f1s) * 1.2 if max(f1s) > 0 else 0.1])
    for bar, f1 in zip(bars, f1s):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{f1:.4f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    output_path = output_dir / 'detector_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def plot_iou_distribution(reports, output_dir):
    """Plot IoU distribution across frames."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for detector, report in reports.items():
        ious = [frame['iou'] for frame in report['per_frame_details']]
        ax.hist(ious, bins=20, alpha=0.6, label=detector, edgecolor='black')
    
    ax.set_xlabel('IoU', fontsize=12)
    ax.set_ylabel('Number of Frames', fontsize=12)
    ax.set_title('Distribution of IoU Across Frames', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    output_path = output_dir / 'iou_distribution.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def plot_confusion_matrix(report, output_dir, detector_name):
    """Plot confusion matrix."""
    summary = report['summary']
    
    # Calculate TN from total pixels (assuming 640x640 images on average)
    avg_pixels = 640 * 640 * summary['num_frames']
    tp = summary['total_tp']
    fp = summary['total_fp']
    fn = summary['total_fn']
    tn = avg_pixels - (tp + fp + fn)
    
    matrix = np.array([[tn, fp], [fn, tp]])
    
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(matrix, cmap='Blues', aspect='auto')
    
    # Labels
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(['Predicted Negative', 'Predicted Positive'])
    ax.set_yticklabels(['Actual Negative', 'Actual Positive'])
    ax.set_xlabel('Predicted', fontsize=12)
    ax.set_ylabel('Actual', fontsize=12)
    ax.set_title(f'Confusion Matrix - {detector_name}', fontsize=14, fontweight='bold')
    
    # Annotate
    for i in range(2):
        for j in range(2):
            text = ax.text(j, i, f'{matrix[i, j]:,}',
                          ha="center", va="center", color="black" if matrix[i, j] < matrix.max()/2 else "white",
                          fontsize=14, fontweight='bold')
    
    plt.colorbar(im, ax=ax)
    plt.tight_layout()
    
    output_path = output_dir / f'confusion_matrix_{detector_name}.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def create_summary_table(reports, output_dir):
    """Create summary table as image."""
    fig, ax = plt.subplots(figsize=(14, len(reports) * 1.5 + 2))
    ax.axis('tight')
    ax.axis('off')
    
    # Data
    headers = ['Detector', 'Mean IoU', 'Precision', 'Recall', 'F1 Score', 'TP', 'FP', 'FN']
    rows = []
    for detector, report in reports.items():
        s = report['summary']
        rows.append([
            detector,
            f"{s['mean_iou']:.4f} ± {s['std_iou']:.4f}",
            f"{s['global_precision']*100:.2f}%",
            f"{s['global_recall']*100:.2f}%",
            f"{s['global_f1']:.4f}",
            f"{s['total_tp']:,}",
            f"{s['total_fp']:,}",
            f"{s['total_fn']:,}"
        ])
    
    table = ax.table(cellText=rows, colLabels=headers, cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.5)
    
    # Style header
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#3498db')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Alternate row colors
    for i in range(1, len(rows) + 1):
        for j in range(len(headers)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#ecf0f1')
    
    plt.title('Validation Results Summary', fontsize=16, fontweight='bold', pad=20)
    
    output_path = output_dir / 'summary_table.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def analyze_performance_by_category(report, output_dir, detector_name):
    """Analyze performance on different frame categories."""
    frames = report['per_frame_details']
    
    # Categories
    has_streaks = [f for f in frames if f['num_gt_streaks'] > 0]
    no_streaks = [f for f in frames if f['num_gt_streaks'] == 0]
    
    detected = [f for f in frames if f['num_pred_streaks'] > 0]
    not_detected = [f for f in frames if f['num_pred_streaks'] == 0]
    
    # Stats
    stats = {
        'Frames with GT streaks': len(has_streaks),
        'Frames without GT streaks': len(no_streaks),
        'Frames with detections': len(detected),
        'Frames without detections': len(not_detected),
        'Avg IoU (has streaks)': np.mean([f['iou'] for f in has_streaks]) if has_streaks else 0,
        'Avg IoU (no streaks)': np.mean([f['iou'] for f in no_streaks]) if no_streaks else 0,
    }
    
    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Frame counts
    ax = axes[0]
    categories = ['GT Streaks', 'No GT Streaks', 'Detections', 'No Detections']
    counts = [len(has_streaks), len(no_streaks), len(detected), len(not_detected)]
    colors = ['#e74c3c', '#95a5a6', '#3498db', '#95a5a6']
    bars = ax.bar(categories, counts, color=colors)
    ax.set_ylabel('Number of Frames', fontsize=12)
    ax.set_title(f'Frame Categories - {detector_name}', fontsize=14, fontweight='bold')
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{count}', ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    # IoU comparison
    ax = axes[1]
    iou_categories = ['Has GT Streaks', 'No GT Streaks']
    iou_values = [stats['Avg IoU (has streaks)'], stats['Avg IoU (no streaks)']]
    bars = ax.bar(iou_categories, iou_values, color=['#e74c3c', '#95a5a6'])
    ax.set_ylabel('Average IoU', fontsize=12)
    ax.set_title(f'IoU by Category - {detector_name}', fontsize=14, fontweight='bold')
    for bar, iou in zip(bars, iou_values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{iou:.4f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    output_path = output_dir / f'category_analysis_{detector_name}.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()
    
    return stats


def main():
    # Paths
    results_dir = Path('results')
    analysis_dir = results_dir / 'analysis'
    analysis_dir.mkdir(exist_ok=True)
    
    # Load reports
    reports = {}
    report_dirs = [
        ('Baseline (σ=5.0)', results_dir / 'validation_baseline'),
        ('Adaptive (p=97)', results_dir / 'validation_adaptive'),
        ('Adaptive (p=95)', results_dir / 'validation_adaptive_95'),
    ]
    
    for name, dir_path in report_dirs:
        report_path = dir_path / 'validation_report.json'
        if report_path.exists():
            reports[name] = load_validation_report(report_path)
            print(f"Loaded: {name}")
    
    if not reports:
        print("No validation reports found!")
        return
    
    print(f"\n{'='*60}")
    print("GENERATING DETAILED ANALYSIS")
    print(f"{'='*60}\n")
    
    # 1. Detector comparison
    print("📊 Creating detector comparison chart...")
    plot_detector_comparison(reports, analysis_dir)
    
    # 2. IoU distribution
    print("📊 Creating IoU distribution plot...")
    plot_iou_distribution(reports, analysis_dir)
    
    # 3. Confusion matrices
    for name, report in reports.items():
        print(f"📊 Creating confusion matrix for {name}...")
        plot_confusion_matrix(report, analysis_dir, name.replace(' ', '_'))
    
    # 4. Summary table
    print("📊 Creating summary table...")
    create_summary_table(reports, analysis_dir)
    
    # 5. Category analysis
    for name, report in reports.items():
        print(f"📊 Analyzing categories for {name}...")
        stats = analyze_performance_by_category(report, analysis_dir, name.replace(' ', '_'))
    
    print(f"\n{'='*60}")
    print("DETAILED STATISTICS")
    print(f"{'='*60}\n")
    
    for name, report in reports.items():
        s = report['summary']
        print(f"\n{name}:")
        print(f"  Frames processed: {s['num_frames']}")
        print(f"  Mean IoU: {s['mean_iou']:.4f} ± {s['std_iou']:.4f}")
        print(f"  Median IoU: {s['median_iou']:.4f}")
        print(f"  Global Precision: {s['global_precision']*100:.2f}%")
        print(f"  Global Recall: {s['global_recall']*100:.2f}%")
        print(f"  Global F1: {s['global_f1']:.4f}")
        print(f"  True Positives: {s['total_tp']:,} pixels")
        print(f"  False Positives: {s['total_fp']:,} pixels")
        print(f"  False Negatives: {s['total_fn']:,} pixels")
    
    print(f"\n{'='*60}")
    print(f"✅ Analysis complete! Results saved to: {analysis_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
