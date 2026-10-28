"""Celery task package (optional Redis broker)."""

from app.tasks.analytic import run_analytic_job

__all__ = ["run_analytic_job"]
