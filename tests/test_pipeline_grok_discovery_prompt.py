from __future__ import annotations

from pipeline.grok_discovery import build_grok_discovery_prompt, synthetic_grok_result_for_tests
from pipeline.models import CorpOrg, GrokDiscoveryResult


def test_prompt_contains_exec_keywords() -> None:
    prompt = build_grok_discovery_prompt("https://zenithbank.com")
    assert "C-suite" in prompt or "CEO" in prompt or "executive" in prompt.lower()
    assert "hotel" not in prompt.lower()


def test_grok_discovery_result_has_corp_field() -> None:
    corp = CorpOrg(input_url="https://zenithbank.com", canonical_name="Zenith Bank")
    result = GrokDiscoveryResult(corp=corp, aliases=[], drafts=[])
    assert result.corp.canonical_name == "Zenith Bank"


def test_synthetic_result_corp_field() -> None:
    result = synthetic_grok_result_for_tests("https://zenithbank.com")
    assert isinstance(result.corp, CorpOrg)
    assert result.corp.input_url == "https://zenithbank.com"
