package k8svalidation

array_contains(arr, v) if {
	some i
	arr[i] == v
}

deny contains msg if {
	resource := input[_]
	resource.kind == "NetworkPolicy"
	not array_contains(resource.spec.policyTypes, "Ingress")
	msg := sprintf("NetworkPolicy/%s: policyTypes must include Ingress", [resource.metadata.name])
}
