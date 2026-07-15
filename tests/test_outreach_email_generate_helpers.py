from __future__ import annotations

import importlib.util
from pathlib import Path

from outreach.schema import TRIAGE_APPROVED


def _load_generate_script():
    root = Path(__file__).resolve().parent.parent
    path = root / "scripts" / "outreach_email_generate_xai.py"
    spec = importlib.util.spec_from_file_location("outreach_email_generate_xai", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_prefer_oid_in_intimate_index_picks_sibling_in_index() -> None:
    mod = _load_generate_script()
    by_id = {
        "oh_stale": {
            "primary_email": "x@example.com",
            "triage": {"status": TRIAGE_APPROVED},
            "generation": None,
        },
        "oh_ok": {
            "primary_email": "x@example.com",
            "triage": {"status": TRIAGE_APPROVED},
            "generation": None,
        },
    }
    assert mod._prefer_oid_in_intimate_index(by_id, "oh_stale", valid_ids={"oh_ok"}) == "oh_ok"


def test_contact_payload_includes_same_email_state() -> None:
    mod = _load_generate_script()
    by_id = {
        "a": {
            "primary_email": "x@example.com",
            "hotel_canonical_url": "https://one.example",
            "target_url": "https://one.example/",
            "triage": {"status": TRIAGE_APPROVED},
        },
        "b": {
            "primary_email": "x@example.com",
            "hotel_canonical_url": "https://two.example",
            "target_url": "https://two.example/",
            "triage": {"status": TRIAGE_APPROVED},
        },
    }
    intimate = {"email": "x@example.com", "full_name": "X"}
    p = mod._contact_payload("a", intimate_row=intimate, state_row=by_id["a"], by_id=by_id)
    assert p["outreach_same_email_state"] == [
        {
            "outreach_id": "a",
            "hotel_canonical_url": "https://one.example",
            "target_url": "https://one.example/",
            "triage_status": TRIAGE_APPROVED,
        },
        {
            "outreach_id": "b",
            "hotel_canonical_url": "https://two.example",
            "target_url": "https://two.example/",
            "triage_status": TRIAGE_APPROVED,
        },
    ]
