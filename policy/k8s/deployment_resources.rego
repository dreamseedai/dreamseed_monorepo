package k8svalidation

has_field(obj, field) if {
	obj[field]
}

deny contains msg if {
	resource := input[_]
	resource.kind == "Deployment"
	container := resource.spec.template.spec.containers[_]
	not has_field(container, "resources")
	msg := sprintf("Deployment/%s: container %s missing resources", [resource.metadata.name, container.name])
}

deny contains msg if {
	resource := input[_]
	resource.kind == "Deployment"
	container := resource.spec.template.spec.containers[_]
	not container.resources.requests
	msg := sprintf("Deployment/%s: container %s missing resource requests", [resource.metadata.name, container.name])
}

deny contains msg if {
	resource := input[_]
	resource.kind == "Deployment"
	container := resource.spec.template.spec.containers[_]
	not container.resources.limits
	msg := sprintf("Deployment/%s: container %s missing resource limits", [resource.metadata.name, container.name])
}
