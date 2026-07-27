from __future__ import annotations

from scripts.discover_ssa_corps import generate_micro_verticals, extract_domain


def test_generate_micro_verticals_covers_all_combos() -> None:
    verticals = generate_micro_verticals(["banking", "mining"], ["nigeria", "south africa"])
    assert len(verticals) >= 4
    joined = " ".join(verticals).lower()
    assert "banking" in joined
    assert "mining" in joined
    assert "nigeria" in joined
    assert "south africa" in joined


def test_generate_micro_verticals_no_duplicates() -> None:
    verticals = generate_micro_verticals(["banking"], ["nigeria"])
    assert len(verticals) == len(set(verticals))


def test_extract_domain_strips_www() -> None:
    assert extract_domain("https://www.zenithbank.com/about") == "zenithbank.com"
    assert extract_domain("https://safaricom.co.ke") == "safaricom.co.ke"


def test_extract_domain_invalid_url_returns_empty() -> None:
    assert extract_domain("not-a-url") == ""
