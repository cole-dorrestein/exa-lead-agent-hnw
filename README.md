# exa-lead-agent-hnw

AI-powered lead generation pipeline for high-net-worth executive prospecting across Sub-Saharan Africa. Targets C-suite, VP-level, and Director-level officers at major SSA corporations for luxury real estate outreach.

Built on Grok 4.20 (xAI) for executive discovery and Exa semantic search for verification and enrichment. Delivers ICP-scored, deduplicated lead lists with LinkedIn URLs, role tiers, confidence scores, and contact routes — ready for direct outreach.

---

## SSA Executive Leads (xAI)

**Current (v4):** Grok-led pipeline + capped Exa — debug/UI artifacts under `outputs/pipeline/`, plus a legacy-compatible `jsons/*.enriched.json` per run and a locked refresh of aggregate files under `fullJSONs/`.

```bash
pip install -r requirements.txt
export XAI_API_KEY=...
export EXA_API_KEY=...
python -m pipeline run https://example-corp.com/
```

To skip aggregate writes for experimentation:

```bash
python -m pipeline run https://example-corp.com/ --no-aggregate-sync
```

**Legacy scripts (archived under [`legacy/`](legacy/README.md)):** root shims keep old commands working; implementation files live in `legacy/`.

1. **Research** — `hotel_decision_maker_research.py` (shim → `legacy/hotel_decision_maker_research.py`) discovers executives at a target corporation, writes JSON under **`jsons/`** and appends CSV under **`csv/`** (needs `XAI_API_KEY`).
2. **Contact enrichment** — `hotel_contact_enrichment.py` (shim → `legacy/hotel_contact_enrichment.py`) re-reads that JSON, runs `grok-4.20-reasoning` with web + X search per candidate, merges email/phone/X/LinkedIn back in. Skips rows that already score high on direct channels.

```bash
pip install -r requirements.txt
export XAI_API_KEY=...
python hotel_decision_maker_research.py --url https://example-corp.com
python hotel_contact_enrichment.py --in-json jsons/corp_leads__....json --out-json jsons/corp_leads__....enriched.json
python hotel_contact_enrichment.py --in-json in.json --out-json out.json --dry-run
```

### Batch processing (multiple corporations)

```bash
python corp_batch_pipeline.py --url https://a.com/ --url https://b.com/ --workers 4 --skip-if-enriched
# or: --urls-file urls.txt
```

### SSA corporation discovery

Identify target corporations across Sub-Saharan Africa before running the lead pipeline:

```bash
python scripts/discover_ssa_corps.py
```

### fullJSONs aggregates (multi-corporation, locked writes)

Python code lives in the **`lead_aggregates/`** package. Merged JSON outputs live under **`fullJSONs/`**.

| File | Purpose |
|------|---------|
| `fullJSONs/all_enriched_leads.json` | Warehouse: every contact from every `jsons/*.enriched.json` with `occurrence_id` = `source_file::dedupe_key` |
| `fullJSONs/intimate_phone_contacts.json` | Rows with structured `phone` / `phone2` (globally deduped) |
| `fullJSONs/intimate_email_contacts.json` | Rows with named non-generic `email` / `email2` |
| `fullJSONs/intimate_unified_contacts.json` | **Canonical outreach slice:** phone and/or named email, one global row per person (`dedupe_key` uses canonical `www.linkedin.com` profile URLs when present) |
| `fullJSONs/url_registry.json` | Canonical corporation URL → status, paths, errors |
| `fullJSONs/.merge.lock` | `filelock` coordination for all updates above |

**Rebuild everything from current `jsons/*.enriched.json`:**

```bash
python scripts/rebuild_fulljsons.py
```

**Backfill latest v4 `outputs/pipeline` runs into `jsons/` and rebuild `fullJSONs/`** (keeps only the latest run per canonical corporation URL, so reruns do not duplicate contacts in aggregates):

```bash
python scripts/import_pipeline_outputs.py --outputs-dir outputs/pipeline --jsons-dir jsons --fulljsons-dir fullJSONs
```

**Rebuild only intimate slices:**

```bash
python scripts/build_intimate_phone_contacts.py
python scripts/build_intimate_email_contacts.py
```

Each completed corporation run triggers a locked refresh of all aggregate `fullJSONs/` files (full rebuild from `jsons/` — simple and idempotent). If a run crashes mid-write, run `python scripts/rebuild_fulljsons.py` to heal aggregates from disk.

---

## Prerequisites

Requires an [Exa API key](https://dashboard.exa.ai/api-keys) and an [xAI API key](https://console.x.ai/). Add the Exa MCP server before running:

```bash
claude mcp add --transport http exa "https://mcp.exa.ai/mcp?exaApiKey=YOUR_EXA_API_KEY&tools=web_search_advanced_exa"
```

---

## What It Can Do

- **ICP Research** — Researches a target corporation against the SSA executive ICP before generating leads
- **Executive Discovery** — Grok 4.20 synthesises corporate filings, press releases, and professional profiles into a structured candidate list
- **Verification** — Exa semantic search cross-references candidates against LinkedIn and corporate websites; no contact data emitted without a cited source URL
- **Role Tiering** — Every lead scored by ICP fit and assigned a role tier (Tier 1: C-suite, Tier 2: VP-level, Tier 3: Director-level)
- **Parallel Batch Processing** — `corp_batch_pipeline.py` runs the pipeline across multiple corporations simultaneously
- **Deduplication & CSV** — Normalises company names, dedupes by LinkedIn URL, sorts by ICP score, outputs clean CSV
- **CRM Interface** — FastAPI + HTMX + Supabase app for browsing, filtering, and exporting leads

---

## Example Usage

```
"Find the top 50 executives at Safaricom we should target for luxury apartment outreach"
"Generate leads across Nigerian banking — CEO, CFO, COO at banks with revenue above $500M"
"Build a prospect list of C-suite officers at SSA mining and energy corporations"
```

---

## ICP

Target profile is defined in [`ICPs.md`](ICPs.md):

- **Geography:** Sub-Saharan Africa — primary markets: Nigeria, South Africa, Kenya, Ghana, Ethiopia, Tanzania
- **Seniority:** Tier 1 (C-suite), Tier 2 (VP-level), Tier 3 (Directors) — regional heads and middle management excluded
- **Industries:** Banking, telecoms, mining, FMCG, tech, insurance, energy
- **Company size:** Revenue ≥ $20M
- **Minimum output:** LinkedIn URL (mandatory), email and phone (bonus)

Operational constraints are defined in [`RULES.md`](RULES.md).

---

## Structure

```
exa-lead-agent-hnw/
├── agent.yaml
├── ICPs.md
├── RULES.md
├── SOUL.md
├── corp_batch_pipeline.py
├── pipeline_metrics.py
├── lead_aggregates/
├── phone_crm/
├── scripts/
│   ├── discover_ssa_corps.py
│   ├── linkedin_exa_enrich.py
│   ├── outreach_email_flow.py
│   ├── phone_crm_sync.py
│   ├── rebuild_fulljsons.py
│   └── ...
├── legacy/
│   ├── hotel_decision_maker_research.py
│   ├── hotel_contact_enrichment.py
│   └── README.md
└── knowledge/
    ├── index.yaml
    └── mcp-setup.md
```

---

## CRM (FastAPI + HTMX + Supabase)

Browse, filter by role tier / contact quality / geography, and export leads directly to outreach workflows.

### Environment

```bash
export DATABASE_URL="postgresql://postgres:password@db.project.supabase.co:5432/postgres"
export CRM_USERNAME="admin"
export CRM_PASSWORD="change-me"
export CRM_JSON_PATH="fullJSONs/all_enriched_leads.json"
```

### Sync and run

```bash
python -m scripts.phone_crm_sync --json fullJSONs/all_enriched_leads.json
uvicorn phone_crm.app:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/` and authenticate.

### Render deploy

Use the included `render.yaml` blueprint, or:

- Build: `pip install -r requirements.txt`
- Start: `uvicorn phone_crm.app:app --host 0.0.0.0 --port $PORT`
- Env vars: `DATABASE_URL`, `CRM_USERNAME`, `CRM_PASSWORD`, `CRM_JSON_PATH`

Health check: `GET /health` → `{"status":"ok"}`
