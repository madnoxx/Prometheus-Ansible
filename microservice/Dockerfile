FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir prometheus-client

COPY app.py .

EXPOSE 8080

CMD ["python", "-u", "app.py"]
