#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for utils.batch_runner — no PyQt5 required."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from utils.batch_runner import BatchJob, BatchJobResult, BatchRunner


def _make_job(job_id: str = "job_001") -> BatchJob:
    return BatchJob(
        job_id=job_id,
        project_id="wastewater",
        owner_id="nwc",
        selected_codes=["001-SUR-BASE", "002-EXC-FINE"],
        output_path=Path(f"output/{job_id}.docx"),
    )


# ---------------------------------------------------------------------------
# 1. Empty list
# ---------------------------------------------------------------------------

def test_run_empty_returns_empty_list():
    runner = BatchRunner(codes={})
    with patch("utils.batch_runner.Builder"):
        results = runner.run([])
    assert results == []


# ---------------------------------------------------------------------------
# 2. Single job succeeds
# ---------------------------------------------------------------------------

def test_single_job_success():
    job = _make_job("job_001")
    with patch("utils.batch_runner.Builder") as MockBuilder:
        MockBuilder.return_value.build.return_value = (True, None)
        runner = BatchRunner(codes={"001-SUR-BASE": {}})
        results = runner.run([job])

    assert len(results) == 1
    r = results[0]
    assert r.job_id == "job_001"
    assert r.success is True
    assert r.output_path == job.output_path
    assert r.error_ar is None
    assert r.elapsed_seconds >= 0


# ---------------------------------------------------------------------------
# 3. Single job failure is captured (not raised)
# ---------------------------------------------------------------------------

def test_single_job_failure_captured():
    job = _make_job("job_fail")
    with patch("utils.batch_runner.Builder") as MockBuilder:
        MockBuilder.return_value.build.return_value = (False, "خطأ في البناء")
        runner = BatchRunner(codes={})
        results = runner.run([job])

    assert len(results) == 1
    r = results[0]
    assert r.success is False
    assert r.error_ar == "خطأ في البناء"
    assert r.output_path is None


# ---------------------------------------------------------------------------
# 4. Exception in builder is captured (not raised)
# ---------------------------------------------------------------------------

def test_single_job_exception_captured():
    job = _make_job("job_exc")
    with patch("utils.batch_runner.Builder") as MockBuilder:
        MockBuilder.return_value.build.side_effect = RuntimeError("crash!")
        runner = BatchRunner(codes={})
        results = runner.run([job])

    assert len(results) == 1
    r = results[0]
    assert r.success is False
    assert "crash!" in r.error_ar
    assert r.output_path is None


# ---------------------------------------------------------------------------
# 5. Multiple jobs — all results returned
# ---------------------------------------------------------------------------

def test_multiple_jobs_all_results_returned():
    jobs = [_make_job(f"job_{i:03d}") for i in range(4)]
    with patch("utils.batch_runner.Builder") as MockBuilder:
        MockBuilder.return_value.build.return_value = (True, None)
        runner = BatchRunner(codes={})
        results = runner.run(jobs)

    assert len(results) == 4
    assert all(r.success for r in results)
    assert [r.job_id for r in results] == ["job_000", "job_001", "job_002", "job_003"]


# ---------------------------------------------------------------------------
# 6. on_job_start callback called for each job
# ---------------------------------------------------------------------------

def test_on_job_start_called_for_each_job():
    jobs = [_make_job(f"j{i}") for i in range(3)]
    starts = []

    def on_start(idx, total, job_id):
        starts.append((idx, total, job_id))

    with patch("utils.batch_runner.Builder") as MockBuilder:
        MockBuilder.return_value.build.return_value = (True, None)
        runner = BatchRunner(codes={})
        runner.run(jobs, on_job_start=on_start)

    assert starts == [
        (0, 3, "j0"),
        (1, 3, "j1"),
        (2, 3, "j2"),
    ]


# ---------------------------------------------------------------------------
# 7. on_job_done callback called for each job
# ---------------------------------------------------------------------------

def test_on_job_done_called_for_each_job():
    jobs = [_make_job(f"d{i}") for i in range(3)]
    done_results: list[BatchJobResult] = []

    with patch("utils.batch_runner.Builder") as MockBuilder:
        MockBuilder.return_value.build.return_value = (True, None)
        runner = BatchRunner(codes={})
        runner.run(jobs, on_job_done=done_results.append)

    assert len(done_results) == 3
    assert [r.job_id for r in done_results] == ["d0", "d1", "d2"]


# ---------------------------------------------------------------------------
# 8. on_all_done called at end with all results
# ---------------------------------------------------------------------------

def test_on_all_done_called_at_end():
    jobs = [_make_job("a1"), _make_job("a2")]
    all_done_capture: list[list[BatchJobResult]] = []

    with patch("utils.batch_runner.Builder") as MockBuilder:
        MockBuilder.return_value.build.return_value = (True, None)
        runner = BatchRunner(codes={})
        runner.run(jobs, on_all_done=all_done_capture.append)

    assert len(all_done_capture) == 1
    all_results = all_done_capture[0]
    assert len(all_results) == 2
    assert all(isinstance(r, BatchJobResult) for r in all_results)


# ---------------------------------------------------------------------------
# 9. Mixed success/failure in a multi-job batch
# ---------------------------------------------------------------------------

def test_mixed_success_failure():
    jobs = [_make_job(f"m{i}") for i in range(3)]

    side_effects = [(True, None), (False, "فشل الوظيفة الثانية"), (True, None)]

    with patch("utils.batch_runner.Builder") as MockBuilder:
        MockBuilder.return_value.build.side_effect = side_effects
        runner = BatchRunner(codes={})
        results = runner.run(jobs)

    assert results[0].success is True
    assert results[1].success is False
    assert results[1].error_ar == "فشل الوظيفة الثانية"
    assert results[2].success is True


# ---------------------------------------------------------------------------
# 10. boq_order and template_vars forwarded correctly
# ---------------------------------------------------------------------------

def test_build_called_with_correct_args():
    job = BatchJob(
        job_id="job_args",
        project_id="roads",
        owner_id="mot",
        selected_codes=["001-SUR-BASE"],
        output_path=Path("output/roads.docx"),
        template_vars={"client": "وزارة النقل"},
        boq_order=["001-SUR-BASE"],
    )

    with patch("utils.batch_runner.Builder") as MockBuilder:
        mock_instance = MockBuilder.return_value
        mock_instance.build.return_value = (True, None)
        runner = BatchRunner(codes={"001-SUR-BASE": {}})
        runner.run([job])

    mock_instance.build.assert_called_once_with(
        selected_codes=["001-SUR-BASE"],
        project_id="roads",
        owner_id="mot",
        output_path=Path("output/roads.docx"),
        template_vars={"client": "وزارة النقل"},
        boq_order=["001-SUR-BASE"],
    )


# ---------------------------------------------------------------------------
# 11. Empty boq_order / template_vars converted to None
# ---------------------------------------------------------------------------

def test_empty_boq_and_vars_passed_as_none():
    job = BatchJob(
        job_id="job_empty",
        project_id="wastewater",
        owner_id="nwc",
        selected_codes=["001-SUR-BASE"],
        output_path=Path("output/empty.docx"),
        template_vars={},   # empty dict → None
        boq_order=[],       # empty list → None
    )

    with patch("utils.batch_runner.Builder") as MockBuilder:
        mock_instance = MockBuilder.return_value
        mock_instance.build.return_value = (True, None)
        runner = BatchRunner(codes={})
        runner.run([job])

    _, kwargs = mock_instance.build.call_args
    assert kwargs["template_vars"] is None
    assert kwargs["boq_order"] is None
