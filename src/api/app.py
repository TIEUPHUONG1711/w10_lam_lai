import os
import random
from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

# Tự tạo endpoint /metrics rồi expose ra enpoint /metrics để prometheus có thể scrape được metrics của app
PrometheusMetrics(app)

ERROR_RATE = float(os.getenv("ERROR_RATE", "0"))
VERSION = os.getenv("VERSION", "v1")


@app.get("/") #api chính để user gọi
def index():
    if random.random() < ERROR_RATE:
        return jsonify(error="injected", version=VERSION), 500

    return jsonify(ok=True, version=VERSION)


@app.get("/healthz") # endpoint để ktra pod còn sống ko
def healthz():
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
    
    
# Nói ngắn gọn: file app.py tồn tại để tạo một API thật có health check và metrics, giúp Kubernetes,
# Prometheus và Argo Rollouts hoạt động trong các bài lab Canary Deployment và Monitoring.    