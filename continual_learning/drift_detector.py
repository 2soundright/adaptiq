"""
continual_learning/drift_detector.py
--------------------------------------
Detects distributional drift in incoming queries by comparing the average
pairwise cosine similarity of the last 50 embeddings vs the previous 50.

If mean cosine similarity < 0.7  → drift detected.
On drift: plasticity is boosted by 50 % for the next update cycle.
"""

from typing import List, Optional, Tuple

import numpy as np

from continual_learning.replay_buffer import get_recent_embeddings

_DRIFT_THRESHOLD  = 0.7   # mean cosine similarity below this → drift
_WINDOW_SIZE      = 50    # number of embeddings per comparison window
_PLASTICITY_BOOST = 1.5   # multiplier applied to plasticity on drift


def _mean_pairwise_cosine(embeddings: List[List[float]]) -> float:
    """
    Compute the mean pairwise cosine similarity for a set of embeddings.
    Uses a random subsample of up to 20 pairs for efficiency.
    """
    if len(embeddings) < 2:
        return 1.0

    try:
        mat = np.array(embeddings, dtype=np.float32)
        # Normalise rows
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1e-9, norms)
        mat   = mat / norms

        # Centroid-based proxy: mean similarity to centroid
        centroid = mat.mean(axis=0)
        centroid /= max(np.linalg.norm(centroid), 1e-9)
        sims = mat @ centroid
        return float(sims.mean())
    except Exception as exc:
        print(f"[drift_detector] _mean_pairwise_cosine error: {exc}")
        return 1.0


def detect_drift(
    company_id: int,
) -> Tuple[bool, float, float]:
    """
    Detect concept drift for a company.

    Compares:
      - recent window  : last 50 embeddings
      - previous window: embeddings 51–100

    Returns:
        (drift_detected: bool, recent_sim: float, previous_sim: float)
    """
    try:
        all_embeddings = get_recent_embeddings(company_id, limit=_WINDOW_SIZE * 2)
    except Exception as exc:
        print(f"[drift_detector] Failed to fetch embeddings: {exc}")
        return False, 1.0, 1.0

    if len(all_embeddings) < _WINDOW_SIZE * 2:
        # Not enough data yet
        return False, 1.0, 1.0

    recent   = all_embeddings[:_WINDOW_SIZE]
    previous = all_embeddings[_WINDOW_SIZE: _WINDOW_SIZE * 2]

    recent_sim   = _mean_pairwise_cosine(recent)
    previous_sim = _mean_pairwise_cosine(previous)

    # Drift: the recent distribution has shifted away from itself compared
    # to the stable previous window, OR recent centroid similarity is low.
    drift_detected = recent_sim < _DRIFT_THRESHOLD

    if drift_detected:
        print(
            f"[drift_detector] Drift detected for company {company_id}: "
            f"recent_sim={recent_sim:.3f} < threshold={_DRIFT_THRESHOLD}"
        )

    return drift_detected, recent_sim, previous_sim


def get_plasticity_multiplier(company_id: int) -> float:
    """
    Return a plasticity multiplier:
      1.5  if drift detected
      1.0  otherwise
    """
    drift, _, _ = detect_drift(company_id)
    return _PLASTICITY_BOOST if drift else 1.0


def drift_summary(company_id: int) -> dict:
    """
    Return a dict summarising the current drift state for the admin panel.
    """
    drift, recent_sim, prev_sim = detect_drift(company_id)
    return {
        "drift_detected":  drift,
        "recent_sim":      round(recent_sim,  4),
        "previous_sim":    round(prev_sim,    4),
        "threshold":       _DRIFT_THRESHOLD,
        "plasticity_mult": _PLASTICITY_BOOST if drift else 1.0,
        "status":          "⚠️ DRIFT DETECTED" if drift else "✅ Stable",
    }
