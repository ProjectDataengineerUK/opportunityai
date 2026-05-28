from unittest.mock import MagicMock
from datetime import datetime, timezone
from agents.evaluator import Evaluator, EvaluationResult
from models import RawJob


def _make_config(weights=None):
    config = MagicMock()
    config.score_weights = weights or {
        "skill_match": 0.35,
        "budget": 0.25,
        "close_chance": 0.20,
        "competition": 0.10,
        "clarity": 0.10,
    }
    config.decision_thresholds = {"aplicar": 80, "avaliar": 50}
    config.user_profile = {
        "skills": ["Python", "IA", "Data Engineering"],
        "min_budget_usd": 200,
        "languages": ["pt", "en"],
    }
    return config


def _make_gemini_mock(skill_match=90, budget_score=80, close_chance=70, competition=60, clarity=85):
    gemini = MagicMock()
    gemini.generate_structured.return_value = EvaluationResult(
        skill_match=skill_match,
        budget_score=budget_score,
        close_chance=close_chance,
        competition=competition,
        clarity=clarity,
        summary="Vaga de Python com bom orçamento.",
        skills_required=["Python", "FastAPI"],
    )
    return gemini


def _make_job(source="remoteok", budget_min=500.0):
    return RawJob(
        external_id=f"{source}:123",
        source=source,
        title="Python Automation Specialist",
        description="Need Python expert for automation tasks",
        budget_min=budget_min,
        budget_currency="USD",
        url="https://example.com/job/123",
        language="en",
    )


def test_score_is_within_range():
    evaluator = Evaluator(_make_gemini_mock(), _make_config())
    result = evaluator.evaluate(_make_job(), "Python")
    assert 0 <= result.score <= 100


def test_high_scores_produce_aplicar():
    evaluator = Evaluator(_make_gemini_mock(90, 95, 85, 80, 90), _make_config())
    result = evaluator.evaluate(_make_job(), "IA")
    assert result.decision == "APLICAR"


def test_mid_scores_produce_avaliar():
    evaluator = Evaluator(_make_gemini_mock(60, 60, 50, 50, 60), _make_config())
    result = evaluator.evaluate(_make_job(), "Python")
    assert result.decision == "AVALIAR"


def test_low_scores_produce_ignorar():
    evaluator = Evaluator(_make_gemini_mock(20, 10, 20, 30, 20), _make_config())
    result = evaluator.evaluate(_make_job(), "Backend")
    assert result.decision == "IGNORAR"


def test_score_breakdown_is_preserved():
    evaluator = Evaluator(_make_gemini_mock(skill_match=75), _make_config())
    result = evaluator.evaluate(_make_job(), "Dados")
    assert result.score_breakdown.skill_match == 75


def test_opportunity_has_correct_source():
    evaluator = Evaluator(_make_gemini_mock(), _make_config())
    job = _make_job(source="remotive")
    result = evaluator.evaluate(job, "Python")
    assert result.source == "remotive"
