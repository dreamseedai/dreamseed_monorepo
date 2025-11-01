package k8svalidation

deny contains msg if {
	resource := input[_]
	resource.kind == "Service"
	resource.spec.type
	resource.spec.type != "ClusterIP"
	msg := sprintf("Service/%s: type must be ClusterIP", [resource.metadata.name])
}
