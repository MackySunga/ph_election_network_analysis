
"""Visible progress helpers for the Philippine Election Network Science notebooks.

These helpers are intentionally lightweight. They print clear stage messages, show a
`tqdm` progress bar when available, and write a small run log under outputs/run_logs/.
"""
from __future__ import annotations

from pathlib import Path
import time
from datetime import datetime

try:
    from tqdm.auto import tqdm
except Exception:  # pragma: no cover
    tqdm = None


def _safe_root(root=None):
    if root is not None:
        return Path(root)
    cwd = Path.cwd()
    return cwd.parent if cwd.name == "notebooks" else cwd


class NotebookProgress:
    def __init__(self, notebook_name: str, total_steps: int, root=None, use_tqdm: bool = True):
        self.notebook_name = str(notebook_name)
        self.total_steps = max(int(total_steps), 1)
        self.current = 0
        self.start = time.time()
        self.root = _safe_root(root)
        self.log_dir = self.root / "outputs" / "run_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        safe_name = ''.join(ch if ch.isalnum() or ch in ('-', '_') else '_' for ch in self.notebook_name)
        self.log_file = self.log_dir / f"{safe_name}.log"
        self.pbar = None
        self._write_log("=" * 80)
        self._write_log(f"Started {self.notebook_name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if use_tqdm and tqdm is not None:
            try:
                self.pbar = tqdm(total=self.total_steps, desc=self.notebook_name, unit="stage")
            except Exception:
                self.pbar = None
        print(f"▶ Starting {self.notebook_name} — {self.total_steps} tracked stages")
        print(f"   Log: {self.log_file}")

    def _write_log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass

    def step(self, label: str):
        self.current = min(self.current + 1, self.total_steps)
        elapsed = time.time() - self.start
        pct = (self.current / self.total_steps) * 100
        msg = f"[{self.current:02d}/{self.total_steps:02d} | {pct:5.1f}%] {label} | elapsed {elapsed:,.1f}s"
        print(msg, flush=True)
        self._write_log(msg)
        if self.pbar is not None:
            try:
                self.pbar.update(1)
                self.pbar.set_postfix_str(str(label)[:60])
            except Exception:
                pass

    def info(self, label: str):
        elapsed = time.time() - self.start
        msg = f"[info | elapsed {elapsed:,.1f}s] {label}"
        print(msg, flush=True)
        self._write_log(msg)

    def done(self, label: str = "Notebook completed"):
        elapsed = time.time() - self.start
        if self.pbar is not None:
            try:
                remaining = self.total_steps - self.current
                if remaining > 0:
                    self.pbar.update(remaining)
                self.pbar.close()
            except Exception:
                pass
        msg = f"✓ {label} | total elapsed {elapsed:,.1f}s"
        print(msg, flush=True)
        self._write_log(msg)


def make_tracker(notebook_name: str, total_steps: int, root=None, use_tqdm: bool = True) -> NotebookProgress:
    return NotebookProgress(notebook_name=notebook_name, total_steps=total_steps, root=root, use_tqdm=use_tqdm)
