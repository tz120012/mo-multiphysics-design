# Mo API — Q1 FastAPI shell
# Build from repo root (required so packages/solver-analytic can be shipped):
#   docker build -f apps/api/Dockerfile .
# Compose: api.build.context=.  dockerfile: apps/api/Dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SOLVER_ANALYTIC_PATH=/opt/mo/packages/solver-analytic \
    SOLVER_FEM_PATH=/opt/mo/packages/solver-fem \
    MO_FEM_DRY_RUN=1 \
    SOLVER_OPT_PATH=/opt/mo/packages/solver-opt

COPY apps/api/requirements.txt .
RUN pip install -r requirements.txt

COPY apps/api/app ./app
# Sync analytic solve (packages/solver-analytic) — needed for POST /api/v1/solver/analytic/solve
COPY packages/solver-analytic /opt/mo/packages/solver-analytic
COPY packages/solver-fem /opt/mo/packages/solver-fem
COPY packages/solver-opt /opt/mo/packages/solver-opt

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=5s --retries=12 --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
