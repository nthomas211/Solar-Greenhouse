FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    python3-gi \
    gir1.2-gtk-3.0 \
    libgirepository1.0-dev \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["uvicorn", "app.server.api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]