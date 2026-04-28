#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch build runner — executes multiple build jobs sequentially."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from engine.builder import Builder  # imported at module level so tests can patch it

logger = logging.getLogger(__name__)


@dataclass
class BatchJob:
    """One build job in the batch."""

    job_id: str                          # unique ID (e.g. "job_001")
    project_id: str
    owner_id: str
    selected_codes: list[str]
    output_path: Path
    template_vars: dict[str, str] = field(default_factory=dict)
    boq_order: list[str] = field(default_factory=list)


@dataclass
class BatchJobResult:
    job_id: str
    success: bool
    output_path: Optional[Path]
    error_ar: Optional[str]
    elapsed_seconds: float


class BatchRunner:
    """Runs a list of BatchJob items sequentially using Builder."""

    def __init__(self, codes: dict) -> None:
        self._codes = codes

    def run(
        self,
        jobs: list[BatchJob],
        on_job_start: Callable[[int, int, str], None] | None = None,
        on_job_done: Callable[[BatchJobResult], None] | None = None,
        on_all_done: Callable[[list[BatchJobResult]], None] | None = None,
    ) -> list[BatchJobResult]:
        """Run all jobs sequentially. Callbacks called on each step.

        Args:
            jobs: list of BatchJob to execute
            on_job_start: called with (job_index, total, job_id) before each job
            on_job_done: called with BatchJobResult after each job
            on_all_done: called with all results when finished

        Returns: list of BatchJobResult
        """
        import time

        builder = Builder(self._codes)
        results: list[BatchJobResult] = []

        for idx, job in enumerate(jobs):
            if on_job_start:
                on_job_start(idx, len(jobs), job.job_id)

            t0 = time.monotonic()
            try:
                success, error_ar = builder.build(
                    selected_codes=job.selected_codes,
                    project_id=job.project_id,
                    owner_id=job.owner_id,
                    output_path=job.output_path,
                    template_vars=job.template_vars or None,
                    boq_order=job.boq_order or None,
                )
            except Exception as exc:
                success = False
                error_ar = str(exc)
                logger.error("Batch job %s failed: %s", job.job_id, exc)

            elapsed = time.monotonic() - t0
            result = BatchJobResult(
                job_id=job.job_id,
                success=success,
                output_path=job.output_path if success else None,
                error_ar=error_ar if not success else None,
                elapsed_seconds=round(elapsed, 2),
            )
            results.append(result)

            if on_job_done:
                on_job_done(result)

        if on_all_done:
            on_all_done(results)

        return results
