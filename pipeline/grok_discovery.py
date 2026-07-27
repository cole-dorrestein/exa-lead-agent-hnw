from __future__ import annotations

import json
import time
import uuid
from typing import Any

from pipeline.candidates import corp_key_from_org, make_candidate_id
from pipeline.models import CorpOrg, GrokDiscoveryResult
from pipeline.telemetry import record_xai_stage

try:
    from google.protobuf.json_format import MessageToDict
except ImportError:  # pragma: no cover
    MessageToDict = None  # type: ignore[misc, assignment]

GROK_DISCOVERY_MODEL = "grok-4.20-reasoning"


def _usage_to_dict(usage: Any) -> dict[str, Any]:
    if usage is None:
        return {}
    if MessageToDict is not None:
        try:
            return dict(MessageToDict(usage, preserving_proto_field_name=True))
        except TypeError:
            pass
    out: dict[str, Any] = {}
    for name in dir(usage):
        if name.startswith("_"):
            continue
        attr = getattr(usage, name, None)
        if callable(attr):
            continue
        if isinstance(attr, (int, float, str, bool)) or attr is None:
            out[name] = attr
    return out or {"repr": repr(usage)}


def build_grok_discovery_prompt(corp_url: str) -> str:
    return f"""Company URL (only input): {corp_url}

Tasks (use web_search and x_search; prefer official company sites, press releases, LinkedIn, regulatory filings, annual reports):

1) Resolve the company: canonical name, industry sector, HQ country and city, revenue estimate, employee count estimate.
2) Emit aliases (trading name / registered name / domain / historical names) with confidence high|medium|low, optional source_url and short quote.
3) Discover all C-suite officers, VPs, and Directors at this company (aim for 12-30 people).
   Include: CEO, CFO, COO, CTO, CMO, CISO, CHRO, Managing Director, VP-level (Vice President, SVP, EVP), Director-level.
   Exclude: regional heads, middle management, assistants.
4) For each person: evidence as SourceRef-style entries (url required when claiming a fact). contact_routes only when explicitly present in source text (never invent email or phone). linkedin_url when clearly the same person. confidence_hint high|medium|low and optional uncertainty string.

Rules: never fabricate emails or phone numbers. Focus on people who are currently in these roles, not former executives.

Return JSON matching the GrokDiscoveryResult schema (fields: corp, aliases, drafts)."""


def assign_draft_ids(result: GrokDiscoveryResult) -> GrokDiscoveryResult:
    key = corp_key_from_org(result.corp)
    out_drafts = []
    for d in result.drafts:
        did = d.draft_id or make_candidate_id(key, d.full_name, d.title)
        out_drafts.append(d.model_copy(update={"draft_id": did}))
    return result.model_copy(update={"drafts": out_drafts})


def run_grok_discovery(
    corp_url: str,
    api_key: str,
    telemetry: Any,
    *,
    max_turns: int = 24,
) -> tuple[GrokDiscoveryResult, dict[str, Any]]:
    """Single Grok 4.20 reasoning call: org resolution + draft candidates."""
    from xai_sdk import Client
    from xai_sdk.chat import user
    from xai_sdk.tools import web_search, x_search

    t0 = time.perf_counter()
    client = Client(api_key=api_key)
    chat = client.chat.create(
        model=GROK_DISCOVERY_MODEL,
        tools=[web_search(), x_search()],
        store_messages=True,
        max_turns=max_turns,
        response_format=GrokDiscoveryResult,
    )
    chat.append(user(build_grok_discovery_prompt(corp_url.strip())))
    final = chat.sample()
    raw = (final.content or "").strip()
    if not raw:
        raise ValueError("Empty Grok discovery response")
    parsed = GrokDiscoveryResult.model_validate_json(raw)
    if not parsed.corp.input_url:
        parsed = parsed.model_copy(update={"corp": parsed.corp.model_copy(update={"input_url": corp_url.strip()})})
    parsed = assign_draft_ids(parsed)
    usage = _usage_to_dict(getattr(final, "usage", None))
    record_xai_stage(
        telemetry,
        stage="grok_discovery",
        usages=[usage],
        seconds=time.perf_counter() - t0,
        notes=["grok-4.20-reasoning discovery"],
    )
    return parsed, usage


def grok_discovery_dry_run_plan(corp_url: str) -> dict[str, Any]:
    """Deterministic plan blob for CLI dry-run (no API keys)."""
    return {
        "pipeline_version": 4,
        "corp_url": corp_url,
        "stages": ["grok_discovery", "gap_planner", "exa_verify", "local_validation", "contact_routes"],
        "grok_model": GROK_DISCOVERY_MODEL,
        "exa_policy": "capped_jobs_only",
        "note": "Use XAI_API_KEY for live grok_discovery; EXA_API_KEY for Exa jobs.",
    }


def parse_grok_discovery_json(data: str | dict[str, Any]) -> GrokDiscoveryResult:
    """Test helper: parse JSON object or string into GrokDiscoveryResult."""
    obj = json.loads(data) if isinstance(data, str) else data
    return assign_draft_ids(GrokDiscoveryResult.model_validate(obj))


def synthetic_grok_result_for_tests(corp_url: str = "https://zenithbank.com/") -> GrokDiscoveryResult:
    """Minimal fixture: Zenith Bank alias + one draft (unit tests)."""
    corp = CorpOrg(
        input_url=corp_url,
        canonical_name="Zenith Bank",
        industry_sector="banking",
        hq_country="Nigeria",
        domains=["zenithbank.com"],
        evidence=[],
    )
    from pipeline.models import CandidateDraft, OrgAlias

    aliases = [
        OrgAlias(
            value="Zenith Bank Nigeria",
            kind="property",
            confidence="high",
            source_url=corp_url,
            quote="Zenith Bank Nigeria",
        ),
    ]
    drafts = [
        CandidateDraft(
            full_name="Example CEO",
            title="Chief Executive Officer",
            company="Zenith Bank",
            evidence=[],
            confidence_hint="medium",
            uncertainty=None,
        )
    ]
    return assign_draft_ids(GrokDiscoveryResult(corp=corp, aliases=aliases, drafts=drafts))


def new_job_id() -> str:
    return uuid.uuid4().hex[:12]
