package main

deny contains msg if {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not has_memory_requests_limits(container)
  msg := sprintf("Deployment %s container %s must set resources.requests.memory and resources.limits.memory", [input.metadata.name, container.name])
}

has_memory_requests_limits(c) if {
  c.resources.requests.memory
  c.resources.limits.memory
}
