# The website: FastAPI serving the API and the built React frontend, one process.
# Build: docker build -t adondeva .    Run: docker run -p 8080:8080 adondeva

FROM node:22-slim AS frontend
WORKDIR /app
COPY web/frontend/package.json web/frontend/package-lock.json ./
RUN npm ci
COPY web/frontend/ ./
RUN npm run build

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY web/backend/requirements.txt web/backend/requirements.txt
RUN pip install --no-cache-dir -r web/backend/requirements.txt
COPY adondeva.py ./
COPY data/ data/
COPY web/ web/
COPY --from=frontend /app/dist web/frontend/dist
# Read the large budget files once at build time so the server starts in seconds, not ~15 s.
RUN python -c "import adondeva as ad; ad.spending_series(False); ad.spending_series(True); [ad.detail_mef_year(p) for s, p in ad.detail_sources().values() if s == 'mef']"
RUN useradd --system app && chown -R app /app/.cache
EXPOSE 8080
# Fly mounts the usage-log volume owned by root: hand it to `app`, then drop privileges for the server.
CMD ["sh", "-c", "mkdir -p /data && chown app /data && exec setpriv --reuid=app --regid=app --init-groups uvicorn web.backend.app:app --host 0.0.0.0 --port 8080 --proxy-headers --forwarded-allow-ips '*'"]
