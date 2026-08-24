FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

COPY . .
RUN mkdir -p /app/data

EXPOSE 5075

CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5075", "--timeout", "120", "run:app"]
