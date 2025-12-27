# Validation Results Summary

## Detector Performance on StreaksYoloDataset (Test Set)

**Dataset:** 50 images from StreaksYoloDataset/test  
**Date:** 2025-12-27

### Results Comparison

| Detector | Config | Mean IoU | Precision | Recall | F1 Score |
|----------|--------|----------|-----------|--------|----------|
| Baseline | σ=5.0 | 0.280 | 0.00% | 0.00% | 0.00 |
| ImprovedDetector | σ=3.0, AR≥2.5 | 0.280 | 0.00% | 0.00% | 0.00 |
| **AdaptiveDetector** | **p=97, AR≥3.0** | **0.045** | **87.45%** | **3.36%** | **0.065** |
| **AdaptiveDetector** | **p=95, AR≥2.5** | **0.048** | **60.09%** | **3.91%** | **0.073** |

### Analysis

#### Baseline & Improved Detectors
- **Problem:** Canny edge detection + Hough Transform completely fails on JPEG astronomical images
- **Reason:** These images are compressed and noisy; edges are weak and fragmented
- **Result:** No lines detected (num_pred_streaks = 0 in most frames)

#### Adaptive Detector (Winner) ✅
- **Method:** Percentile thresholding + morphological filtering by elongation
- **Strengths:**
  - High precision (87% at p=97, 60% at p=95) - few false positives
  - Actually detects streaks (unlike baseline)
  - Simple and robust approach
  
- **Weaknesses:**
  - Low recall (3-4%) - misses most ground truth streaks
  - Likely missing faint/partial streaks
  
- **Why it works:** Doesn't rely on edge detection; directly identifies bright elongated regions

### Configuration Trade-offs

**Higher Percentile (p=97):**
- ✅ Very high precision (87%)
- ❌ Lower recall (3.36%)
- **Use case:** When false positives are costly

**Lower Percentile (p=95):**
- ✅ Better recall (3.91%)
- ⚠️ Moderate precision (60%)  
- **Use case:** When missing streaks is costly

### Recommendations for v0.2

1. **Use AdaptiveDetector as default** (replace baseline)
2. **Target metrics for improved version:**
   - IoU > 0.3
   - Recall > 30%
   - Precision > 70%

3. **Next steps to improve recall:**
   - Lower min_aspect_ratio (detect wider streaks)
   - Multi-scale detection (catch different streak sizes)
   - ML-based detector (v1.0 roadmap)

4. **For paper publication:**
   - Current results demonstrate need for specialized astronomical streak detection
   - Highlight failure of classical CV approaches on compressed astro data
   - Position AdaptiveDetector as "baseline for future ML work"

### Files Generated

- `results/validation_baseline/validation_report.json`
- `results/validation_adaptive/validation_report.json` (p=97)
- `results/validation_adaptive_95/validation_report.json` (p=95)
- `results/validation_improved/validation_report.json`

### Conclusion

Phase 1 (Validation System) **✅ COMPLETE**

**Key Achievement:** Quantitative baseline established for future improvements

**Next Phase:** Physical ODC Model implementation
