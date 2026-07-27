from __future__ import annotations

from pipeline.config import PipelineConfig
from pipeline.grok_validation import validate_with_grok
from pipeline.models import CorpOrg, PipelineTelemetry, SourceRef


def test_validate_without_xai_heuristic() -> None:
    corp = CorpOrg(input_url="https://h.example", domains=["h.example"])
    ref = SourceRef(url="https://www.linkedin.com/in/x", title="Pat - GM", snippet="Pat is GM")
    pack = {
        "hotel": {"input_url": corp.input_url},
        "candidate_groups": [
            {
                "candidate_key": "pat|gm",
                "candidate_id": "c_heur",
                "name_hints": ["Pat"],
                "title_hints": ["GM"],
                "sources": [{"url": ref.url, "title": ref.title, "snippet": ref.snippet}],
            }
        ],
    }
    tel = PipelineTelemetry()
    out, usages = validate_with_grok(
        corp,
        pack,
        [ref],
        PipelineConfig(),
        None,
        tel,
    )
    assert not usages
    assert len(out) == 1
    assert out[0].full_name == "Pat"
    assert any("heuristic" in n for n in out[0].notes)
