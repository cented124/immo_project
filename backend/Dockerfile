FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt && useradd --uid 10001 --create-home app && mkdir /data && chown app:app /data
COPY --chown=app:app backend backend
COPY --chown=app:app templates templates
COPY --chown=app:app docs docs
COPY --chown=app:app .github .github
COPY --chown=app:app project /seed
COPY --chown=app:app project/README.md project/README.md
COPY --chown=app:app frontend/app frontend/app
COPY --chown=app:app frontend/components frontend/components
COPY --chown=app:app frontend/public frontend/public
COPY --chown=app:app frontend/tests frontend/tests
COPY --chown=app:app frontend/*.json frontend/*.ts frontend/Dockerfile frontend/AGENTS.md frontend/
COPY --chown=app:app scripts scripts
COPY --chown=app:app ["Deine PDF-Vorlage", "Deine PDF-Vorlage"]
COPY --chown=app:app README.md ANLEITUNG-WINDOWS.md ANLEITUNG-WINDOWS.html STARTEN.cmd STOPPEN.cmd DIAGNOSE.cmd REPARIEREN.cmd SICHERN.cmd STARTEN-DOCKER.cmd STOPPEN-DOCKER.cmd LIVE-STARTEN.sh compose.yaml compose.production.yaml Caddyfile .env.example .dockerignore .gitignore .gitattributes ./
ENV PYTHONPATH=/app/backend
USER app
CMD ["sh", "-c", "alembic -c backend/alembic.ini upgrade head && python -m app.cli import-project && uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log"]
