{{- define "api-observability-rollout.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "api-observability-rollout.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s" (include "api-observability-rollout.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end }}

{{- define "api-observability-rollout.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "api-observability-rollout.name" . }}
app.kubernetes.io/instance: {{ include "api-observability-rollout.fullname" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: Helm
{{- end }}

{{- define "api-observability-rollout.analysisName" -}}
{{- printf "%s-%s" (include "api-observability-rollout.fullname" .) .Values.analysis.nameSuffix -}}
{{- end }}
