package k8svalidation

deny contains msg if {
	resource := input[_]
	resource.kind != "Namespace"
	resource.kind != "CustomResourceDefinition"
	not resource.metadata.namespace
	msg := sprintf("%s/%s: namespace must be set", [resource.kind, resource.metadata.name])
}

deny contains msg if {
	resource := input[_]
	resource.kind != "Namespace"
	resource.kind != "CustomResourceDefinition"
	resource.metadata.namespace != "seedtest"
	msg := sprintf("%s/%s: namespace must be seedtest", [resource.kind, resource.metadata.name])
}
