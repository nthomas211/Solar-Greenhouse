FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache build-base

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the worker script
CMD ["python", "cli_runner.py"]