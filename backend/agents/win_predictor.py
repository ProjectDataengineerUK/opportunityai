"""
Win probability predictor using Bayesian smoothing with Laplace prior.

Approach: frequentist win-rate per feature segment, smoothed with Laplace's rule
of succession and a hierarchical fallback when a segment has too few samples.

Segmentation hierarchy (most → least specific):
  1. (area, source, score_bucket, urgency, payment_verified)  — full segment
  2. (area, source, score_bucket)
  3. (area, source)
  4. (area,)
  5. global
  6. neutral prior (0.5)
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SegmentFeatures:
    area: str
    source: str
    score_bucket: str          # "low" / "mid" / "high" / "top"
    urgency: str               # "quente" / "normal" / "frio"
    payment_verified: bool


@dataclass
class WinStats:
    wins: float = 0.0
    total: float = 0.0


# Mapping from segment key (tuple) → WinStats.
# Keys are arbitrary-length tuples from the hierarchy list below.
HistoryStats = dict[tuple, WinStats]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SCORE_BUCKETS = [(0, 40, "low"), (40, 60, "mid"), (60, 80, "high"), (80, 101, "top")]


def _score_bucket(score: float) -> str:
    for lo, hi, label in _SCORE_BUCKETS:
        if lo <= score < hi:
            return label
    return "high"


def _segment_keys(f: SegmentFeatures) -> list[tuple]:
    """Return hierarchy of segment keys from most to least specific."""
    return [
        (f.area, f.source, f.score_bucket, f.urgency, f.payment_verified),
        (f.area, f.source, f.score_bucket),
        (f.area, f.source),
        (f.area,),
        (),  # global
    ]


# ---------------------------------------------------------------------------
# Core pure prediction function
# ---------------------------------------------------------------------------

def predict_win_probability(
    features: SegmentFeatures,
    history: HistoryStats,
    laplace_alpha: float = 1.0,
    min_samples: float = 5.0,
) -> float:
    """Return estimated win probability in [0, 1].

    Uses Laplace smoothed win-rate with hierarchical fallback.
    The neutral prior is 0.5 (1 pseudo-win out of 2 pseudo-trials when alpha=1).
    """
    neutral_prior = 0.5

    for key in _segment_keys(features):
        stats = history.get(key)
        if stats is None or stats.total < min_samples:
            continue
        # Laplace smoothing: (wins + α) / (total + 2α)  [symmetric prior at 0.5]
        return (stats.wins + laplace_alpha) / (stats.total + 2 * laplace_alpha)

    # No segment has enough data — return Laplace-smoothed neutral prior.
    # When history is completely empty this equals exactly 0.5.
    global_stats = history.get(())
    if global_stats is not None and global_stats.total > 0:
        return (global_stats.wins + laplace_alpha) / (global_stats.total + 2 * laplace_alpha)

    return neutral_prior


# ---------------------------------------------------------------------------
# History aggregation
# ---------------------------------------------------------------------------

def build_history_stats(
    outcomes: list[dict],
    opportunities_by_id: dict[str, dict],
    no_response_weight: float = 1.0,
) -> HistoryStats:
    """Aggregate win/total counts from outcomes joined with opportunity features.

    Args:
        outcomes: list of outcome dicts (keys: opportunity_id, outcome).
        opportunities_by_id: mapping opportunity_id → opportunity dict.
        no_response_weight: how much 'sem_resposta' counts as a loss (0–1).
    """
    history: HistoryStats = {}

    for outcome in outcomes:
        opp_id = outcome.get("opportunity_id", "")
        result = outcome.get("outcome", "")
        opp = opportunities_by_id.get(opp_id)
        if opp is None:
            continue

        score = float(opp.get("score", 50.0))
        features = SegmentFeatures(
            area=opp.get("area", ""),
            source=opp.get("source", ""),
            score_bucket=_score_bucket(score),
            urgency=opp.get("urgency", "normal"),
            payment_verified=bool(opp.get("client_payment_verified", False)),
        )

        if result == "ganhou":
            win_value = 1.0
            loss_value = 0.0
        elif result == "perdeu":
            win_value = 0.0
            loss_value = 1.0
        elif result == "sem_resposta":
            win_value = 0.0
            loss_value = no_response_weight
        else:
            continue  # unknown outcome — skip

        effective_total = win_value + loss_value
        if effective_total == 0.0:
            continue

        for key in _segment_keys(features):
            if key not in history:
                history[key] = WinStats()
            history[key].wins += win_value
            history[key].total += effective_total

    return history


# ---------------------------------------------------------------------------
# Convenience: features from an Opportunity-like dict
# ---------------------------------------------------------------------------

def features_from_opportunity(opp: dict) -> SegmentFeatures:
    return SegmentFeatures(
        area=opp.get("area", ""),
        source=opp.get("source", ""),
        score_bucket=_score_bucket(float(opp.get("score", 50.0))),
        urgency=opp.get("urgency", "normal"),
        payment_verified=bool(opp.get("client_payment_verified", False)),
    )
