package k8svalidation

# Require readinessProbe and livenessProbe for all containers in Deployments

deny contains msg if {
	resource := input[_]
	resource.kind == "Deployment"
	container := resource.spec.template.spec.containers[_]
	not container.readinessProbe
	msg := sprintf("Deployment/%s: container %s missing readinessProbe", [resource.metadata.name, container.name])
}

deny contains msg if {
	resource := input[_]
	resource.kind == "Deployment"
	container := resource.spec.template.spec.containers[_]
	not container.livenessProbe
	msg := sprintf("Deployment/%s: container %s missing livenessProbe", [resource.metadata.name, container.name])
}
