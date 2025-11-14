# ServiceMonitor CRD 설치 가이드

ServiceMonitor CRD는 Prometheus Operator의 일부로 제공됩니다.

## 현재 상태 확인

```bash
# ServiceMonitor CRD 확인
kubectl get crd servicemonitors.monitoring.coreos.com

# Prometheus Operator 확인
kubectl get pods -A | grep prometheus-operator
```

## 설치 방법

### 옵션 1: Helm 사용 (권장)

```bash
# Helm repo 추가
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Prometheus Operator 설치 (전체 스택)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

# 또는 Prometheus Operator만 설치
helm install prometheus-operator prometheus-community/prometheus-operator \
  --namespace monitoring \
  --create-namespace
```

### 옵션 2: YAML 매니페스트 사용

```bash
# Prometheus Operator bundle 다운로드 및 적용
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml
```

### 옵션 3: GKE Managed Prometheus (GKE 환경)

GKE 환경에서는 Managed Prometheus를 사용할 수 있습니다:

```bash
# GKE Managed Prometheus 활성화 (관리 콘솔에서)
# 또는 gcloud 명령어로 활성화
```

## 설치 후 확인

```bash
# CRD 확인
kubectl get crd servicemonitors.monitoring.coreos.com

# API 리소스 확인
kubectl api-resources | grep servicemonitor
```

## 정책 활성화

ServiceMonitor CRD가 설치되면, 정책 파일에서 주석을 해제하세요:

```bash
# 파일 편집
vim portal_front/policies/kyverno/validate-crds-hpa-servicemonitor-externalsecret.yaml

# 또는 sed로 자동 주석 해제
sed -i 's/^    # - name: validate-servicemonitor/    - name: validate-servicemonitor/' \
  portal_front/policies/kyverno/validate-crds-hpa-servicemonitor-externalsecret.yaml

sed -i 's/^    #   match:/  match:/' \
  portal_front/policies/kyverno/validate-crds-hpa-servicemonitor-externalsecret.yaml

# 정책 재적용
kubectl apply -f portal_front/policies/kyverno/validate-crds-hpa-servicemonitor-externalsecret.yaml
```

## 참고

- ServiceMonitor CRD는 `monitoring.coreos.com/v1` API 그룹을 사용합니다
- Prometheus Operator가 설치되어 있어야 ServiceMonitor를 사용할 수 있습니다
- GKE 환경에서는 Managed Prometheus 사용을 고려할 수 있습니다

