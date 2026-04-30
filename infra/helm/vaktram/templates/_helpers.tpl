{{/* Shared helpers for the Vaktram chart. */}}

{{- define "vaktram.fullname" -}}
{{- printf "%s-%s" .Release.Name .Component | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "vaktram.image" -}}
{{- printf "%s/%s:%s" .Values.global.imageRegistry .Image .Values.global.imageTag -}}
{{- end -}}
