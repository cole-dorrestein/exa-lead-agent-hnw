from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from outreach.indexes import rebuild_indexes
from outreach.schema import TRIAGE_APPROVED, TRIAGE_DECLINED, TRIAGE_PENDING, empty_state


def _write_state(path: Path, by_id: dict[str, dict]) -> None:
    doc = empty_state()
    doc["by_id"] = by_id
    doc["indexes"] = rebuild_indexes(by_id)
    path.write_text(json.dumps(doc), encoding="utf-8")


def _run_triage(root: Path, state_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "outreach_email_triage.py"),
            "--state-path",
            str(state_path),
            "--approve-all-pending",
        ],
        cwd=str(root),
        capture_output=True,
        text=True,
    )


def _run_triage_interactive(root: Path, state_path: Path, *, stdin: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "outreach_email_triage.py"),
            "--state-path",
            str(state_path),
            "--interactive",
        ],
        cwd=str(root),
        input=stdin,
        capture_output=True,
        text=True,
    )


def test_triage_skips_pending_when_email_already_generated(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    state_path = tmp_path / "state.json"
    by_id = {
        "old": {
            "outreach_id": "old",
            "primary_email": "same@example.com",
            "target_url": "https://one.example/",
            "hotel_canonical_url": "https://one.example",
            "intimate_snapshot": {},
            "intimate_row_hash": "h1",
            "intimate_doc_generated_at_utc": None,
            "triage": {"status": TRIAGE_APPROVED, "decided_at_utc": None, "note": None},
            "generation": {"body": "already generated"},
            "send": None,
        },
        "new": {
            "outreach_id": "new",
            "primary_email": "same@example.com",
            "target_url": "https://two.example/",
            "hotel_canonical_url": "https://two.example",
            "intimate_snapshot": {},
            "intimate_row_hash": "h2",
            "intimate_doc_generated_at_utc": None,
            "triage": {"status": TRIAGE_PENDING, "decided_at_utc": None, "note": None},
            "generation": None,
            "send": None,
        },
    }
    _write_state(state_path, by_id)
    r = _run_triage(root, state_path)
    assert r.returncode == 0, r.stderr
    out = json.loads(state_path.read_text(encoding="utf-8"))
    assert out["by_id"]["new"]["triage"]["status"] == TRIAGE_PENDING


def test_triage_skips_pending_when_email_declined(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    state_path = tmp_path / "state.json"
    by_id = {
        "old": {
            "outreach_id": "old",
            "primary_email": "same@example.com",
            "target_url": "https://one.example/",
            "hotel_canonical_url": "https://one.example",
            "intimate_snapshot": {},
            "intimate_row_hash": "h1",
            "intimate_doc_generated_at_utc": None,
            "triage": {"status": TRIAGE_DECLINED, "decided_at_utc": None, "note": None},
            "generation": None,
            "send": None,
        },
        "new": {
            "outreach_id": "new",
            "primary_email": "same@example.com",
            "target_url": "https://two.example/",
            "hotel_canonical_url": "https://two.example",
            "intimate_snapshot": {},
            "intimate_row_hash": "h2",
            "intimate_doc_generated_at_utc": None,
            "triage": {"status": TRIAGE_PENDING, "decided_at_utc": None, "note": None},
            "generation": None,
            "send": None,
        },
    }
    _write_state(state_path, by_id)
    r = _run_triage(root, state_path)
    assert r.returncode == 0, r.stderr
    out = json.loads(state_path.read_text(encoding="utf-8"))
    assert out["by_id"]["new"]["triage"]["status"] == TRIAGE_PENDING


def test_triage_skips_pending_when_email_is_resume_approved(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    state_path = tmp_path / "state.json"
    by_id = {
        "old": {
            "outreach_id": "old",
            "primary_email": "same@example.com",
            "target_url": "https://one.example/",
            "hotel_canonical_url": "https://one.example",
            "intimate_snapshot": {},
            "intimate_row_hash": "h1",
            "intimate_doc_generated_at_utc": None,
            "triage": {"status": TRIAGE_APPROVED, "decided_at_utc": None, "note": None},
            "generation": None,
            "send": None,
        },
        "new": {
            "outreach_id": "new",
            "primary_email": "same@example.com",
            "target_url": "https://two.example/",
            "hotel_canonical_url": "https://two.example",
            "intimate_snapshot": {},
            "intimate_row_hash": "h2",
            "intimate_doc_generated_at_utc": None,
            "triage": {"status": TRIAGE_PENDING, "decided_at_utc": None, "note": None},
            "generation": None,
            "send": None,
        },
    }
    _write_state(state_path, by_id)
    r = _run_triage(root, state_path)
    assert r.returncode == 0, r.stderr
    out = json.loads(state_path.read_text(encoding="utf-8"))
    assert out["by_id"]["new"]["triage"]["status"] == TRIAGE_PENDING


def test_triage_approve_all_pending_groups_same_email(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    state_path = tmp_path / "state.json"
    by_id = {
        "a": {
            "outreach_id": "a",
            "primary_email": "same@example.com",
            "target_url": "https://one.example/",
            "hotel_canonical_url": "https://one.example",
            "intimate_snapshot": {},
            "intimate_row_hash": "h1",
            "intimate_doc_generated_at_utc": None,
            "triage": {"status": TRIAGE_PENDING, "decided_at_utc": None, "note": None},
            "generation": None,
            "send": None,
        },
        "b": {
            "outreach_id": "b",
            "primary_email": "same@example.com",
            "target_url": "https://two.example/",
            "hotel_canonical_url": "https://two.example",
            "intimate_snapshot": {},
            "intimate_row_hash": "h2",
            "intimate_doc_generated_at_utc": None,
            "triage": {"status": TRIAGE_PENDING, "decided_at_utc": None, "note": None},
            "generation": None,
            "send": None,
        },
    }
    _write_state(state_path, by_id)
    r = _run_triage(root, state_path)
    assert r.returncode == 0, r.stderr
    assert "1 email groups" in (r.stdout or "")
    out = json.loads(state_path.read_text(encoding="utf-8"))
    assert out["by_id"]["a"]["triage"]["status"] == TRIAGE_APPROVED
    assert out["by_id"]["b"]["triage"]["status"] == TRIAGE_APPROVED
    assert out["by_id"]["a"]["triage"]["note"] == "email_group_approved"


def test_triage_interactive_y_approves_all_listings_same_email(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    state_path = tmp_path / "state.json"
    by_id = {
        "a": {
            "outreach_id": "a",
            "primary_email": "same@example.com",
            "target_url": "https://one.example/",
            "hotel_canonical_url": "https://one.example",
            "intimate_snapshot": {"full_name": "Rachel Louis"},
            "intimate_row_hash": "h1",
            "intimate_doc_generated_at_utc": None,
            "triage": {"status": TRIAGE_PENDING, "decided_at_utc": None, "note": None},
            "generation": None,
            "send": None,
        },
        "b": {
            "outreach_id": "b",
            "primary_email": "same@example.com",
            "target_url": "https://two.example/",
            "hotel_canonical_url": "https://two.example",
            "intimate_snapshot": {"full_name": "Rachel Louis"},
            "intimate_row_hash": "h2",
            "intimate_doc_generated_at_utc": None,
            "triage": {"status": TRIAGE_PENDING, "decided_at_utc": None, "note": None},
            "generation": None,
            "send": None,
        },
    }
    _write_state(state_path, by_id)
    r = _run_triage_interactive(root, state_path, stdin="y\n")
    assert r.returncode == 0, r.stderr
    out = json.loads(state_path.read_text(encoding="utf-8"))
    assert out["by_id"]["a"]["triage"]["status"] == TRIAGE_APPROVED
    assert out["by_id"]["b"]["triage"]["status"] == TRIAGE_APPROVED
    assert "Email group" in (r.stdout or "")
