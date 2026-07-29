FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DQ_HOST=0.0.0.0
ENV DQ_PORT=8000

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

RUN mkdir -p \
    /app/denodo_agent_poc/runtime_data/source \
    /app/denodo_agent_poc/runtime_data/results \
    /app/denodo_agent_poc/runtime_data/logs

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/portal-status', timeout=5)"

CMD ["python", "-m", "uvicorn", "agent_portal_v4:app", "--app-dir", "denodo_agent_poc/src/api", "--host", "0.0.0.0", "--port", "8000"]