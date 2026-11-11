# Image minimale, utilisateur non root, aucune dépendance de build en production
FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NOTES_DB=/data/notes.db

RUN groupadd --system app && useradd --system --gid app --no-create-home app \
    && mkdir /data && chown app:app /data

WORKDIR /srv
COPY requirements.txt .
# pip, setuptools et ensurepip embarquent leurs propres copies de certifi, urllib3, msgpack…
# Inutiles à l'exécution, on les retire pour réduire la surface d'attaque (et les CVE remontées par Trivy).
RUN pip install -r requirements.txt \
    && pip uninstall -y setuptools wheel pip \
    && rm -rf /usr/local/lib/python3.13/ensurepip /root/.cache
COPY app ./app

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app:create_app()"]
