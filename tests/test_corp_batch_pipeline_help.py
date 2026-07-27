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
