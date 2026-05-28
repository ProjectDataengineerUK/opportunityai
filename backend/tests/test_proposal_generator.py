from unittest.mock import MagicMock
from agents.proposal_generator import ProposalGenerator, ProposalResult


def _make_config():
    config = MagicMock()
    config.user_profile = {
        "skills": ["Python", "IA", "Data Engineering"],
        "min_budget_usd": 200,
        "languages": ["pt", "en"],
    }
    return config


def _make_generator(proposal="Test proposal text.", suggested_price=500.0, estimated_hours=20):
    gemini = MagicMock()
    gemini.generate_structured.return_value = ProposalResult(
        proposal=proposal,
        suggested_price=suggested_price,
        estimated_hours=estimated_hours,
    )
    return ProposalGenerator(gemini, _make_config())


def test_proposal_returns_text():
    generator = _make_generator(proposal="I can help you build this pipeline.")
    result = generator.generate(
        title="Data Pipeline", description="ETL from S3 to BigQuery",
        area="Dados", language="en", skills_required=["Python", "BigQuery"],
        budget_min=800.0, summary="Well-defined data engineering task.",
    )
    assert result.proposal == "I can help you build this pipeline."


def test_proposal_includes_price():
    generator = _make_generator(suggested_price=750.0)
    result = generator.generate(
        title="ML Model", description="Train classifier",
        area="IA", language="en", skills_required=["Python", "sklearn"],
        budget_min=500.0, summary="Model training task.",
    )
    assert result.suggested_price == 750.0


def test_proposal_with_no_budget():
    generator = _make_generator(suggested_price=None, estimated_hours=None)
    result = generator.generate(
        title="Automation Script", description="Automate Excel reports",
        area="Automação", language="pt", skills_required=["Python"],
        budget_min=None, summary="Simple automation task.",
    )
    assert result.suggested_price is None
    assert result.estimated_hours is None


def test_proposal_estimates_hours():
    generator = _make_generator(estimated_hours=40)
    result = generator.generate(
        title="Backend API", description="Build REST API with FastAPI",
        area="Backend", language="en", skills_required=["Python", "FastAPI"],
        budget_min=1000.0, summary="Full API development project.",
    )
    assert result.estimated_hours == 40
