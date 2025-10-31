package k8svalidation

deny contains msg if {
	resource := input[_]
	resource.apiVersion == "monitoring.coreos.com/v1"
	resource.kind == "ServiceMonitor"
	not resource.metadata.labels.release
	msg := sprintf("ServiceMonitor/%s: missing 'release' label", [resource.metadata.name])
}
