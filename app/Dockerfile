# Multi-stage build: builder installs deps into a virtualenv, runtime
# image copies only the venv + app code. Keeps the final image small.

FROM python:3.12-slim AS builder
WORKDIR /build
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime
ENV PATH="/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY --from=builder /venv /venv
WORKDIR /app
COPY app.py ./
COPY templates ./templates
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
