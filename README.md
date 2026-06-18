## 1. Overview

Project này mô phỏng một DevSecOps platform chạy trên Kubernetes.

Flow tổng thể:

```text
Developer
↓
GitHub
↓
GitHub Actions
↓
Docker Build
↓
GHCR
↓
ArgoCD
↓
Argo Rollouts
↓
Prometheus
↓
AlertManager
````

## 2. Components

| Folder              | Ý nghĩa                                  |
| ------------------- | ---------------------------------------- |
| `src/api`           | Flask API có `/`, `/healthz`, `/metrics` |
| `app-common`        | Tạo namespace `demo`                     |
| `app-api`           | Rollout, Service, ServiceMonitor         |
| `app-analysis`      | AnalysisTemplate kiểm tra success rate   |
| `app-alert`         | PrometheusRule cảnh báo runtime          |
| `argocd/apps`       | Child apps cho ArgoCD                    |
| `argocd/root.yaml`  | Root App of Apps                         |
| `.github/workflows` | CI/CD build, push, validate              |

## 3. Quick Start

### Start cluster

```powershell
minikube start -p w10-lab --cpus=4 --memory=7000
kubectl config use-context w10-lab
kubectl get nodes
```

### Install ArgoCD

```powershell
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl get pods -n argocd
```

### Deploy root app

```powershell
kubectl apply -f argocd/root.yaml
kubectl get application -n argocd
```

## 4. Sync Waves

| Wave | App                                      | Ý nghĩa                                |
| ---- | ---------------------------------------- | -------------------------------------- |
| `-1` | `common`                                 | Tạo namespace `demo`                   |
| `0`  | `kube-prometheus-stack`, `argo-rollouts` | Cài CRD và controller                  |
| `1`  | `analysis`, `alert`                      | Tạo AnalysisTemplate và PrometheusRule |
| `2`  | `api`                                    | Deploy API sau cùng                    |

Thứ tự này đảm bảo:

```text
Namespace trước
↓
CRD trước
↓
Rule trước
↓
App sau cùng
```

## 5. Verify Deployment

### ArgoCD apps

```powershell
kubectl get application -n argocd
```

Kỳ vọng:

```text
root                    Synced   Healthy
common                  Synced   Healthy
argo-rollouts           Synced   Healthy
kube-prometheus-stack   Synced   Healthy
analysis                Synced   Healthy
alert                   Synced   Healthy
api                     Synced   Healthy
```

### Rollout

```powershell
kubectl argo rollouts get rollout api -n demo
```

Kỳ vọng:

```text
Status: Healthy
Ready: 5
Available: 5
```

### Pods

```powershell
kubectl get pods -n demo
```

## 6. Access API

```powershell
kubectl port-forward svc/api 8080:80 -n demo
```

Mở:

```text
http://localhost:8080
```

Kỳ vọng:

```json
{
  "ok": true,
  "version": "v2"
}
```

Metrics:

```text
http://localhost:8080/metrics
```

## 7. Monitoring

### Prometheus

```powershell
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
```

Open:

```text
http://localhost:9090
```

Query:

```promql
flask_http_request_total
```

### Grafana

```powershell
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
```

Open:

```text
http://localhost:3000
```

Username:

```text
admin
```

Get password:

```powershell
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String((kubectl get secret kube-prometheus-stack-grafana -n monitoring -o jsonpath="{.data.admin-password}")))
```

## 8. Email Alert Setup

Copy secret example:

```powershell
copy app-alert\email-secret.yaml.example app-alert\email-secret.yaml
```

Edit:

```yaml
stringData:
  smtp-user: your-email@gmail.com
  smtp-password: YOUR_GMAIL_APP_PASSWORD
```

Apply:

```powershell
kubectl apply -f app-alert\email-secret.yaml
kubectl get secret alertmanager-email -n monitoring
```

Important:

```text
Do not commit email-secret.yaml
Commit only email-secret.yaml.example
```

## 9. Test Successful Canary

Update API version or image.

Push code:

```powershell
git add .
git commit -m "test successful canary"
git push origin main
```

Watch rollout:

```powershell
kubectl argo rollouts get rollout api -n demo --watch
```

Expected:

```text
10%
↓
50%
↓
100%
↓
Healthy
```

## 10. Test Failed Canary

Set:

```yaml
- name: ERROR_RATE
  value: "0.5"
```

Push:

```powershell
git add .
git commit -m "test failed canary"
git push origin main
```

Generate traffic:

```powershell
kubectl port-forward svc/api 8080:80 -n demo
```

In another terminal:

```powershell
1..300 | % { try { Invoke-WebRequest http://localhost:8080 | Out-Null } catch {} }
```

Watch:

```powershell
kubectl get analysisrun -n demo
kubectl argo rollouts get rollout api -n demo
```

Expected:

```text
AnalysisRun Failed
Rollout stops or rolls back
```

## 11. Test Runtime Alert

Set:

```yaml
- name: ERROR_RATE
  value: "1"
```

Generate traffic:

```powershell
1..100 | % { try { Invoke-WebRequest http://localhost:8080 | Out-Null } catch {} }
```

Open Prometheus alerts:

```text
http://localhost:9090/alerts
```

Expected:

```text
ApiHighErrorRate = Firing
```

If AlertManager email is configured, email notification should be sent.

## 12. CI/CD

### Build Push

Workflow:

```text
.github/workflows/build-push.yml
```

It performs:

```text
Docker build
↓
Docker push to GHCR
↓
Update rollout.yaml
↓
Commit manifest
```

### Validate

Workflow:

```text
.github/workflows/validate.yml
```

It checks Kubernetes manifests before ArgoCD sync.

## 13. Cleanup

Delete root app:

```powershell
kubectl delete -f argocd/root.yaml
```

Delete namespaces:

```powershell
kubectl delete ns demo
kubectl delete ns monitoring
kubectl delete ns argo-rollouts
kubectl delete ns argocd
```

Stop cluster:

```powershell
minikube stop -p w10-lab
```

Delete cluster:

```powershell
minikube delete -p w10-lab
```

## 14. Troubleshooting

### Rollout kind not found

```text
no matches for kind "Rollout"
```

Fix:

```powershell
kubectl get crd | findstr rollouts
```

Install Argo Rollouts first.

### ServiceMonitor kind not found

```text
no matches for kind "ServiceMonitor"
```

Fix:

```powershell
kubectl get crd | findstr servicemonitors
```

Install kube-prometheus-stack first.

### ImagePullBackOff

Check image:

```powershell
kubectl describe pod <pod-name> -n demo
```

Common reasons:

```text
GHCR package private
wrong image tag
missing package permission
```

### ArgoCD OutOfSync

Refresh:

```powershell
kubectl annotate application api -n argocd argocd.argoproj.io/refresh=hard --overwrite
```

### OOMKilled

Scale down heavy monitoring components temporarily:

```powershell
kubectl scale statefulset prometheus-kube-prometheus-stack-prometheus -n monitoring --replicas=0
kubectl scale deployment kube-prometheus-stack-grafana -n monitoring --replicas=0
```

## 15. Final Evidence

Use these commands for screenshots:

```powershell
kubectl get application -n argocd
kubectl argo rollouts get rollout api -n demo
kubectl get pods -n demo
kubectl get servicemonitor -n demo
kubectl get prometheusrule -n demo
kubectl get analysistemplate -n demo
kubectl get analysisrun -n demo
```

````

Commit:

```powershell
git add README.md
git commit -m "add project readme runbook"
git push origin main
````
