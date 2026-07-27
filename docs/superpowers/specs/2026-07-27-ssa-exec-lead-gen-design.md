# SSA Executive Lead Gen — Design Spec
_Date: 2026-07-27_

## Goal

Repurpose the hotel lead gen pipeline to find high-ranking executives (C-suite, VPs, Directors) at Sub-Saharan African corporations and international corporations with African offices. Output is a lead list for a sales team selling high-end apartments.

## Target

- **Geography:** Sub-Saharan Africa
- **Companies:** $20M+ revenue — banking, mining, telecoms, FMCG, tech, and other high-earning industries
- **People:** C-suite (CEO, CFO, COO, MD), VPs, Directors — no regional heads
- **Minimum output per lead:** LinkedIn profile URL; email + phone as bonus

---

## Architecture: Two-Phase Pipeline

```
Phase 1: Corp Discovery
  scripts/discover_ssa_corps.py
  → Exa deep search across SSA micro-verticals
  → corps_discovered.json  [name, URL, country, industry, revenue_estimate]

Phase 2: Exec Extraction
  corp_batch_pipeline.py
  → for each URL in corps_discovered.json:
      Grok discovers C-suite / VPs / Directors
      Exa verifies + enriches contacts
      LinkedIn enrichment pass
  → JSON + CSV per run → aggregated into fullJSONs/
```

**Unchanged:** contact_enrichment/, linkedin_enrich/, lead_aggregates/, phone_crm/, outreach/

---

## Phase 1: Corp Discovery

### Entry point

```bash
python scripts/discover_ssa_corps.py \
  --industries banking mining telecoms fmcg tech \
  --countries nigeria "south africa" kenya ghana ethiopia tanzania \
  --min-revenue 20M \
  --out corps_discovered.json
```

### Mechanism

Uses the `exa-lead-gen` batch subagent pattern. Generates micro-verticals from the `--industries` + `--countries` args, e.g.:

- `"Nigerian commercial banks revenue over 50 million USD"`
- `"South African mining corporations JSE listed"`
- `"Kenyan telecommunications companies"`
- `"Sub-Saharan African FMCG multinationals"`
- `"East African technology companies over 20 million revenue"`

Each Exa deep call returns ~35–48 companies. Batch subagents write JSON to `/tmp/`, Python compiler deduplicates + writes `corps_discovered.json`.

### Output schema per company

```json
{
  "name": "Zenith Bank",
  "url": "https://zenithbank.com",
  "country": "Nigeria",
  "industry": "banking",
  "revenue_estimate": ">$1B"
}
```

---

## Phase 2: Exec Extraction

### Model changes (`pipeline/models.py`)

`HotelOrg` → `CorpOrg`:

```python
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
```

`RoleFamily` updated:

```python
RoleFamily = Literal["c_suite", "vp_level", "director_level", "board", "owner_exec", "other"]
```

`GrokDiscoveryResult.hotel: HotelOrg` → `GrokDiscoveryResult.corp: CorpOrg` throughout.

### Grok discovery prompt (`pipeline/grok_discovery.py`)

New prompt replaces hotel-specific logic:

```
Company URL (only input): {url}

Tasks (use web_search and x_search; prefer official sites, press, LinkedIn, regulatory filings):

1) Resolve the company: canonical name, industry sector, HQ country/city, revenue estimate, employee count estimate.
2) Emit aliases (trading name / registered name / domain / historical) with confidence high|medium|low.
3) Discover all C-suite officers, VPs, and Directors at this company (12–30 people).
   Include: CEO, CFO, COO, MD, CTO, CMO, VP-level, Director-level.
   Exclude: regional heads, middle management.
4) For each person: evidence (url required), linkedin_url when clearly the same person,
   contact_routes only when explicitly present in source text (never invent email/phone),
   confidence_hint high|medium|low.

Rules: never fabricate emails or phone numbers.

Return JSON matching the GrokDiscoveryResult schema (fields: corp, aliases, drafts).
```

### Batch entry point

`corp_batch_pipeline.py` replaces `hotel_batch_pipeline.py`:

```bash
python corp_batch_pipeline.py \
  --corps-file corps_discovered.json \
  --workers 4 \
  --skip-if-enriched
```

Also supports direct URL args:
```bash
python corp_batch_pipeline.py --url https://zenithbank.com --url https://safaricom.co.ke
```

### Files changed

| File | Change |
|------|--------|
| `pipeline/models.py` | `HotelOrg` → `CorpOrg`, update `RoleFamily`, update `GrokDiscoveryResult`, `PipelineRunResult`, `PipelineUiJson` |
| `pipeline/grok_discovery.py` | New discovery prompt, rename `HotelOrg` refs |
| `pipeline/candidates.py` | `hotel_key_from_org` → `corp_key_from_org` |
| `pipeline/review_board.py` | `ReviewRow.hotel_name` → `corp_name` |
| `pipeline/io.py` | Update `HotelOrg` refs |
| `pipeline/cli.py` | Update help text |
| `pipeline/source_pack.py` | Update `HotelOrg` refs |
| `pipeline/legacy_export.py` | Update `HotelOrg` refs |
| `hotel_batch_pipeline.py` | New `corp_batch_pipeline.py` alongside (keep shim for legacy) |
| `ICPs.md` | New ICP for SSA exec lead gen |
| `scripts/discover_ssa_corps.py` | New Phase 1 script |
| Tests | Update fixtures + rename references |

---

## Output

### Final CSV per exec

| full_name | title | role_tier | company | industry | hq_country | linkedin_url | email | phone |

### Aggregates (unchanged paths)

- `fullJSONs/all_enriched_leads.json` — all contacts
- `fullJSONs/intimate_unified_contacts.json` — contacts with LinkedIn and/or named email

### Phone CRM

Unchanged. Syncs from `fullJSONs/all_enriched_leads.json` as before.

---

## What is NOT changing

- `contact_enrichment/` — unchanged
- `linkedin_enrich/` — unchanged
- `lead_aggregates/` — unchanged
- `phone_crm/` — unchanged (hotel list UI is cosmetic, not blocking)
- `outreach/` — unchanged
- `exa_verify.py`, `exa_discovery.py`, `gap_planner.py` — logic unchanged, only `HotelOrg` refs updated

---

## API Keys Required

| Key | Used by |
|-----|---------|
| `EXA_API_KEY` | Phase 1 corp discovery + Phase 2 Exa verification |
| `XAI_API_KEY` | Phase 2 Grok discovery + contact enrichment |
