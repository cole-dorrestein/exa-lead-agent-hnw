from __future__ import annotations

from pipeline.candidates import (
    classify_role_family,
    classify_role_tier,
    dedupe_candidates,
    infer_current_role_confidence_from_text,
    normalize_name,
    parse_linkedin_result_title,
)
from pipeline.models import CandidateLead, SourceRef


def test_normalize_name() -> None:
    assert normalize_name("  Jane   Doe  ") == "Jane Doe"


def test_classify_gm_tier1() -> None:
    # General Manager is no longer a special tier-1 role in the corp exec model
    assert classify_role_tier("General Manager") == 3
    assert classify_role_family("General Manager") == "other"


def test_classify_sales_tier2() -> None:
    # Director of Sales is director_level family, tier 3 in the corp exec model
    assert classify_role_tier("Director of Sales") == 3
    assert classify_role_family("Director of Sales") == "director_level"


def test_former_title_low_confidence() -> None:
    assert infer_current_role_confidence_from_text("GM", "Former General Manager at X") == "low"


def test_parse_linkedin_title() -> None:
    n, t = parse_linkedin_result_title("Jane Doe - General Manager | LinkedIn")
    assert n == "Jane Doe"
    assert t == "General Manager"


def test_dedupe_merges_linkedin() -> None:
    s = SourceRef(url="https://www.linkedin.com/in/jane", title="Jane - GM", snippet="x")
    a = CandidateLead(
        candidate_id="a",
        full_name="Jane",
        title="GM",
        role_tier=1,
        role_family="c_suite",
        current_role_confidence="high",
        evidence=[s],
        linkedin_url="https://www.linkedin.com/in/jane",
    )
    b = CandidateLead(
        candidate_id="b",
        full_name="Jane",
        title="GM",
        role_tier=1,
        role_family="c_suite",
        current_role_confidence="high",
        evidence=[s],
        linkedin_url="https://www.linkedin.com/in/jane",
    )
    out = dedupe_candidates([a, b])
    assert len(out) == 1


def test_classify_role_family_c_suite() -> None:
    from pipeline.candidates import classify_role_family
    assert classify_role_family("CEO") == "c_suite"
    assert classify_role_family("Chief Financial Officer") == "c_suite"
    assert classify_role_family("Managing Director") == "c_suite"
    assert classify_role_family("Chief Operating Officer") == "c_suite"


def test_classify_role_family_vp() -> None:
    from pipeline.candidates import classify_role_family
    assert classify_role_family("VP of Finance") == "vp_level"
    assert classify_role_family("Vice President Operations") == "vp_level"


def test_classify_role_family_director() -> None:
    from pipeline.candidates import classify_role_family
    assert classify_role_family("Director of Marketing") == "director_level"
    assert classify_role_family("Finance Director") == "director_level"


def test_classify_role_tier_c_suite_is_tier1() -> None:
    from pipeline.candidates import classify_role_tier
    assert classify_role_tier("CEO") == 1
    assert classify_role_tier("CFO") == 1
    assert classify_role_tier("Managing Director") == 1


def test_classify_role_tier_vp_is_tier2() -> None:
    from pipeline.candidates import classify_role_tier
    assert classify_role_tier("Vice President of Operations") == 2
    assert classify_role_tier("VP Finance") == 2


def test_classify_role_tier_director_is_tier3() -> None:
    from pipeline.candidates import classify_role_tier
    assert classify_role_tier("Director of Sales") == 3


def test_initial_corp_from_url() -> None:
    from pipeline.candidates import initial_corp_from_url
    from pipeline.models import CorpOrg
    corp = initial_corp_from_url("https://zenithbank.com")
    assert isinstance(corp, CorpOrg)
    assert corp.input_url == "https://zenithbank.com"
    assert "zenithbank.com" in corp.domains
