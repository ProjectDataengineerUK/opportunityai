import asyncio

from agents.sources.workana import WorkanaSource, _parse_budget, _title
from agents.sources.upwork import UpworkSource


# ---------- Workana ----------

def _workana_item(**over):
    item = {
        "slug": "python-ai-bot",
        "title": '<a href="/job/python-ai-bot"><span title="Build a Python AI bot">Build a...</span></a>',
        "description": "Need a <strong>Python</strong> dev for an AI automation bot.<br/>",
        "budget": "USD 500 - 1.000",
        "totalBids": "Propostas: 12",
        "hasVerifiedPaymentMethod": True,
    }
    item.update(over)
    return item


def test_workana_parse_extracts_fields():
    jobs = WorkanaSource._parse([_workana_item()])
    assert len(jobs) == 1
    job = jobs[0]
    assert job.external_id == "workana:python-ai-bot"
    assert job.source == "workana"
    assert job.title == "Build a Python AI bot"
    assert "Python" in job.description and "<strong>" not in job.description
    assert job.url == "https://www.workana.com/job/python-ai-bot"
    assert job.budget_min == 500.0 and job.budget_max == 1000.0
    assert job.budget_currency == "USD"
    assert job.language == "pt"


def test_workana_parse_filters_non_matching_keywords():
    item = _workana_item(
        slug="logo-design",
        title='<span title="Design a logo">Design a logo</span>',
        description="Looking for a graphic designer for a brand logo.",
    )
    assert WorkanaSource._parse([item]) == []


def test_workana_parse_dedupes_by_slug():
    jobs = WorkanaSource._parse([_workana_item(), _workana_item()])
    assert len(jobs) == 1


def test_workana_title_falls_back_to_stripped_html():
    item = {"title": "<a>Plain <b>Python</b> title</a>"}
    assert _title(item) == "Plain Python title"


def test_parse_budget_fixed_range():
    assert _parse_budget("USD 100 - 250") == (100.0, 250.0, "USD")


def test_parse_budget_less_than():
    assert _parse_budget("Menos de USD 50") == (None, 50.0, "USD")


def test_parse_budget_more_than_with_thousands():
    assert _parse_budget("Mais de USD 3.000") == (3000.0, None, "USD")


def test_parse_budget_hourly_has_no_amounts():
    assert _parse_budget("Menos de USD 15 / hora") == (None, None, "USD")


def test_parse_budget_empty():
    assert _parse_budget("") == (None, None, None)


# ---------- Upwork ----------

def test_upwork_no_token_returns_empty():
    assert asyncio.run(UpworkSource(token="").fetch()) == []


def test_upwork_parse_node_fixed_price():
    node = {
        "id": "123",
        "title": "ML Engineer",
        "description": "Build models",
        "ciphertext": "~01abc",
        "amount": {"rawValue": "1500", "currency": "USD"},
        "client": {"verificationStatus": "VERIFIED"},
    }
    job = UpworkSource._parse_node(node)
    assert job.external_id == "upwork:123"
    assert job.source == "upwork"
    assert job.budget_min == 1500.0 and job.budget_max is None
    assert job.url == "https://www.upwork.com/jobs/~01abc"


def test_upwork_parse_node_hourly_range():
    node = {
        "id": "9",
        "title": "Data pipeline",
        "ciphertext": "~09xyz",
        "amount": {"rawValue": None},
        "hourlyBudgetMin": {"rawValue": "25", "currency": "USD"},
        "hourlyBudgetMax": {"rawValue": "40", "currency": "USD"},
    }
    job = UpworkSource._parse_node(node)
    assert job.budget_min == 25.0 and job.budget_max == 40.0
    assert job.budget_currency == "USD"
