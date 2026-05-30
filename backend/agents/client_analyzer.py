from dataclasses import dataclass
from datetime import datetime, timezone
from models import RawJob


@dataclass
class ClientAnalysis:
    score: float
    hire_rate: float | None
    payment_verified: bool
    total_spent: float | None
    proposals_count: int | None
    posted_at: datetime | None
    urgency: str  # "quente" | "normal" | "frio"


def _urgency(posted_at: datetime | None, proposals_count: int | None) -> str:
    now = datetime.now(timezone.utc)
    hours_old = ((now - posted_at).total_seconds() / 3600) if posted_at else None
    bids = proposals_count or 0

    if hours_old is not None and hours_old < 24 and bids < 10:
        return "quente"
    if (hours_old is not None and hours_old > 72) or bids > 25:
        return "frio"
    return "normal"


def _score_from_signals(
    hire_rate: float | None,
    payment_verified: bool,
    total_spent: float | None,
) -> float:
    score = 50.0  # base neutra sem dados

    if payment_verified:
        score += 20

    if hire_rate is not None:
        if hire_rate >= 0.6:
            score += 20
        elif hire_rate >= 0.3:
            score += 10
        else:
            score -= 15

    if total_spent is not None:
        if total_spent >= 10_000:
            score += 15
        elif total_spent >= 1_000:
            score += 8
        elif total_spent == 0:
            score -= 10

    return max(0.0, min(100.0, score))


class ClientAnalyzer:
    def analyze(self, job: RawJob) -> ClientAnalysis:
        if job.source == "freelancer":
            return self._freelancer(job.raw_data)
        if job.source == "remoteok":
            return self._remoteok(job.raw_data)
        if job.source == "remotive":
            return self._remotive(job.raw_data)
        if job.source == "upwork":
            return self._upwork(job.raw_data)
        if job.source == "workana":
            return self._workana(job.raw_data)
        return self._default()

    def _freelancer(self, data: dict) -> ClientAnalysis:
        bid_stats = data.get("bid_stats", {})
        proposals_count = bid_stats.get("bid_count")

        time_submitted = data.get("time_submitted")
        posted_at = (
            datetime.fromtimestamp(time_submitted, tz=timezone.utc)
            if time_submitted
            else None
        )

        # Employer reputation (present when employer_details=True is requested)
        employer = data.get("owner_details", data.get("owner", {}))
        reputation = employer.get("employer_reputation", {}).get("entire_history", {})

        hire_rate_raw = reputation.get("hire_rate")
        hire_rate = float(hire_rate_raw) if hire_rate_raw is not None else None

        earnings_raw = reputation.get("earnings_score")
        total_spent = float(earnings_raw) if earnings_raw is not None else None

        status = employer.get("status", {})
        payment_verified = bool(status.get("payment_verified", False))

        score = _score_from_signals(hire_rate, payment_verified, total_spent)
        urgency = _urgency(posted_at, proposals_count)

        return ClientAnalysis(
            score=score,
            hire_rate=hire_rate,
            payment_verified=payment_verified,
            total_spent=total_spent,
            proposals_count=proposals_count,
            posted_at=posted_at,
            urgency=urgency,
        )

    def _remoteok(self, data: dict) -> ClientAnalysis:
        date_raw = data.get("date") or data.get("epoch")
        posted_at = None
        if date_raw:
            try:
                posted_at = datetime.fromtimestamp(int(date_raw), tz=timezone.utc)
            except (ValueError, TypeError):
                pass

        urgency = _urgency(posted_at, None)
        return ClientAnalysis(
            score=50.0,
            hire_rate=None,
            payment_verified=False,
            total_spent=None,
            proposals_count=None,
            posted_at=posted_at,
            urgency=urgency,
        )

    def _remotive(self, data: dict) -> ClientAnalysis:
        date_str = data.get("publication_date") or data.get("date")
        posted_at = None
        if date_str:
            try:
                posted_at = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
                if posted_at.tzinfo is None:
                    posted_at = posted_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        urgency = _urgency(posted_at, None)
        return ClientAnalysis(
            score=50.0,
            hire_rate=None,
            payment_verified=False,
            total_spent=None,
            proposals_count=None,
            posted_at=posted_at,
            urgency=urgency,
        )

    def _upwork(self, data: dict) -> ClientAnalysis:
        client = data.get("client") or {}

        spent = (client.get("totalSpent") or {}).get("rawValue")
        total_spent = float(spent) if spent not in (None, "") else None

        payment_verified = client.get("verificationStatus") == "VERIFIED"

        applicants = data.get("totalApplicants")
        proposals_count = int(applicants) if applicants is not None else None

        created = data.get("createdDateTime")
        posted_at = None
        if created:
            try:
                posted_at = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
                if posted_at.tzinfo is None:
                    posted_at = posted_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        score = _score_from_signals(None, payment_verified, total_spent)
        urgency = _urgency(posted_at, proposals_count)
        return ClientAnalysis(
            score=score,
            hire_rate=None,
            payment_verified=payment_verified,
            total_spent=total_spent,
            proposals_count=proposals_count,
            posted_at=posted_at,
            urgency=urgency,
        )

    def _workana(self, data: dict) -> ClientAnalysis:
        # Workana expõe poucos sinais e datas relativas ("Ontem"), então a urgência
        # é guiada pelo número de propostas (ex.: "Propostas: 56").
        payment_verified = bool(data.get("hasVerifiedPaymentMethod", False))

        proposals_count = None
        bids_raw = data.get("totalBids")
        if bids_raw:
            digits = "".join(ch for ch in str(bids_raw) if ch.isdigit())
            proposals_count = int(digits) if digits else None

        score = _score_from_signals(None, payment_verified, None)
        urgency = _urgency(None, proposals_count)
        return ClientAnalysis(
            score=score,
            hire_rate=None,
            payment_verified=payment_verified,
            total_spent=None,
            proposals_count=proposals_count,
            posted_at=None,
            urgency=urgency,
        )

    def _default(self) -> ClientAnalysis:
        return ClientAnalysis(
            score=50.0,
            hire_rate=None,
            payment_verified=False,
            total_spent=None,
            proposals_count=None,
            posted_at=None,
            urgency="normal",
        )
