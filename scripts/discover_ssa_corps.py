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
        if "://" not in url:
            # Only treat as a URL if it contains a dot (looks like a hostname)
            if "." not in url:
                return ""
            url = "https://" + url
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
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
