from unittest.mock import MagicMock, call
from agents.proposal_generator import ProposalGenerator, ProposalResult


def _make_result(**kwargs):
    defaults = dict(
        proposal="Test proposal.",
        proposal_direct="Direct version.",
        proposal_consultive="Consultive version.",
        suggested_price=500.0,
        estimated_hours=20,
    )
    return ProposalResult(**{**defaults, **kwargs})


def _make_generator():
    gemini = MagicMock()
    gemini.generate_structured.return_value = _make_result()
    config = MagicMock()
    config.user_profile = {
        "skills": ["Python", "FastAPI", "BigQuery"],
        "min_budget_usd": 200,
        "languages": ["pt", "en"],
    }
    return ProposalGenerator(gemini, config), gemini


def _captured_prompt(gemini) -> str:
    return gemini.generate_structured.call_args[0][0]


def test_prompt_includes_required_skills():
    generator, gemini = _make_generator()
    generator.generate(
        title="Data pipeline", description="ETL job",
        area="Dados", language="en",
        skills_required=["dbt", "Spark"],
        budget_min=800.0, summary="Clean ETL task.",
    )
    prompt = _captured_prompt(gemini)
    assert "dbt" in prompt
    assert "Spark" in prompt


def test_prompt_includes_freelancer_skills():
    generator, gemini = _make_generator()
    generator.generate(
        title="API", description="Build REST API",
        area="Backend", language="en",
        skills_required=[], budget_min=500.0, summary="API task.",
    )
    prompt = _captured_prompt(gemini)
    assert "Python" in prompt
    assert "FastAPI" in prompt


def test_prompt_uses_portuguese_for_pt_language():
    generator, gemini = _make_generator()
    generator.generate(
        title="Automação", description="Scripts Excel",
        area="Automação", language="pt",
        skills_required=["Python"], budget_min=300.0, summary="Automação simples.",
    )
    prompt = _captured_prompt(gemini)
    assert "português" in prompt


def test_prompt_uses_english_for_en_language():
    generator, gemini = _make_generator()
    generator.generate(
        title="ML model", description="Train classifier",
        area="IA", language="en",
        skills_required=["sklearn"], budget_min=600.0, summary="ML task.",
    )
    prompt = _captured_prompt(gemini)
    assert "English" in prompt


def test_prompt_includes_budget_when_provided():
    generator, gemini = _make_generator()
    generator.generate(
        title="Backend", description="REST API",
        area="Backend", language="en",
        skills_required=[], budget_min=1500.0, summary="Big project.",
    )
    prompt = _captured_prompt(gemini)
    assert "1500" in prompt


def test_prompt_handles_missing_budget():
    generator, gemini = _make_generator()
    generator.generate(
        title="Script", description="Simple script",
        area="Python", language="en",
        skills_required=[], budget_min=None, summary="Small task.",
    )
    prompt = _captured_prompt(gemini)
    assert "não informado" in prompt


def test_prompt_requests_both_proposal_styles():
    generator, gemini = _make_generator()
    generator.generate(
        title="Pipeline", description="Data pipeline",
        area="Dados", language="en",
        skills_required=[], budget_min=500.0, summary="Pipeline task.",
    )
    prompt = _captured_prompt(gemini)
    assert "proposal_direct" in prompt
    assert "proposal_consultive" in prompt


def test_result_fields_are_passed_through():
    generator, gemini = _make_generator()
    gemini.generate_structured.return_value = _make_result(
        proposal_direct="Short and direct.",
        proposal_consultive="Long consultive version.",
        suggested_price=900.0,
        estimated_hours=35,
    )
    result = generator.generate(
        title="API", description="Build API",
        area="Backend", language="en",
        skills_required=[], budget_min=800.0, summary="API project.",
    )
    assert result.proposal_direct == "Short and direct."
    assert result.proposal_consultive == "Long consultive version."
    assert result.suggested_price == 900.0
    assert result.estimated_hours == 35
