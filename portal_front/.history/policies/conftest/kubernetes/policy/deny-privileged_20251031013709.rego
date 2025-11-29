package kubernetes.admission

deny contains msg if {
	input.kind == "Pod"
	some i
	c := input.spec.containers[i]
	c.securityContext.privileged == true
	msg := sprintf("privileged container not allowed: %s", [c.name])
}

deny contains msg if {
	input.kind == "Deployment"
	some i
	c := input.spec.template.spec.containers[i]
	c.securityContext.privileged == true
	msg := sprintf("privileged container not allowed: %s", [c.name])
}
