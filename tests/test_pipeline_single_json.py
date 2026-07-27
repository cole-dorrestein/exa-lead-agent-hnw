from __future__ import annotations

from pipeline.io import build_pipeline_ui_json
from pipeline.models import CandidateLead, CorpOrg, OrgAlias, PipelineTelemetry


def test_pipeline_ui_json_shape() -> None:
    tel = PipelineTelemetry()
    tel.exa_search_requests = 2
    tel.exa_content_pages = 1
    tel.stages = []
    corp = CorpOrg(input_url="https://zenithbank.com/", canonical_name="Zenith Bank")
    aliases = [OrgAlias(value="Zenith Bank Nigeria", kind="property", confidence="high")]
    c = CandidateLead(
        candidate_id="c1",
        full_name="CEO",
        title="Chief Executive Officer",
        role_tier=1,
        role_family="c_suite",
        current_role_confidence="high",
        relationship_confidence="high",
    )
    ui = build_pipeline_ui_json(
        input_url="https://zenithbank.com/",
        resolved_org=corp,
        aliases=aliases,
        candidates=[c],
        rejected_candidates=[],
        telemetry=tel,
        needs_manual_org_review=False,
    )
    d = ui.model_dump()
    assert d["input_url"].startswith("https://")
    assert "xai_usd" in d["provider_costs"]
    assert "exa_usd" in d["provider_costs"]
    assert d["quality_metrics"]["candidate_count"] == 1
    assert d["quality_metrics"]["tier1_count"] == 1
