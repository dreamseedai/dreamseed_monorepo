package kubernetes.admission

# Enforce runAsNonRoot at pod template level (Deployment)
deny contains msg if {
	input.kind == "Deployment"
	not input.spec.template.spec.securityContext.runAsNonRoot
	msg := "pod template securityContext.runAsNonRoot must be true"
}

# Enforce seccompProfile RuntimeDefault at pod template level
deny contains msg if {
	input.kind == "Deployment"
	sc := input.spec.template.spec.securityContext
	not sc.seccompProfile
	msg := "pod template securityContext.seccompProfile must be set"
}

deny contains msg if {
	input.kind == "Deployment"
	sc := input.spec.template.spec.securityContext
	sc.seccompProfile.type != "RuntimeDefault"
	msg := sprintf("seccompProfile.type must be RuntimeDefault (got %v)", [sc.seccompProfile.type])
}

# Disallow privilege escalation on all containers
deny contains msg if {
	input.kind == "Deployment"
	some i
	c := input.spec.template.spec.containers[i]
	not c.securityContext
	msg := sprintf("container %s missing securityContext", [c.name])
}

deny contains msg if {
	input.kind == "Deployment"
	some i
	c := input.spec.template.spec.containers[i]
	not c.securityContext.allowPrivilegeEscalation
	msg := sprintf("container %s must set allowPrivilegeEscalation: false", [c.name])
}

deny contains msg if {
	input.kind == "Deployment"
	some i
	c := input.spec.template.spec.containers[i]
	c.securityContext.allowPrivilegeEscalation != false
	msg := sprintf("container %s must set allowPrivilegeEscalation: false", [c.name])
}
