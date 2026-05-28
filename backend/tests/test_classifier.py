from unittest.mock import MagicMock
from agents.classifier import Classifier, ClassificationResult


def _make_classifier(area="Python"):
    gemini = MagicMock()
    gemini.generate_structured.return_value = ClassificationResult(area=area, reason="matches")
    return Classifier(gemini)


def test_classifier_returns_valid_area():
    classifier = _make_classifier("IA")
    result = classifier.classify("LLM Agent Builder", "Build an AI agent using GPT-4")
    assert result == "IA"


def test_classifier_returns_irrelevante():
    classifier = _make_classifier("Irrelevante")
    result = classifier.classify("WordPress Theme", "Need a WP designer")
    assert result == "Irrelevante"


def test_classifier_truncates_long_description():
    classifier = _make_classifier("Dados")
    long_desc = "x" * 2000
    result = classifier.classify("Data Pipeline", long_desc)
    call_args = classifier.gemini.generate_structured.call_args[0][0]
    assert len(call_args) < 1500
    assert result == "Dados"
