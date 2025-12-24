from typing import List, Dict
import numpy as np
from ..core.types import FrameQuality, NightReport

def aggregate_night_metrics(qualities: List[FrameQuality], dataset_id: str) -> NightReport:
    """
    Aggregates frame metrics into a night report.
    """
    if not qualities:
        return NightReport(
            dataset_id=dataset_id,
            n_frames=0,
            affected_frames=0,
            median_streak_area_fraction=0.0,
            p95_streak_area_fraction=0.0,
            severity_histogram={}
        )

    fractions = [q.streak_area_fraction for q in qualities]
    affected_count = sum(1 for q in qualities if q.num_streaks > 0)
    
    # Histogram of severity
    severities = [q.severity_score for q in qualities]
    hist_counts, _ = np.histogram(severities, bins=[0, 0.2, 0.4, 0.6, 0.8, 1.01])
    hist_labels = ["0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]
    severity_histogram = dict(zip(hist_labels, hist_counts.tolist()))

    return NightReport(
        dataset_id=dataset_id,
        n_frames=len(qualities),
        affected_frames=affected_count,
        median_streak_area_fraction=float(np.median(fractions)),
        p95_streak_area_fraction=float(np.percentile(fractions, 95)),
        severity_histogram=severity_histogram
    )
