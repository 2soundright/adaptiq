"""
continual_learning/ewc.py
--------------------------
Elastic Weight Consolidation – adapted for RAG relevance adaptation.

In a classic neural-network setting EWC uses a Fisher information matrix
to protect important weights.  Here we use the same *plasticity* concept
to control how quickly individual chunk relevance scores respond to feedback:

  plasticity = base / (1 + usage_count × 0.1)

High usage_count → low plasticity  → stable, well-validated chunks change slowly.
Low  usage_count → high plasticity → new/untested chunks adapt quickly.

The drift_detector can temporarily boost plasticity by 50 % when distributional
shift is detected (see drift_detector.py).
"""

from typing import Dict, Optional


# ── Plasticity calculation ────────────────────────────────────────────────────

def calculate_plasticity(
    base_plasticity: float,
    usage_count: int,
    drift_boost: bool = False,
) -> float:
    """
    Compute the effective plasticity for a chunk.

    Args:
        base_plasticity: Starting plasticity (e.g. 0.2).
        usage_count:     How many times this chunk has been retrieved/used.
        drift_boost:     If True, multiply the result by 1.5 (drift detected).

    Returns:
        Effective plasticity clamped to [0.001, 1.0].
    """
    if usage_count < 0:
        usage_count = 0

    plasticity = base_plasticity / (1.0 + usage_count * 0.1)

    if drift_boost:
        plasticity *= 1.5

    return max(0.001, min(1.0, plasticity))


# ── Score update rule ─────────────────────────────────────────────────────────

def update_relevance_score(
    old_score: float,
    feedback_value: float,
    usage_count: int,
    base_plasticity: float = 0.2,
    drift_boost: bool = False,
) -> float:
    """
    Apply the EWC-inspired relevance update rule:
        new = old × (1 − plasticity) + feedback × plasticity

    Args:
        old_score:       Current relevance score.
        feedback_value:  1.0 for positive, 0.0 for negative feedback.
        usage_count:     Retrieval frequency for this chunk.
        base_plasticity: Base plasticity constant.
        drift_boost:     Whether drift has been detected.

    Returns:
        New relevance score clamped to [0.0, 2.0].
    """
    plasticity = calculate_plasticity(base_plasticity, usage_count, drift_boost)
    new_score  = old_score * (1.0 - plasticity) + feedback_value * plasticity
    return max(0.0, min(2.0, new_score))


# ── Fisher information proxy ──────────────────────────────────────────────────

def compute_importance_weights(
    chunk_scores: Dict[str, float],
    usage_counts: Dict[str, int],
) -> Dict[str, float]:
    """
    Compute a simple importance weight for each chunk.
    Chunks with high relevance_score AND high usage_count are considered
    'important' (Fisher-high) and should change slowly.

    Returns:
        Dict mapping chunk_id → importance weight ∈ [0, 1].
    """
    weights: Dict[str, float] = {}
    try:
        if not chunk_scores:
            return weights
        max_score = max(chunk_scores.values()) or 1.0
        max_usage = max(usage_counts.values()) if usage_counts else 1

        for cid, score in chunk_scores.items():
            usage = usage_counts.get(cid, 0)
            norm_score = score / max_score
            norm_usage = usage / max(max_usage, 1)
            weights[cid] = (norm_score + norm_usage) / 2.0
    except Exception as exc:
        print(f"[ewc] compute_importance_weights error: {exc}")
    return weights
