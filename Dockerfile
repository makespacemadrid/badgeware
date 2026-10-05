FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --create-home app

COPY requirements.txt ./
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

COPY --chown=app:app tshirt_templates ./tshirt_templates
COPY --chown=app:app static ./static
COPY --chown=app:app templates ./templates
RUN mkdir -p instance/uploads instance/templates && chown -R app:app instance

USER app

EXPOSE 5000
VOLUME ["/app/instance"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '5000') + '/api/v1/health', timeout=3)" || exit 1

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers ${WEB_CONCURRENCY:-2} --access-logfile - --error-logfile - tshirt_templates.app:app"]

