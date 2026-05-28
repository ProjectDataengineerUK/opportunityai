from unittest.mock import MagicMock
from agents.fraud_detector import FraudDetector, FraudResult


def _make_detector(risk_score=10.0, flags=None):
    gemini = MagicMock()
    gemini.generate_structured.return_value = FraudResult(
        risk_score=risk_score,
        flags=flags or [],
        explanation="Análise concluída.",
    )
    return FraudDetector(gemini)


def test_safe_job_returns_low_risk():
    detector = _make_detector(risk_score=5.0)
    result = detector.analyze("Python Dev", "Build REST API", 500.0, 1000.0)
    assert result.risk_score < 30
    assert result.flags == []


def test_scam_job_returns_high_risk():
    detector = _make_detector(risk_score=90.0, flags=["pagamento fora da plataforma", "tarefa de teste gratuita"])
    result = detector.analyze("Easy Money", "Send me your CV and pay deposit", None, None)
    assert result.risk_score > 80
    assert len(result.flags) > 0


def test_result_has_explanation():
    detector = _make_detector(risk_score=40.0)
    result = detector.analyze("Data Engineer", "ETL pipeline work", 300.0, None)
    assert isinstance(result.explanation, str)
    assert len(result.explanation) > 0


def test_none_budget_is_accepted():
    detector = _make_detector(risk_score=15.0)
    result = detector.analyze("ML Engineer", "Train a model", None, None)
    assert result.risk_score == 15.0
