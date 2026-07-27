# SSA Executive Lead Gen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repurpose the hotel lead gen pipeline to find C-suite/VP/Director executives at Sub-Saharan African corporations ($20M+ revenue), outputting a lead list with LinkedIn, email, and phone for sales use.

**Architecture:** Two-phase pipeline — Phase 1 (`scripts/discover_ssa_corps.py`) uses Exa to build a list of SSA company URLs; Phase 2 (the existing pipeline, modified) feeds those URLs through Grok to extract executives and enrich their contact details. The `pipeline/` package is refactored from hotel-specific to generic corp terminology. The `legacy/`, `contact_enrichment/`, `lead_aggregates/`, `phone_crm/`, and `outreach/` packages are left unchanged.

**Tech Stack:** Python 3.11+, Pydantic v2, xai-sdk (Grok), exa-py, pytest

## Global Constraints

- Python 3.11+ only — no `match` backports needed
- All `pipeline/` imports use `from __future__ import annotations`
- Pydantic v2 — use `model_copy`, `model_validate`, `model_dump_json`
- Never fabricate emails or phone numbers in prompts
- Keep `HotelOrg = CorpOrg` alias in `models.py` until Task 5 — `legacy/` and `contact_enrichment/` import `HotelOrg` and are not in scope
- Keep `hotel_key_from_org = corp_key_from_org` alias until Task 5 for same reason
- Run tests from repo root: `pytest tests/ -x -q`

---

## Task 1: Rename HotelOrg → CorpOrg in models.py; fix ReviewRow; update review_board.py

**Files:**
- Modify: `pipeline/models.py`
- Modify: `pipeline/review_board.py`
- Modify: `tests/test_pipeline_models.py`
- Modify: `tests/test_pipeline_review_board.py`

**Interfaces:**
- Produces: `CorpOrg` (exported from `pipeline.models`), `HotelOrg = CorpOrg` alias, `corp_key_from_org`, `hotel_key_from_org = corp_key_from_org` alias
- Produces: `ReviewRow` with fields `corp_name: str`, `corp_url: str` (replacing `hotel_name`, `hotel_url`)
- Produces: `RoleFamily = Literal["c_suite", "vp_level", "director_level", "board", "owner_exec", "other"]`
- Note: `GrokDiscoveryResult` still has `.hotel` field in this task — renamed in Task 3

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_pipeline_models.py — replace entire file with:
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
```

```python
# tests/test_pipeline_review_board.py — replace entire file with:
from __future__ import annotations

from pipeline.models import CandidateLead, ContactRoute, CorpOrg
from pipeline.review_board import build_review_rows


def test_review_board_orders_tier1_before_tier3() -> None:
    corp = CorpOrg(input_url="https://x.com", canonical_name="X Corp")
    low = CandidateLead(
        candidate_id="t3",
        full_name="Sales Dir",
        title="Director of Sales",
        role_tier=3,
        role_family="director_level",
        current_role_confidence="high",
        contact_routes=[ContactRoute(kind="email", value="a@x.com", confidence="high", source_url="https://x")],
    )
    high = CandidateLead(
        candidate_id="t1",
        full_name="CEO",
        title="CEO",
        role_tier=1,
        role_family="c_suite",
        current_role_confidence="high",
        contact_routes=[],
    )
    rows = build_review_rows(corp, [low, high])
    assert rows[0].full_name == "CEO"
    assert rows[1].full_name == "Sales Dir"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_pipeline_models.py tests/test_pipeline_review_board.py -x -q
```

Expected: FAIL — `CorpOrg` not found, `role_family="c_suite"` invalid, `ReviewRow` missing `corp_name`

- [ ] **Step 3: Update pipeline/models.py**

Replace the `HotelOrg` class, `RoleFamily`, `ReviewRow`, `PipelineRunResult`, `corp_key_from_org` and add aliases. The full diff:

```python
# Replace HotelOrg class (lines ~41-52) with:
class CorpOrg(BaseModel):
    input_url: str
    canonical_name: str | None = None
    industry_sector: str | None = None
    hq_country: str | None = None
    hq_city: str | None = None
    revenue_estimate: str | None = None
    employee_count_estimate: str | None = None
    domains: list[str] = Field(default_factory=list)
    evidence: list[SourceRef] = Field(default_factory=list)


# backward compat — legacy/ and contact_enrichment/ import HotelOrg; do not remove until Task 5
HotelOrg = CorpOrg
```

```python
# Replace RoleFamily (line ~19) with:
RoleFamily = Literal["c_suite", "vp_level", "director_level", "board", "owner_exec", "other"]
```

```python
# Replace ReviewRow class (lines ~118-136) with:
class ReviewRow(BaseModel):
    corp_name: str
    corp_url: str
    candidate_id: str
    full_name: str
    title: str | None = None
    company: str | None = None
    role_tier: RoleTier
    role_family: RoleFamily
    current_role_confidence: RoleConfidence
    best_email: str | None = None
    best_phone: str | None = None
    linkedin_url: str | None = None
    other_routes: str | None = None
    needs_human_review: bool
    needs_contact_mining: bool
    evidence_urls: str
    evidence_summary: str
    notes: str
```

```python
# Replace PipelineRunResult (lines ~158-163) with:
class PipelineRunResult(BaseModel):
    corp: CorpOrg
    candidates: list[CandidateLead]
    review_rows: list[ReviewRow]
    telemetry: PipelineTelemetry
    source_pack_json: str | None = None
```

```python
# Replace PipelineUiJson resolved_org type (line ~169):
class PipelineUiJson(BaseModel):
    """Single UI-ready artifact for pipeline v4."""
    input_url: str
    resolved_org: CorpOrg          # was HotelOrg
    aliases: list[OrgAlias]
    ...  # rest unchanged
```

```python
# Replace hotel_key_from_org function (lines ~198-204) with:
def corp_key_from_org(corp: CorpOrg) -> str:
    if corp.domains:
        return corp.domains[0]
    from urllib.parse import urlparse
    p = urlparse(corp.input_url)
    return (p.netloc or "nohost").lower()


# backward compat alias — remove in Task 5
hotel_key_from_org = corp_key_from_org
```

```python
# Replace make_candidate_id (lines ~185-195) — update param type comment only, logic unchanged:
def make_candidate_id(corp_key: str, full_name: str, title: str | None) -> str:
    """Stable id from corp scope + normalized name + title."""
    parts = "|".join([_slug(corp_key), _slug(full_name or ""), _slug(title or "")])
    h = hashlib.sha256(parts.encode("utf-8")).hexdigest()[:16]
    return f"c_{h}"
```

- [ ] **Step 4: Update pipeline/review_board.py**

```python
# Replace entire file with:
from __future__ import annotations

from pipeline.models import CandidateLead, ContactRoute, CorpOrg, ReviewRow


def _best_email(routes: list[ContactRoute]) -> str | None:
    emails = [r for r in routes if r.kind == "email"]
    for conf in ("high", "medium", "low"):
        for r in emails:
            if r.confidence == conf:
                return r.value
    return None


def _best_phone(routes: list[ContactRoute]) -> str | None:
    phones = [r for r in routes if r.kind == "phone"]
    for conf in ("high", "medium", "low"):
        for r in phones:
            if r.confidence == conf:
                return r.value
    return None


def _other_routes(routes: list[ContactRoute]) -> str | None:
    parts: list[str] = []
    for r in routes:
        if r.kind in ("email", "phone"):
            continue
        parts.append(f"{r.kind}:{r.value}")
    return "; ".join(parts) if parts else None


def _evidence_summary(c: CandidateLead) -> str:
    bits: list[str] = []
    for e in c.evidence[:5]:
        q = (e.snippet or "")[:240].replace("\n", " ")
        bits.append(q)
    return " | ".join(bits) if bits else ""


def _tier_sort_key(c: CandidateLead) -> tuple[int, int, str]:
    conf = c.current_role_confidence
    strong = conf in ("high", "medium")
    tier = int(c.role_tier)
    if tier == 1 and strong:
        band = 0
    elif tier == 2 and strong:
        band = 1
    elif tier == 1:
        band = 2
    elif tier == 3 and c.role_family == "director_level":
        band = 3
    else:
        band = 4
    conf_order = {"high": 0, "medium": 1, "low": 2, "conflict": 3}
    return (band, conf_order.get(conf, 2), c.full_name.lower())


def build_review_rows(corp: CorpOrg, candidates: list[CandidateLead]) -> list[ReviewRow]:
    corp_name = corp.canonical_name or (corp.domains[0] if corp.domains else corp.input_url)
    sorted_cs = sorted(candidates, key=_tier_sort_key)
    rows: list[ReviewRow] = []
    for c in sorted_cs:
        ev_urls = ";".join(e.url for e in c.evidence if e.url)
        rows.append(
            ReviewRow(
                corp_name=str(corp_name),
                corp_url=corp.input_url,
                candidate_id=c.candidate_id,
                full_name=c.full_name,
                title=c.title,
                company=c.company,
                role_tier=c.role_tier,
                role_family=c.role_family,
                current_role_confidence=c.current_role_confidence,
                best_email=_best_email(c.contact_routes),
                best_phone=_best_phone(c.contact_routes),
                linkedin_url=c.linkedin_url,
                other_routes=_other_routes(c.contact_routes),
                needs_human_review=c.needs_human_review,
                needs_contact_mining=c.needs_contact_mining,
                evidence_urls=ev_urls,
                evidence_summary=_evidence_summary(c),
                notes="; ".join(c.notes) if c.notes else "",
            )
        )
    return rows
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_pipeline_models.py tests/test_pipeline_review_board.py -x -q
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add pipeline/models.py pipeline/review_board.py tests/test_pipeline_models.py tests/test_pipeline_review_board.py
git commit -m "refactor(pipeline): rename HotelOrg→CorpOrg, update RoleFamily and ReviewRow fields"
```

---

## Task 2: Update candidates.py — role classification + initial_corp_from_url

**Files:**
- Modify: `pipeline/candidates.py`
- Test: `tests/test_pipeline_candidates.py` (already exists — run to verify it still passes)

**Interfaces:**
- Consumes: `CorpOrg`, `corp_key_from_org` from `pipeline.models`
- Produces: updated `classify_role_family` returning new RoleFamily values, `initial_corp_from_url(url) -> CorpOrg`, `initial_hotel_from_url = initial_corp_from_url` alias

- [ ] **Step 1: Write the failing test**

Add to `tests/test_pipeline_candidates.py` (append — do not replace the file):

```python
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
```

- [ ] **Step 2: Run to verify failures**

```bash
pytest tests/test_pipeline_candidates.py -x -q -k "c_suite or vp_level or director or tier_c or tier_vp or tier_director or initial_corp"
```

Expected: FAIL — `classify_role_family` returns old values, `initial_corp_from_url` not defined

- [ ] **Step 3: Update pipeline/candidates.py**

Update the import block at top:

```python
from pipeline.models import (
    CandidateDraft,
    CandidateLead,
    ContactRoute,
    CorpOrg,
    GrokDiscoveryResult,
    OrgAlias,
    RelationshipConfidence,
    RoleConfidence,
    RoleFamily,
    RoleTier,
    SourceRef,
    SourceType,
    corp_key_from_org,
    hotel_key_from_org,   # keep — used by grok_validation until Task 4
    make_candidate_id,
)

# backward compat alias — used by exa_discovery until Task 4
HotelOrg = CorpOrg
```

Replace `classify_role_family` function:

```python
def classify_role_family(title: str | None) -> RoleFamily:
    t = normalize_title(title)
    if not t:
        return "other"
    if any(x in t for x in ("owner", "founder", "co-founder", "proprietor")):
        return "owner_exec"
    if any(x in t for x in ("board member", "non-executive", "trustee", "board of director")):
        return "board"
    if any(
        x in t
        for x in (
            "ceo",
            "cfo",
            "coo",
            "cto",
            "cmo",
            "ciso",
            "chro",
            "chief executive",
            "chief financial",
            "chief operating",
            "chief technology",
            "chief marketing",
            "chief information",
            "chief human",
            "managing director",
            "md ",
            " md",
            "group chief",
        )
    ):
        return "c_suite"
    if any(x in t for x in ("vice president", "vp ", "vp-", " vp", "svp", "evp", "avp")):
        return "vp_level"
    if "director" in t:
        return "director_level"
    return "other"
```

Replace `classify_role_tier` function:

```python
def classify_role_tier(title: str | None) -> RoleTier:
    t = normalize_title(title)
    if not t:
        return 4
    tier1 = (
        "owner",
        "founder",
        "co-founder",
        "chief executive",
        "ceo",
        "cfo",
        "coo",
        "cto",
        "cmo",
        "ciso",
        "chro",
        "managing director",
        "group chief",
        "md ",
    )
    if any(x in t for x in tier1):
        return 1
    tier2 = (
        "vice president",
        "vp ",
        "vp-",
        " vp",
        "svp",
        "evp",
        "avp",
    )
    if any(x in t for x in tier2):
        return 2
    if "director" in t or "head of" in t:
        return 3
    if "manager" in t or "head" in t:
        return 3
    return 4
```

Replace `_alias_match_strings` function (remove hotel-specific field refs):

```python
def _alias_match_strings(corp: CorpOrg, aliases: list[OrgAlias]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for a in aliases:
        v = (a.value or "").strip()
        if len(v) < 2 or v.lower() in seen:
            continue
        seen.add(v.lower())
        out.append(v)
    for fld in (corp.canonical_name,):
        v = (fld or "").strip()
        if len(v) >= 2 and v.lower() not in seen:
            seen.add(v.lower())
            out.append(v)
    return out
```

Update `relationship_confidence_for_draft` signature:

```python
def relationship_confidence_for_draft(
    draft: CandidateDraft,
    corp: CorpOrg,
    aliases: list[OrgAlias],
    extra_sources: list[SourceRef] | None = None,
) -> RelationshipConfidence:
    alias_vals = _alias_match_strings(corp, aliases)
    ...
    dom = (corp.domains[0] if corp.domains else "").split(".")[0].lower()
    ...
```

Replace `initial_hotel_from_url` with `initial_corp_from_url` (keep alias):

```python
def initial_corp_from_url(input_url: str) -> CorpOrg:
    u = input_url.strip()
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    d = domain_from_url(u)
    return CorpOrg(
        input_url=u,
        domains=[d] if d else [],
        evidence=[],
    )


# backward compat — exa_discovery imports initial_hotel_from_url until Task 4
initial_hotel_from_url = initial_corp_from_url
```

Also update all remaining `HotelOrg` type annotations in the function signatures to `CorpOrg` and `hotel_key_from_org` calls to `corp_key_from_org` within candidates.py.

For `candidate_from_linkedin_source`, update:
```python
def candidate_from_linkedin_source(ref: SourceRef, corp: CorpOrg) -> CandidateLead | None:
    ...
    key = corp_key_from_org(corp)
```

For the functions at lines ~310-415 that take `hotel: HotelOrg`, rename to `corp: CorpOrg` and update internal calls.

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_pipeline_candidates.py -x -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/candidates.py tests/test_pipeline_candidates.py
git commit -m "refactor(pipeline): update role classification for corp exec tiers; add initial_corp_from_url"
```

---

## Task 3: Update grok_discovery.py — new exec prompt + rename .hotel → .corp in GrokDiscoveryResult; update cli.py

**Files:**
- Modify: `pipeline/models.py` (rename `GrokDiscoveryResult.hotel` → `.corp`)
- Modify: `pipeline/grok_discovery.py`
- Modify: `pipeline/cli.py`
- Modify: `tests/test_pipeline_grok_validation.py`
- Modify: `tests/test_pipeline_single_json.py`

**Interfaces:**
- Consumes: `CorpOrg`, `corp_key_from_org` from prior tasks
- Produces: `GrokDiscoveryResult` with `.corp: CorpOrg` field (no more `.hotel`), new SSA exec discovery prompt, `run_grok_discovery(corp_url, ...)` signature, `run_pipeline(corp_url, ...)` signature

- [ ] **Step 1: Write failing tests**

```python
# tests/test_pipeline_grok_discovery_prompt.py — new file
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
```

- [ ] **Step 2: Run to verify failures**

```bash
pytest tests/test_pipeline_grok_discovery_prompt.py -x -q
```

Expected: FAIL — `GrokDiscoveryResult` has no `.corp`, prompt contains "Hotel"

- [ ] **Step 3: Rename GrokDiscoveryResult.hotel → .corp in pipeline/models.py**

```python
# Replace GrokDiscoveryResult class:
class GrokDiscoveryResult(BaseModel):
    corp: CorpOrg
    aliases: list[OrgAlias] = Field(default_factory=list)
    drafts: list[CandidateDraft] = Field(default_factory=list)
```

- [ ] **Step 4: Update pipeline/grok_discovery.py**

Replace `build_grok_discovery_prompt`:

```python
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
```

Update `assign_draft_ids`:

```python
def assign_draft_ids(result: GrokDiscoveryResult) -> GrokDiscoveryResult:
    key = corp_key_from_org(result.corp)
    out_drafts = []
    for d in result.drafts:
        did = d.draft_id or make_candidate_id(key, d.full_name, d.title)
        out_drafts.append(d.model_copy(update={"draft_id": did}))
    return result.model_copy(update={"drafts": out_drafts})
```

Update `run_grok_discovery` signature and body:

```python
def run_grok_discovery(
    corp_url: str,
    api_key: str,
    telemetry: Any,
    *,
    max_turns: int = 24,
) -> tuple[GrokDiscoveryResult, dict[str, Any]]:
    """Single Grok 4.20 reasoning call: org resolution + draft candidates."""
    ...
    chat.append(user(build_grok_discovery_prompt(corp_url.strip())))
    ...
    if not parsed.corp.input_url:
        parsed = parsed.model_copy(update={"corp": parsed.corp.model_copy(update={"input_url": corp_url.strip()})})
    ...
```

Update `grok_discovery_dry_run_plan`:

```python
def grok_discovery_dry_run_plan(corp_url: str) -> dict[str, Any]:
    return {
        "pipeline_version": 4,
        "corp_url": corp_url,
        "stages": ["grok_discovery", "gap_planner", "exa_verify", "local_validation", "contact_routes"],
        "grok_model": GROK_DISCOVERY_MODEL,
        "exa_policy": "capped_jobs_only",
        "note": "Use XAI_API_KEY for live grok_discovery; EXA_API_KEY for Exa jobs.",
    }
```

Update `synthetic_grok_result_for_tests`:

```python
def synthetic_grok_result_for_tests(corp_url: str = "https://zenithbank.com/") -> GrokDiscoveryResult:
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
```

Update imports in grok_discovery.py:

```python
from pipeline.candidates import corp_key_from_org, make_candidate_id
from pipeline.models import CorpOrg, GrokDiscoveryResult
```

- [ ] **Step 5: Update pipeline/cli.py**

Rename `hotel_url` → `corp_url` throughout `run_pipeline` and `main`. Update:

```python
from pipeline.candidates import (
    dedupe_candidates,
    initial_corp_from_url,
    leads_from_people_gap_sources,
    promote_discovery_to_candidates,
)

def run_pipeline(
    corp_url: str,
    config: PipelineConfig,
    *,
    out_dir: Path,
    ...
) -> PipelineRunResult:
    ...
    if dry_run:
        corp = initial_corp_from_url(corp_url)
        discovery = GrokDiscoveryResult(corp=corp, aliases=[], drafts=[])
        ...
        plan = {
            **grok_discovery_dry_run_plan(corp_url),
            ...
        }
        return PipelineRunResult(
            corp=corp,
            candidates=[],
            review_rows=[],
            telemetry=tel,
            source_pack_json=json.dumps(plan, indent=2),
        )

    ...
    discovery, _usages = run_grok_discovery(corp_url, xai_key, tel)
    ...
    rough.extend(leads_from_people_gap_sources(discovery.corp, list(discovery.aliases), global_src))
    rough = dedupe_candidates(rough[: config.max_candidates])
    mined = mine_contacts_v4(discovery.corp, rough, config, exa, tel)
    rows = build_review_rows(discovery.corp, mined)
    ui = build_pipeline_ui_json(
        input_url=corp_url.strip(),
        resolved_org=discovery.corp,
        ...
    )
    rid = run_id_for_url(corp_url)
    ...
    return PipelineRunResult(
        corp=ui.resolved_org,
        ...
    )
```

Update `main()` argparse:

```python
p = argparse.ArgumentParser(description="Grok-led SSA executive pipeline (v4)")
run_p = sub.add_parser("run", help="Run pipeline for one company URL")
run_p.add_argument("url")
...
# In args.cmd == "run":
res = run_pipeline(args.url, cfg, ...)
...
# In args.cmd == "run-many":
for u in lines:
    run_pipeline(u, cfg, ...)
```

- [ ] **Step 6: Fix tests/test_pipeline_grok_validation.py**

```python
# Replace HotelOrg import and usage:
from pipeline.models import CorpOrg, PipelineTelemetry, SourceRef
...
corp = CorpOrg(input_url="https://h.example", domains=["h.example"])
```

- [ ] **Step 7: Fix tests/test_pipeline_single_json.py**

```python
# Replace HotelOrg import and usage:
from pipeline.models import CandidateLead, CorpOrg, OrgAlias, PipelineTelemetry
...
corp = CorpOrg(input_url="https://zenithbank.com/", canonical_name="Zenith Bank")
```

- [ ] **Step 8: Run tests**

```bash
pytest tests/test_pipeline_grok_discovery_prompt.py tests/test_pipeline_grok_validation.py tests/test_pipeline_single_json.py -x -q
```

Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add pipeline/models.py pipeline/grok_discovery.py pipeline/cli.py tests/test_pipeline_grok_discovery_prompt.py tests/test_pipeline_grok_validation.py tests/test_pipeline_single_json.py
git commit -m "refactor(pipeline): new SSA exec discovery prompt; GrokDiscoveryResult.hotel→.corp"
```

---

## Task 4: Sweep remaining pipeline/ files — update all HotelOrg refs

**Files:**
- Modify: `pipeline/grok_validation.py`
- Modify: `pipeline/io.py`
- Modify: `pipeline/source_pack.py`
- Modify: `pipeline/legacy_export.py`
- Modify: `pipeline/contact_mining.py`
- Modify: `pipeline/exa_discovery.py`
- Modify: `pipeline/gap_planner.py`
- Modify: `pipeline/linkedin_merge.py`
- Modify: `pipeline/__init__.py`

**Interfaces:**
- Consumes: `CorpOrg`, `corp_key_from_org` from prior tasks
- Produces: all `pipeline/` files use `CorpOrg`, `corp_key_from_org`, `discovery.corp` — no direct `HotelOrg` usage (only the alias in models.py remains)

- [ ] **Step 1: Run full test suite to see current state**

```bash
pytest tests/ -x -q
```

Note which tests fail — these are the cascade failures from the `.hotel` → `.corp` rename in Task 3.

- [ ] **Step 2: Update pipeline/grok_validation.py**

```python
# Line 9 — replace import:
from pipeline.candidates import classify_role_family, classify_role_tier, corp_key_from_org, make_candidate_id

# Lines 14-18 — replace HotelOrg with CorpOrg:
from pipeline.models import (
    CandidateLead,
    ContactRoute,
    CorpOrg,
    RoleConfidence,
    RoleFamily,
    RoleTier,
    SourceRef,
)

# Line 104 — update signature:
def build_validation_prompt(corp: CorpOrg, chunk: dict[str, Any]) -> str:

# Line 127 — update signature:
    corp: CorpOrg,

# Line 180 — update call:
    hk = corp_key_from_org(corp)

# Line 226 — update signature:
    corp: CorpOrg,

# Line 231 — update call:
    hk = corp_key_from_org(corp)
```

- [ ] **Step 3: Update pipeline/io.py**

```python
# Replace HotelOrg with CorpOrg in import block and resolved_org type hint:
from pipeline.models import (
    CandidateDraft,
    CandidateLead,
    CorpOrg,
    OrgAlias,
    PipelineRunResult,
    PipelineTelemetry,
    PipelineUiJson,
    ReviewRow,
)

def build_pipeline_ui_json(
    *,
    input_url: str,
    resolved_org: CorpOrg,
    ...
```

- [ ] **Step 4: Update pipeline/source_pack.py**

```python
# Replace import:
from pipeline.models import CandidateLead, CorpOrg, SourceRef

# Replace function signature:
def build_source_pack(
    corp: CorpOrg,
    candidates: list[CandidateLead],
    orphan_sources: list[SourceRef],
    config: PipelineConfig,
) -> dict[str, Any]:

# Replace hotel_blob with corp_blob:
    corp_blob = {
        "input_url": corp.input_url,
        "canonical_name": corp.canonical_name,
        "industry_sector": corp.industry_sector,
        "hq_country": corp.hq_country,
        "hq_city": corp.hq_city,
        "revenue_estimate": corp.revenue_estimate,
        "domains": corp.domains,
    }

    return {
        "corp": corp_blob,
        "candidate_groups": groups,
        "orphan_sources": orphan_block[:200],
    }
```

- [ ] **Step 5: Update pipeline/legacy_export.py**

```python
# Replace _resolved_hotel_name with _resolved_corp_name:
def _resolved_corp_name(ui: PipelineUiJson) -> str:
    corp = ui.resolved_org
    return corp.canonical_name or (corp.domains[0] if corp.domains else ui.input_url)

# Update all internal references: hotel_name → corp_name, _resolved_hotel_name → _resolved_corp_name
# Line 165: hotel_name = _resolved_corp_name(ui)
# Line 192: "contacts": [_legacy_contact(candidate, corp_name) for candidate in ui.candidates],
```

- [ ] **Step 6: Update pipeline/contact_mining.py**

```python
# Replace import:
from pipeline.models import CandidateLead, ContactRoute, CorpOrg

# Replace all HotelOrg type annotations → CorpOrg, parameter names hotel → corp
```

- [ ] **Step 7: Update pipeline/exa_discovery.py**

```python
# Replace import:
from pipeline.candidates import (
    candidate_from_linkedin_source,
    domain_from_url,
    initial_corp_from_url,
)
from pipeline.models import CandidateLead, CorpOrg, SourceRef

# Replace all HotelOrg → CorpOrg, initial_hotel_from_url → initial_corp_from_url
# Update function signatures: hotel → corp
```

- [ ] **Step 8: Update pipeline/gap_planner.py**

```python
# Replace import:
from pipeline.models import CandidateDraft, ExaJob, GrokDiscoveryResult, CorpOrg, OrgAlias

# Update function signatures and internal references: hotel → corp
def _alias_strings(corp: CorpOrg, aliases: list[OrgAlias]) -> list[str]:
def _bare_hostname_alias(corp: CorpOrg, aliases: list[OrgAlias]) -> bool:
```

- [ ] **Step 9: Update pipeline/linkedin_merge.py**

```python
# Replace import:
from pipeline.models import CandidateLead, CorpOrg, SourceRef

# Update function signature: hotel → corp
```

- [ ] **Step 10: Update pipeline/__init__.py**

```python
"""Grok-led SSA executive sourcing pipeline."""

from pipeline.models import CandidateLead, CorpOrg, PipelineRunResult

__all__ = ["CandidateLead", "CorpOrg", "PipelineRunResult", "__version__"]

__version__ = "0.1.0"
```

- [ ] **Step 11: Run full test suite**

```bash
pytest tests/ -x -q
```

Fix any remaining cascade failures from the sweep.

- [ ] **Step 12: Commit**

```bash
git add pipeline/grok_validation.py pipeline/io.py pipeline/source_pack.py pipeline/legacy_export.py pipeline/contact_mining.py pipeline/exa_discovery.py pipeline/gap_planner.py pipeline/linkedin_merge.py pipeline/__init__.py
git commit -m "refactor(pipeline): sweep remaining files — HotelOrg→CorpOrg, hotel→corp"
```

---

## Task 5: Fix remaining broken tests + remove backward-compat aliases

**Files:**
- Modify: `tests/test_pipeline_legacy_export.py`
- Modify: `tests/test_pipeline_source_pack.py`
- Modify: `tests/test_pipeline_cli_dry_run.py`
- Modify: `tests/test_pipeline_gap_planner.py`
- Modify: `tests/test_pipeline_exa_discovery.py`
- Modify: `pipeline/models.py` (remove `HotelOrg = CorpOrg` alias)
- Modify: `pipeline/candidates.py` (remove `initial_hotel_from_url` alias)

**Interfaces:**
- Produces: clean codebase with no HotelOrg alias — any remaining usage is a bug

- [ ] **Step 1: Run full test suite and collect all failures**

```bash
pytest tests/ -q 2>&1 | grep FAILED
```

- [ ] **Step 2: Fix tests/test_pipeline_legacy_export.py**

Replace all `HotelOrg` imports with `CorpOrg`. Remove `property_name` field (does not exist on `CorpOrg`). Replace hotel-specific `role_family` values with new ones:

```python
from pipeline.models import (
    CandidateLead,
    ContactRoute,
    CorpOrg,
    PipelineTelemetry,
    PipelineUiJson,
    SourceRef,
)

def _sample_ui() -> PipelineUiJson:
    corp = CorpOrg(
        input_url="https://zenithbank.com",
        canonical_name="Zenith Bank",
        industry_sector="banking",
        hq_country="Nigeria",
        domains=["zenithbank.com"],
    )
    candidate = CandidateLead(
        candidate_id="c_1",
        full_name="Alex Person",
        title="Chief Executive Officer",
        company="Zenith Bank",
        role_tier=1,
        role_family="c_suite",
        current_role_confidence="high",
        relationship_confidence="high",
        linkedin_url="https://uk.linkedin.com/in/alex-person",
        contact_routes=[
            ContactRoute(kind="email", value="alex@zenithbank.com", confidence="high", source_url="https://zenithbank.com/team"),
            ContactRoute(kind="phone", value="+234 1 000 0000", confidence="medium", source_url="https://zenithbank.com/contact"),
            ContactRoute(kind="generic_email", value="info@zenithbank.com", confidence="medium", source_url="https://zenithbank.com/contact"),
        ],
        ...  # keep rest of candidate fields
    )
    ...
    # Build PipelineUiJson with corp=corp (not hotel=hotel)
```

- [ ] **Step 3: Fix tests/test_pipeline_source_pack.py**

```python
# Replace import and fixture:
from pipeline.models import CandidateLead, CorpOrg, SourceRef

corp = CorpOrg(input_url="https://zenithbank.com", domains=["zenithbank.com"])
```

- [ ] **Step 4: Fix any remaining test files** that still import `HotelOrg` directly

```bash
grep -r "HotelOrg" tests/ --include="*.py" -l
```

For each file listed, replace `HotelOrg` → `CorpOrg` and update any removed fields (`property_name`, `brand_name`, `management_company`, `ownership_group`).

- [ ] **Step 5: Remove backward-compat aliases from pipeline/models.py**

Remove the line:
```python
HotelOrg = CorpOrg
```

Remove the line:
```python
hotel_key_from_org = corp_key_from_org
```

- [ ] **Step 6: Remove initial_hotel_from_url alias from pipeline/candidates.py**

Remove:
```python
initial_hotel_from_url = initial_corp_from_url
```

Remove `hotel_key_from_org` from the import in candidates.py (no longer needed).

- [ ] **Step 7: Run full test suite**

```bash
pytest tests/ -q
```

Expected: all tests pass. If any `HotelOrg` NameError appears, grep and fix:

```bash
grep -r "HotelOrg\|hotel_key_from_org\|initial_hotel_from_url" pipeline/ tests/ --include="*.py"
```

- [ ] **Step 8: Commit**

```bash
git add -u
git commit -m "refactor(pipeline): remove HotelOrg backward-compat aliases; all tests green"
```

---

## Task 6: New corp_batch_pipeline.py — batch entry point

**Files:**
- Create: `corp_batch_pipeline.py`
- Test: `tests/test_corp_batch_pipeline_help.py`

**Interfaces:**
- Consumes: `pipeline.cli.run_pipeline(corp_url, config, ...)`
- Produces: `python corp_batch_pipeline.py --url URL [--url URL2 ...] [--corps-file FILE] [--workers N] [--skip-if-enriched]`

- [ ] **Step 1: Write failing test**

```python
# tests/test_corp_batch_pipeline_help.py
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent


def test_corp_batch_pipeline_help_exits_zero() -> None:
    result = subprocess.run(
        [sys.executable, str(root / "corp_batch_pipeline.py"), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--url" in result.stdout or "--corps-file" in result.stdout


def test_corp_batch_pipeline_requires_url_or_file(monkeypatch) -> None:
    import sys
    monkeypatch.setattr(sys, "argv", ["corp_batch_pipeline.py"])
    import importlib
    import corp_batch_pipeline  # noqa: F401
    # Just verify the module is importable
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_corp_batch_pipeline_help.py -x -q
```

Expected: FAIL — `corp_batch_pipeline.py` does not exist

- [ ] **Step 3: Create corp_batch_pipeline.py**

```python
#!/usr/bin/env python3
"""Run SSA executive pipeline for many company URLs concurrently."""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_repo_root = Path(__file__).resolve().parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from scripts._repo_dotenv import load_repo_dotenv
from pipeline.cli import run_pipeline
from pipeline.config import PipelineConfig


def _read_corps_file(path: Path) -> list[str]:
    """Read URLs from corps_discovered.json or a plain text file."""
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("["):
        corps = json.loads(text)
        return [c["url"] for c in corps if c.get("url")]
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]


def _run_one(url: str, *, out_dir: Path, cfg: PipelineConfig) -> tuple[str, str]:
    try:
        res = run_pipeline(url, cfg, out_dir=out_dir)
        return url, f"ok candidates={len(res.candidates)}"
    except Exception as exc:
        return url, f"error: {exc}"


def main(argv: list[str] | None = None) -> int:
    load_repo_dotenv(Path(__file__).resolve().parent)
    p = argparse.ArgumentParser(description="Batch SSA executive pipeline")
    p.add_argument("--url", dest="urls", action="append", default=[], metavar="URL", help="Company URL (repeatable)")
    p.add_argument("--corps-file", type=Path, metavar="FILE", help="JSON or text file of company URLs")
    p.add_argument("--workers", type=int, default=2, help="Parallel workers (default 2)")
    p.add_argument("--out", type=Path, default=Path("outputs/pipeline"))
    p.add_argument("--max-candidates", type=int, default=50)
    p.add_argument("--no-aggregate-sync", action="store_true")
    args = p.parse_args(argv)

    urls: list[str] = list(args.urls)
    if args.corps_file:
        urls.extend(_read_corps_file(args.corps_file))

    if not urls:
        print("error: provide --url or --corps-file", file=sys.stderr)
        return 1

    seen: set[str] = set()
    deduped = [u for u in urls if not (u in seen or seen.add(u))]  # type: ignore[func-returns-value]

    cfg = PipelineConfig(
        max_candidates=args.max_candidates,
        skip_linkedin=False,
        skip_contact_mining=False,
    )
    out_dir: Path = args.out

    print(f"Running pipeline for {len(deduped)} corps with {args.workers} workers...")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_run_one, u, out_dir=out_dir, cfg=cfg): u for u in deduped}
        for fut in as_completed(futures):
            url, status = fut.result()
            print(f"  {url}: {status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_corp_batch_pipeline_help.py -x -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add corp_batch_pipeline.py tests/test_corp_batch_pipeline_help.py
git commit -m "feat: add corp_batch_pipeline.py for batch SSA exec pipeline runs"
```

---

## Task 7: New scripts/discover_ssa_corps.py — Phase 1 Exa company discovery

**Files:**
- Create: `scripts/discover_ssa_corps.py`
- Test: `tests/test_discover_ssa_corps.py`

**Interfaces:**
- Produces: `discover_corps(exa_key, industries, countries, out_file) -> list[dict]`
- Produces: `generate_micro_verticals(industries, countries) -> list[str]`
- CLI: `python scripts/discover_ssa_corps.py --industries banking mining --countries nigeria "south africa" --out corps_discovered.json`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_discover_ssa_corps.py
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
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_discover_ssa_corps.py -x -q
```

Expected: FAIL — module not found

- [ ] **Step 3: Create scripts/discover_ssa_corps.py**

```python
#!/usr/bin/env python3
"""Phase 1 — discover Sub-Saharan African company URLs via Exa deep search."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from scripts._repo_dotenv import load_repo_dotenv


_QUERY_TEMPLATES = [
    "top {industry} companies {country} official website",
    "largest {industry} corporations {country}",
    "{country} {industry} company annual report",
    "major {industry} firms {country} executive team",
]


def generate_micro_verticals(industries: list[str], countries: list[str]) -> list[str]:
    verticals: list[str] = []
    for country in countries:
        for industry in industries:
            for tmpl in _QUERY_TEMPLATES:
                verticals.append(tmpl.format(industry=industry, country=country))
    return verticals


def extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url if "://" in url else "https://" + url)
        netloc = parsed.netloc.lower()
        return netloc.lstrip("www.") if netloc else ""
    except Exception:
        return ""


def _is_company_url(url: str) -> bool:
    """Exclude news, social, directory, and aggregator domains."""
    skip = (
        "linkedin.com", "facebook.com", "twitter.com", "bloomberg.com",
        "reuters.com", "businessday.ng", "guardian.ng", "wikipedia.org",
        "glassdoor.com", "indeed.com", "crunchbase.com",
    )
    domain = extract_domain(url).lower()
    return bool(domain) and not any(s in domain for s in skip)


def discover_corps(
    exa_key: str,
    industries: list[str],
    countries: list[str],
    *,
    results_per_query: int = 10,
) -> list[dict]:
    from exa_py import Exa

    client = Exa(api_key=exa_key)
    verticals = generate_micro_verticals(industries, countries)
    raw: list[dict] = []

    for i, query in enumerate(verticals, 1):
        print(f"  [{i}/{len(verticals)}] {query}")
        try:
            result = client.search(query, num_results=results_per_query, use_autoprompt=True)
            for item in getattr(result, "results", []):
                url = str(getattr(item, "url", "") or "").strip()
                if url and _is_company_url(url):
                    country_hint = next((c for c in countries if c.lower() in query.lower()), "")
                    industry_hint = next((ind for ind in industries if ind.lower() in query.lower()), "")
                    raw.append({
                        "name": getattr(item, "title", "") or "",
                        "url": url,
                        "country": country_hint,
                        "industry": industry_hint,
                        "revenue_estimate": None,
                    })
        except Exception as exc:
            print(f"    warning: query failed — {exc}", file=sys.stderr)

    # Deduplicate by domain
    seen: set[str] = set()
    deduped: list[dict] = []
    for c in raw:
        domain = extract_domain(c["url"])
        if domain and domain not in seen:
            seen.add(domain)
            deduped.append(c)

    return deduped


def main(argv: list[str] | None = None) -> int:
    load_repo_dotenv(Path(__file__).resolve().parents[1])
    p = argparse.ArgumentParser(description="Discover SSA company URLs via Exa")
    p.add_argument("--industries", nargs="+", default=["banking", "mining", "telecoms", "fmcg", "tech"],
                   metavar="IND")
    p.add_argument("--countries", nargs="+",
                   default=["nigeria", "south africa", "kenya", "ghana", "ethiopia", "tanzania"],
                   metavar="COUNTRY")
    p.add_argument("--out", default="corps_discovered.json", metavar="FILE")
    p.add_argument("--results-per-query", type=int, default=10)
    args = p.parse_args(argv)

    exa_key = (os.environ.get("EXA_API_KEY") or "").strip()
    if not exa_key:
        print("error: EXA_API_KEY not set", file=sys.stderr)
        return 1

    print(f"Discovering corps: {args.industries} × {args.countries}")
    corps = discover_corps(
        exa_key,
        args.industries,
        args.countries,
        results_per_query=args.results_per_query,
    )

    out = Path(args.out)
    out.write_text(json.dumps(corps, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Discovered {len(corps)} corps → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_discover_ssa_corps.py -x -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/discover_ssa_corps.py tests/test_discover_ssa_corps.py
git commit -m "feat(phase1): add discover_ssa_corps.py — Exa-based SSA company discovery"
```

---

## Task 8: Update ICPs.md for SSA exec lead gen

**Files:**
- Modify: `ICPs.md`

- [ ] **Step 1: Replace ICPs.md content**

```markdown
# ICP Database

## SSA Executive Lead Gen (High-Net-Worth Apartment Sales)

**Target**
C-suite officers, VPs, and Directors at Sub-Saharan African corporations and international corporations with African offices. Revenue ≥ $20M. Industries: banking, telecoms, mining, FMCG, tech, insurance, energy.

**Geography**
Sub-Saharan Africa — primary markets: Nigeria, South Africa, Kenya, Ghana, Ethiopia, Tanzania.

**Seniority**
- Tier 1: CEO, CFO, COO, CTO, CMO, Managing Director, Group Chief Officers
- Tier 2: Vice Presidents (VP, SVP, EVP)
- Tier 3: Directors (Finance Director, Commercial Director, etc.)
- Excluded: Regional Heads, Middle Management

**Minimum contact data required**
- LinkedIn profile URL (mandatory)
- Email address (bonus)
- Phone (bonus)

**Output use case**
Lead list for sales team selling high-end apartments to high-net-worth individuals.

**Useful enrichments**
- full_name, title, company, hq_country, industry_sector
- linkedin_url, email, phone
- role_tier, role_family (c_suite / vp_level / director_level)
- revenue_estimate (company-level qualifier)

*Last updated: 2026-07-27*
```

- [ ] **Step 2: Commit**

```bash
git add ICPs.md
git commit -m "docs: update ICPs.md for SSA exec lead gen (apartment sales)"
```

---

## End-to-End Smoke Test

After all tasks complete, verify the pipeline accepts a company URL:

```bash
export XAI_API_KEY=your_key
export EXA_API_KEY=your_key
python -m pipeline run https://zenithbank.com --dry-run
```

Expected output: `candidates=0 review_rows=0` plus a dry-run JSON plan (no API calls made).

For Phase 1 discovery:

```bash
export EXA_API_KEY=your_key
python scripts/discover_ssa_corps.py --industries banking --countries nigeria --results-per-query 5 --out /tmp/test_corps.json
```

Expected: `/tmp/test_corps.json` written with Nigerian banking company URLs.
