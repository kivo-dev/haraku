FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --system --uid 10001 harako && chown -R harako /srv
USER harako
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2).status==200 else 1)"
# Schema changes are applied by a separate step:  alembic upgrade head   (see docker-compose.yml "migrate")
# --no-access-log: access lines contain the query string (user coordinates). Our own filter redacts
# them when access logging is turned on again.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log --workers ${WEB_CONCURRENCY:-1}"]
