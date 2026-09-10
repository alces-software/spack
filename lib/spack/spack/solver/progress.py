# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
"""Verbose progress for the ASP concretizer setup and solve phases.

Enabled by ``spack -v``. Status lines go to stderr so ``spack spec --json``
on stdout stays machine-readable. On a TTY, counters rewrite in place;
otherwise only phase transitions and coarse checkpoints are printed.
"""

import sys
import time
from typing import IO, Optional

from spack.util import tty


class ConcretizerProgress:
    """Live setup/solve progress, no-op unless verbose mode is on."""

    def __init__(self, stream: Optional[IO[str]] = None) -> None:
        self.enabled = tty.is_verbose()
        self.stream = stream or sys.stderr
        self._tty = hasattr(self.stream, "isatty") and self.stream.isatty()
        self._last_len = 0
        self._last_non_tty = 0.0
        self._status_open = False

    def __enter__(self) -> "ConcretizerProgress":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.finish()

    def phase(self, message: str) -> None:
        """Named phase, e.g. ``Concretizing hdf5`` or ``grounding``."""
        self.finish()
        if self.enabled:
            tty.verbose(message, stream=self.stream)

    def count(self, n: int, what: str) -> None:
        """One-line tally, e.g. ``1402 reuse candidates``."""
        self.finish()
        if self.enabled:
            tty.verbose(f"{n} {what}", stream=self.stream)

    def item(self, label: str, i: int, n: int, name: str) -> None:
        """Counter for a loop, e.g. ``package rules [  48/312] cmake``."""
        if not self.enabled or n <= 0:
            return
        text = f"{label} [{i:4d}/{n}] {name}"
        if self._tty:
            self._rewrite(text)
            return
        if i == 1 or i == n or i % 25 == 0:
            print(f"    {text}", file=self.stream, flush=True)

    def heartbeat(self, elapsed: float, nmodels: int) -> None:
        """Rewrite (or periodically print) the clingo search status."""
        if not self.enabled:
            return
        models = "model" if nmodels == 1 else "models"
        text = f"solving... {elapsed:5.1f}s ({nmodels} {models})"
        if self._tty:
            self._rewrite(text)
            return
        now = time.monotonic()
        if self._last_non_tty == 0.0 or now - self._last_non_tty >= 10.0:
            print(f"    {text}", file=self.stream, flush=True)
            self._last_non_tty = now

    def done(self, message: str) -> None:
        """Close a status line with a final message."""
        if not self.enabled:
            return
        if self._tty and self._status_open:
            self._rewrite(message, final=True)
        else:
            self.finish()
            print(f"    {message}", file=self.stream, flush=True)

    def finish(self) -> None:
        """End an in-place status line so later output is not glued to it."""
        if self._status_open:
            print(file=self.stream, flush=True)
            self._status_open = False
            self._last_len = 0

    def _rewrite(self, text: str, *, final: bool = False) -> None:
        line = f"    {text}"
        pad = max(0, self._last_len - len(line))
        end = "\n" if final else ""
        print(f"\r{line}{' ' * pad}", end=end, flush=True, file=self.stream)
        self._last_len = 0 if final else len(line)
        self._status_open = not final
