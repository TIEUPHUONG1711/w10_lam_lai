# App Alert Module

## Mục đích

Module này triển khai runtime alerting cho ứng dụng.

Flow hoạt động:

Application
↓
Prometheus Metrics
↓
PrometheusRule
↓
AlertManager
↓
Email Notification

## Các file

### prometheus-rules.yaml

Tạo các cảnh báo runtime:

* ApiHighErrorRate
* ApiDown

### email-secret.yaml.example

File mẫu cấu hình Gmail SMTP.

Không chứa thông tin nhạy cảm.

### email-secret.yaml

File chứa Gmail App Password thật.

Không commit file này lên Git.

### .argocdignore

Yêu cầu ArgoCD bỏ qua các file nhạy cảm hoặc file local.

---

## Cấu hình Email

### Bước 1: Tạo file secret thật

Copy file mẫu:

```bash
cp email-secret.yaml.example email-secret.yaml
```

Hoặc trên Windows:

```powershell
copy email-secret.yaml.example email-secret.yaml
```

### Bước 2: Điền Gmail App Password

Ví dụ:

```yaml
stringData:
  smtp-user: your-email@gmail.com
  smtp-password: YOUR_APP_PASSWORD
```

Lưu ý:

* Không dùng mật khẩu Gmail thông thường
* Phải dùng Google App Password

### Bước 3: Apply Secret

```bash
kubectl apply -f email-secret.yaml
```

Kiểm tra:

```bash
kubectl get secret -n monitoring
```

---

## Triển khai Alert Rules

Apply rule:

```bash
kubectl apply -f prometheus-rules.yaml
```

Kiểm tra:

```bash
kubectl get prometheusrule -n demo
```

---

## Kiểm tra Alert

Mở Prometheus:

```text
http://localhost:9090
```

Trang Alerts:

```text
http://localhost:9090/alerts
```

Kiểm tra các alert:

* ApiHighErrorRate
* ApiDown

---

## Test Error Alert

Tăng ERROR_RATE:

```yaml
- name: ERROR_RATE
  value: "1"
```

Apply rollout mới.

Tạo traffic:

```powershell
1..100 | % { try { Invoke-WebRequest http://localhost:8080 | Out-Null } catch {} }
```

Kỳ vọng:

```text
ApiHighErrorRate = Firing
```

---

## Security Notes

Không commit:

```text
email-secret.yaml
```

Luôn commit:

```text
email-secret.yaml.example
```

File `.gitignore` và `.argocdignore` phải chứa:

```text
email-secret.yaml
```
