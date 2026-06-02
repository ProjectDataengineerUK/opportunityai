from datetime import datetime, timedelta, timezone

from agents.client_analyzer import (
    ClientAnalyzer,
    _score_from_signals,
    _urgency,
)
from models import RawJob


def _job(source, **raw):
    return RawJob(
        external_id=f"{source}:1",
        source=source,
        title="Python AI engineer",
        description="Build an LLM pipeline.",
        url="https://example.com/job/1",
        raw_data=raw,
    )


def _ts(hours_ago: float) -> int:
    """Unix timestamp for N hours in the past."""
    return int((datetime.now(timezone.utc) - timedelta(hours=hours_ago)).timestamp())


def _iso(hours_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


# ---------- _urgency ----------

def test_urgency_quente_recent_and_few_bids():
    posted = datetime.now(timezone.utc) - timedelta(hours=5)
    assert _urgency(posted, proposals_count=3) == "quente"


def test_urgency_frio_when_old():
    posted = datetime.now(timezone.utc) - timedelta(hours=100)
    assert _urgency(posted, proposals_count=2) == "frio"


def test_urgency_frio_when_too_many_bids():
    posted = datetime.now(timezone.utc) - timedelta(hours=5)
    assert _urgency(posted, proposals_count=30) == "frio"


def test_urgency_normal_midrange():
    posted = datetime.now(timezone.utc) - timedelta(hours=48)
    assert _urgency(posted, proposals_count=15) == "normal"


def test_urgency_normal_when_no_date_and_no_bids():
    assert _urgency(None, None) == "normal"


def test_urgency_frio_by_bids_without_date():
    assert _urgency(None, proposals_count=40) == "frio"


# ---------- _score_from_signals ----------

def test_score_base_is_neutral_without_data():
    assert _score_from_signals(None, False, None) == 50.0


def test_score_payment_verified_adds():
    assert _score_from_signals(None, True, None) == 70.0


def test_score_high_hire_rate_adds():
    assert _score_from_signals(0.7, False, None) == 70.0


def test_score_low_hire_rate_penalizes():
    assert _score_from_signals(0.1, False, None) == 35.0


def test_score_high_total_spent_adds():
    assert _score_from_signals(None, False, 20_000) == 65.0


def test_score_zero_total_spent_penalizes():
    assert _score_from_signals(None, False, 0) == 40.0


def test_score_clamps_to_100():
    # 50 + 20 (verified) + 20 (hire) + 15 (spent) = 105 -> clamp 100
    assert _score_from_signals(0.9, True, 50_000) == 100.0


def test_score_clamps_to_0_floor():
    # never below 0 even with penalties
    assert _score_from_signals(0.0, False, 0) >= 0.0


# ---------- dispatch per source ----------

def test_analyze_freelancer_extracts_reputation_and_bids():
    job = _job(
        "freelancer",
        bid_stats={"bid_count": 7},
        time_submitted=_ts(5),
        owner_details={
            "employer_reputation": {"entire_history": {"hire_rate": 0.8, "earnings_score": 15000}},
            "status": {"payment_verified": True},
        },
    )
    result = ClientAnalyzer().analyze(job)
    assert result.proposals_count == 7
    assert result.hire_rate == 0.8
    assert result.total_spent == 15000.0
    assert result.payment_verified is True
    assert result.posted_at is not None
    assert result.urgency == "quente"  # 5h old, 7 bids
    # 50 +20 verified +20 hire>=0.6 +15 spent>=10k -> clamp 100
    assert result.score == 100.0


def test_analyze_freelancer_handles_missing_reputation():
    job = _job("freelancer", bid_stats={}, owner_details={})
    result = ClientAnalyzer().analyze(job)
    assert result.hire_rate is None
    assert result.total_spent is None
    assert result.payment_verified is False
    assert result.score == 50.0


def test_analyze_upwork_extracts_client_signals():
    job = _job(
        "upwork",
        client={"totalSpent": {"rawValue": "8000"}, "verificationStatus": "VERIFIED"},
        totalApplicants=12,
        createdDateTime=_iso(10),
    )
    result = ClientAnalyzer().analyze(job)
    assert result.total_spent == 8000.0
    assert result.payment_verified is True
    assert result.proposals_count == 12
    assert result.posted_at is not None
    # 50 +20 verified +8 spent>=1k = 78
    assert result.score == 78.0


def test_analyze_upwork_unverified_no_spend():
    job = _job("upwork", client={"verificationStatus": "NONE"})
    result = ClientAnalyzer().analyze(job)
    assert result.payment_verified is False
    assert result.total_spent is None
    assert result.score == 50.0


def test_analyze_workana_parses_bids_digits():
    job = _job("workana", hasVerifiedPaymentMethod=True, totalBids="Propostas: 56")
    result = ClientAnalyzer().analyze(job)
    assert result.payment_verified is True
    assert result.proposals_count == 56
    assert result.urgency == "frio"  # >25 bids
    assert result.score == 70.0  # 50 + 20 verified


def test_analyze_workana_without_bids():
    job = _job("workana")
    result = ClientAnalyzer().analyze(job)
    assert result.proposals_count is None
    assert result.payment_verified is False


def test_analyze_remoteok_parses_epoch_date():
    job = _job("remoteok", date=_ts(2))
    result = ClientAnalyzer().analyze(job)
    assert result.posted_at is not None
    assert result.score == 50.0
    assert result.hire_rate is None


def test_analyze_remoteok_invalid_date_is_safe():
    job = _job("remoteok", date="not-a-number")
    result = ClientAnalyzer().analyze(job)
    assert result.posted_at is None
    assert result.urgency == "normal"


def test_analyze_remotive_parses_iso_date():
    job = _job("remotive", publication_date=_iso(3))
    result = ClientAnalyzer().analyze(job)
    assert result.posted_at is not None
    assert result.score == 50.0


def test_analyze_remotive_handles_z_suffix():
    job = _job("remotive", publication_date="2026-05-30T12:00:00Z")
    result = ClientAnalyzer().analyze(job)
    assert result.posted_at is not None
    assert result.posted_at.tzinfo is not None


def test_analyze_remotive_invalid_date_is_safe():
    job = _job("remotive", publication_date="garbage")
    result = ClientAnalyzer().analyze(job)
    assert result.posted_at is None
