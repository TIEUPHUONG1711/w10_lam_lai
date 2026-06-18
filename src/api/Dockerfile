FROM python:3.13-alpine

RUN pip install flask prometheus-flask-exporter

COPY app.py /app/app.py

WORKDIR /app

EXPOSE 8080

CMD ["python", "app.py"]