package k8svalidation

# Require a standard app label on common resource kinds used here

has_label(resource, key) if {
	resource.metadata.labels[key]
}

kind_in(resource, kinds) if {
	some i
	resource.kind == kinds[i]
}

deny contains msg if {
	resource := input[_]
	kinds := ["Deployment", "Service", "NetworkPolicy", "CronJob"]
	kind_in(resource, kinds)
	not has_label(resource, "app")
	msg := sprintf("%s/%s: missing required label 'app'", [resource.kind, resource.metadata.name])
}
