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


def _run_one(url: str, *, out_dir: Path, cfg: PipelineConfig, no_aggregate_sync: bool = False) -> tuple[str, str]:
    try:
        res = run_pipeline(url, cfg, out_dir=out_dir, aggregate_sync=not no_aggregate_sync)
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
        # Tip: for large batch runs, prefer --no-aggregate-sync + one rebuild pass at the end
        futures = {pool.submit(_run_one, u, out_dir=out_dir, cfg=cfg, no_aggregate_sync=args.no_aggregate_sync): u for u in deduped}
        for fut in as_completed(futures):
            url, status = fut.result()
            print(f"  {url}: {status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
