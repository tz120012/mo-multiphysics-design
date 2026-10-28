"""Celery task package (optional Redis broker)."""

from app.tasks.analytic import run_analytic_job
from app.tasks.fem import run_fem_job

__all__ = ["run_analytic_job", "run_fem_job"]
