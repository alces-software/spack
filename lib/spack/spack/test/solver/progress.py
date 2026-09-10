# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import io

import pytest

from spack.solver.progress import ConcretizerProgress
from spack.util import tty


class TtyIO(io.StringIO):
    def isatty(self) -> bool:
        return True


@pytest.fixture
def verbose(monkeypatch):
    monkeypatch.setattr(tty, "_verbose", True)


def test_progress_noop_when_not_verbose():
    stream = io.StringIO()
    progress = ConcretizerProgress(stream=stream)
    progress.phase("Concretizing hdf5")
    progress.count(12, "possible packages")
    progress.item("package rules", 1, 12, "hdf5")
    progress.heartbeat(1.5, 0)
    progress.finish()
    assert stream.getvalue() == ""


def test_progress_phase_and_counts_go_to_stream(verbose):
    stream = io.StringIO()
    progress = ConcretizerProgress(stream=stream)
    progress.phase("Concretizing hdf5")
    progress.count(12, "possible packages")
    # tty.verbose writes via color to the given stream
    out = stream.getvalue()
    assert "Concretizing hdf5" in out
    assert "12 possible packages" in out


def test_progress_item_rewrites_on_tty(verbose):
    stream = TtyIO()
    progress = ConcretizerProgress(stream=stream)
    progress.item("package rules", 1, 3, "cmake")
    progress.item("package rules", 3, 3, "zlib")
    progress.finish()
    text = stream.getvalue()
    assert "package rules [   1/3] cmake" in text
    assert "package rules [   3/3] zlib" in text
    assert "\r" in text


def test_progress_item_checkpoints_on_pipe(verbose):
    stream = io.StringIO()
    progress = ConcretizerProgress(stream=stream)
    for i in range(1, 26):
        progress.item("package rules", i, 25, f"pkg{i}")
    text = stream.getvalue()
    assert "package rules [   1/25] pkg1" in text
    assert "package rules [  25/25] pkg25" in text
    assert "package rules [  25/25] pkg25" in text
    # intermediate packages besides 1, 25, and multiples of 25 are omitted
    assert "pkg2\n" not in text


def test_progress_heartbeat_and_done_on_tty(verbose):
    stream = TtyIO()
    progress = ConcretizerProgress(stream=stream)
    progress.heartbeat(1.2, 0)
    progress.heartbeat(2.4, 1)
    progress.done("solved in 2.4s (1 model)")
    text = stream.getvalue()
    assert "solving...   2.4s (1 model)" in text
    assert "solved in 2.4s (1 model)" in text
    assert text.endswith("\n")
