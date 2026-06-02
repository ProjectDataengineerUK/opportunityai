"""Tests for win_predictor — covers AT-WP01 through AT-WP05 and edge cases."""

from agents.win_predictor import (
    HistoryStats,
    SegmentFeatures,
    WinStats,
    _score_bucket,
    build_history_stats,
    features_from_opportunity,
    predict_win_probability,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _features(
    area: str = "IA",
    source: str = "freelancer",
    score: float = 75.0,
    urgency: str = "normal",
    payment_verified: bool = False,
) -> SegmentFeatures:
    return SegmentFeatures(
        area=area,
        source=source,
        score_bucket=_score_bucket(score),
        urgency=urgency,
        payment_verified=payment_verified,
    )


def _history_with_segment(
    key: tuple,
    wins: float,
    total: float,
) -> HistoryStats:
    """Build a history dict with a single segment key pre-filled."""
    return {key: WinStats(wins=wins, total=total)}


def _outcome(opp_id: str, result: str) -> dict:
    return {"opportunity_id": opp_id, "outcome": result}


def _opp(
    opp_id: str,
    area: str = "IA",
    source: str = "freelancer",
    score: float = 75.0,
    urgency: str = "normal",
    payment_verified: bool = False,
) -> dict:
    return {
        "id": opp_id,
        "area": area,
        "source": source,
        "score": score,
        "urgency": urgency,
        "client_payment_verified": payment_verified,
    }


# ---------------------------------------------------------------------------
# AT-WP01 — Prior without data
# ---------------------------------------------------------------------------

def test_empty_history_returns_neutral_prior():
    """AT-WP01: no outcomes → win_probability == 0.5 for any features."""
    f = _features()
    assert predict_win_probability(f, {}) == 0.5


def test_empty_history_any_area_returns_neutral_prior():
    for area in ("IA", "Dados", "Python", "Backend", "Cloud"):
        f = _features(area=area)
        assert predict_win_probability(f, {}) == 0.5


# ---------------------------------------------------------------------------
# AT-WP02 — Laplace smoothing with 1 sample
# ---------------------------------------------------------------------------

def test_one_win_does_not_yield_1():
    """AT-WP02: 1 win in segment 'IA' with alpha=1 must be between 0.5 and 0.8."""
    # key covers the full segment, but we set min_samples=1 so it's used
    f = _features(area="IA", source="freelancer", score=75.0)
    full_key = (f.area, f.source, f.score_bucket, f.urgency, f.payment_verified)
    history = _history_with_segment(full_key, wins=1.0, total=1.0)

    prob = predict_win_probability(f, history, laplace_alpha=1.0, min_samples=1.0)

    assert 0.5 < prob < 0.8, f"Expected 0.5 < {prob} < 0.8 (Laplace must pull away from 1.0)"


def test_laplace_smoothed_formula_exactness():
    """(wins + α) / (total + 2α) for alpha=1, wins=1, total=1 → 2/3."""
    f = _features()
    full_key = (f.area, f.source, f.score_bucket, f.urgency, f.payment_verified)
    history = _history_with_segment(full_key, wins=1.0, total=1.0)

    prob = predict_win_probability(f, history, laplace_alpha=1.0, min_samples=1.0)
    assert abs(prob - 2 / 3) < 1e-9


# ---------------------------------------------------------------------------
# AT-WP03 — Strong segment raises probability above 0.6
# ---------------------------------------------------------------------------

def test_strong_segment_raises_probability():
    """AT-WP03: 9 wins / 10 total in 'freelancer' segment → prob > 0.6."""
    f = _features(area="IA", source="freelancer", score=75.0)
    full_key = (f.area, f.source, f.score_bucket, f.urgency, f.payment_verified)
    history = _history_with_segment(full_key, wins=9.0, total=10.0)

    prob = predict_win_probability(f, history, laplace_alpha=1.0, min_samples=5.0)
    assert prob > 0.6, f"Strong segment should give prob > 0.6, got {prob}"


def test_zero_wins_lowers_probability():
    """Segment with 0 wins and many outcomes must be below 0.5."""
    f = _features()
    full_key = (f.area, f.source, f.score_bucket, f.urgency, f.payment_verified)
    history = _history_with_segment(full_key, wins=0.0, total=10.0)

    prob = predict_win_probability(f, history, laplace_alpha=1.0, min_samples=5.0)
    assert prob < 0.5, f"Losing segment should give prob < 0.5, got {prob}"


# ---------------------------------------------------------------------------
# AT-WP04 — sem_resposta counts as defeat
# ---------------------------------------------------------------------------

def test_no_response_counted_as_loss():
    """AT-WP04: 5 sem_resposta with no wins → prob < 0.5."""
    outcomes = [_outcome(f"o{i}", "sem_resposta") for i in range(5)]
    opps = {f"o{i}": _opp(f"o{i}") for i in range(5)}

    history = build_history_stats(outcomes, opps, no_response_weight=1.0)
    f = _features()
    # We need min_samples=5 for the segment to be trusted
    prob = predict_win_probability(f, history, laplace_alpha=1.0, min_samples=5.0)
    assert prob < 0.5, f"5 sem_resposta should push prob below 0.5, got {prob}"


def test_no_response_weight_zero_ignores_no_response():
    """sem_resposta with weight=0 effectively contributes 0 to denominator → ignored."""
    outcomes = [_outcome(f"o{i}", "sem_resposta") for i in range(10)]
    opps = {f"o{i}": _opp(f"o{i}") for i in range(10)}

    history = build_history_stats(outcomes, opps, no_response_weight=0.0)
    # When weight==0, effective_total==0 → all outcomes skipped → empty history
    assert history == {}


def test_no_response_partial_weight():
    """sem_resposta with weight=0.5 counts as half a loss."""
    outcomes = [_outcome("o0", "sem_resposta")]
    opps = {"o0": _opp("o0")}

    history = build_history_stats(outcomes, opps, no_response_weight=0.5)
    global_stats = history.get(())
    assert global_stats is not None
    assert global_stats.wins == 0.0
    assert abs(global_stats.total - 0.5) < 1e-9


# ---------------------------------------------------------------------------
# AT-WP05 — Hierarchical fallback
# ---------------------------------------------------------------------------

def test_fallback_uses_area_when_full_segment_empty():
    """AT-WP05: exact segment has no data but area has → uses area rate."""
    f = _features(area="Dados", source="upwork", score=55.0, urgency="frio")

    # Only populate the (area,) key, not the full segment
    area_key = ("Dados",)
    history = _history_with_segment(area_key, wins=8.0, total=10.0)

    prob = predict_win_probability(f, history, laplace_alpha=1.0, min_samples=5.0)
    # (8+1)/(10+2) = 0.75, not the neutral 0.5
    assert prob > 0.6, f"Expected fallback to area key to give >0.6, got {prob}"
    assert abs(prob - 9 / 12) < 1e-9


def test_fallback_to_global_when_only_global_has_data():
    """When no segment key matches, falls back to global ()."""
    f = _features(area="Cloud")
    history = {(): WinStats(wins=7.0, total=10.0)}

    prob = predict_win_probability(f, history, laplace_alpha=1.0, min_samples=5.0)
    assert abs(prob - 8 / 12) < 1e-9  # (7+1)/(10+2)


def test_no_fallback_below_min_samples_uses_next_level():
    """A segment with data but below min_samples is skipped in favour of broader key."""
    f = _features(area="Python", source="remoteok", score=65.0)
    full_key = (f.area, f.source, f.score_bucket, f.urgency, f.payment_verified)
    area_key = ("Python",)

    # Full segment has 2 samples (below min_samples=5), area key has 10
    history = {
        full_key: WinStats(wins=2.0, total=2.0),  # small, biased
        area_key: WinStats(wins=5.0, total=10.0),  # reliable
    }

    prob = predict_win_probability(f, history, laplace_alpha=1.0, min_samples=5.0)
    # Should use area_key: (5+1)/(10+2) = 0.5
    assert abs(prob - 6 / 12) < 1e-9


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_deterministic_same_inputs_same_output():
    """Same features + same history → same result every time."""
    f = _features()
    history = {("IA",): WinStats(wins=6.0, total=10.0)}
    results = {predict_win_probability(f, history, min_samples=5.0) for _ in range(5)}
    assert len(results) == 1, "Result must be deterministic"


def test_build_history_skips_unknown_outcomes():
    """Outcomes with unrecognised outcome string are ignored."""
    outcomes = [_outcome("o1", "desistiu")]  # unknown
    opps = {"o1": _opp("o1")}
    history = build_history_stats(outcomes, opps)
    assert history == {}


def test_build_history_skips_orphan_outcome():
    """Outcomes whose opportunity_id does not exist in opps_by_id are skipped."""
    outcomes = [_outcome("missing_id", "ganhou")]
    history = build_history_stats(outcomes, {})
    assert history == {}


def test_build_history_win_increments_all_levels():
    """A single 'ganhou' outcome increments counters at all 5 hierarchy levels."""
    outcomes = [_outcome("o1", "ganhou")]
    opps = {"o1": _opp("o1", area="IA", source="freelancer")}
    history = build_history_stats(outcomes, opps)

    # Full + 3 intermediate + global = 5 keys
    assert len(history) == 5
    for stats in history.values():
        assert stats.wins == 1.0
        assert stats.total == 1.0


def test_build_history_loss_increments_total_only():
    outcomes = [_outcome("o1", "perdeu")]
    opps = {"o1": _opp("o1")}
    history = build_history_stats(outcomes, opps)

    for stats in history.values():
        assert stats.wins == 0.0
        assert stats.total == 1.0


def test_score_bucket_boundaries():
    assert _score_bucket(0) == "low"
    assert _score_bucket(39.9) == "low"
    assert _score_bucket(40) == "mid"
    assert _score_bucket(59.9) == "mid"
    assert _score_bucket(60) == "high"
    assert _score_bucket(79.9) == "high"
    assert _score_bucket(80) == "top"
    assert _score_bucket(100) == "top"


def test_features_from_opportunity_dict():
    opp = {
        "area": "Dados",
        "source": "upwork",
        "score": 82.0,
        "urgency": "quente",
        "client_payment_verified": True,
    }
    f = features_from_opportunity(opp)
    assert f.area == "Dados"
    assert f.source == "upwork"
    assert f.score_bucket == "top"
    assert f.urgency == "quente"
    assert f.payment_verified is True


def test_features_from_opportunity_missing_keys():
    """features_from_opportunity must not raise on minimal dict."""
    f = features_from_opportunity({})
    assert f.score_bucket == "mid"  # default score 50.0 → "mid"
    assert f.payment_verified is False


def test_predict_probability_clamped_between_0_and_1():
    """Result is always in [0, 1] regardless of inputs."""
    f = _features()
    for wins, total in [(0, 100), (100, 100), (0, 0), (1, 1)]:
        history = {(): WinStats(wins=float(wins), total=float(total))} if total > 0 else {}
        prob = predict_win_probability(f, history, min_samples=1.0)
        assert 0.0 <= prob <= 1.0
