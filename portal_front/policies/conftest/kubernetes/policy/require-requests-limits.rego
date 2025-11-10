package kubernetes.admission

deny contains msg if {
	input.kind == "Deployment"
	some i
	c := input.spec.template.spec.containers[i]
	not c.resources.requests.cpu
	msg := sprintf("container %s missing resources.requests.cpu", [c.name])
}

deny contains msg if {
	input.kind == "Deployment"
	some i
	c := input.spec.template.spec.containers[i]
	not c.resources.limits.cpu
	msg := sprintf("container %s missing resources.limits.cpu", [c.name])
}
