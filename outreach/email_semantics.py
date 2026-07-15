from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from outreach.schema import TRIAGE_APPROVED, TRIAGE_DECLINED

TRIAGE_SKIPPED = "skipped"
TERMINAL_TRIAGE_STATUSES = frozenset({TRIAGE_DECLINED, TRIAGE_SKIPPED})


@dataclass
class EmailStatus:
    has_generated: bool = False
    has_terminal: bool = False
    has_approved: bool = False

    @property
    def generation_blocked(self) -> bool:
        return self.has_generated or self.has_terminal

    @property
    def triage_blocked(self) -> bool:
        return self.generation_blocked or self.has_approved


def normalize_email(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    out = value.strip().lower()
    return out or None


def row_generated(row: dict[str, Any]) -> bool:
    gen = row.get("generation")
    if not isinstance(gen, dict):
        return False
    body = gen.get("body")
    return isinstance(body, str) and bool(body.strip())


def row_triage_status(row: dict[str, Any]) -> str | None:
    triage = row.get("triage")
    if not isinstance(triage, dict):
        return None
    status = triage.get("status")
    return status if isinstance(status, str) else None


def absorb_row(status: EmailStatus, row: dict[str, Any]) -> None:
    if row_generated(row):
        status.has_generated = True
    triage_status = row_triage_status(row)
    if triage_status in TERMINAL_TRIAGE_STATUSES:
        status.has_terminal = True
    if triage_status == TRIAGE_APPROVED:
        status.has_approved = True


def build_email_statuses(by_id: dict[str, Any]) -> dict[str, EmailStatus]:
    out: dict[str, EmailStatus] = {}
    for _, maybe_row in sorted(by_id.items(), key=lambda kv: str(kv[0])):
        if not isinstance(maybe_row, dict):
            continue
        email = normalize_email(maybe_row.get("primary_email"))
        if not email:
            continue
        status = out.setdefault(email, EmailStatus())
        absorb_row(status, maybe_row)
    return out
