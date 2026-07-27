from __future__ import annotations

import json

from pipeline.models import (
    CandidateLead,
    CorpOrg,
    PipelineRunResult,
    PipelineTelemetry,
    ReviewRow,
    make_candidate_id,
)


def test_make_candidate_id_stable() -> None:
    a = make_candidate_id("zenithbank.com", "Jane Doe", "CEO")
    b = make_candidate_id("zenithbank.com", "Jane Doe", "CEO")
    assert a == b
    assert a.startswith("c_")


def test_corp_org_new_fields() -> None:
    corp = CorpOrg(
        input_url="https://zenithbank.com",
        hq_country="Nigeria",
        industry_sector="banking",
        revenue_estimate=">$1B",
        employee_count_estimate="5000+",
    )
    assert corp.hq_country == "Nigeria"
    assert corp.industry_sector == "banking"
    assert corp.revenue_estimate == ">$1B"


def test_candidate_lead_json_roundtrip() -> None:
    c = CandidateLead(
        candidate_id="c_x",
        full_name="A",
        title="CEO",
        role_tier=1,
        role_family="c_suite",
        current_role_confidence="high",
    )
    s = c.model_dump_json()
    c2 = CandidateLead.model_validate_json(s)
    assert c2.full_name == "A"


def test_pipeline_run_result_dump() -> None:
    r = PipelineRunResult(
        corp=CorpOrg(input_url="https://x.com"),
        candidates=[],
        review_rows=[],
        telemetry=PipelineTelemetry(),
    )
    d = r.model_dump()
    assert json.loads(json.dumps(d))["corp"]["input_url"] == "https://x.com"


def test_review_row_fields() -> None:
    row = ReviewRow(
        corp_name="Zenith Bank",
        corp_url="https://zenithbank.com",
        candidate_id="c1",
        full_name="N",
        title="T",
        company=None,
        role_tier=2,
        role_family="vp_level",
        current_role_confidence="medium",
        best_email=None,
        best_phone=None,
        linkedin_url=None,
        other_routes=None,
        needs_human_review=False,
        needs_contact_mining=True,
        evidence_urls="",
        evidence_summary="",
        notes="",
    )
    assert row.role_tier == 2
    assert row.corp_name == "Zenith Bank"
