package main

# Template: allow only these image registries. Copy to active policy folder and set your org's registries.
default allow := false

allowed_registries := {
  "registry.k8s.io",
  "gcr.io/your-project",
  "ghcr.io/your-org",
}

deny[msg] {
  startswith(image(), "")
  not registry_allowed()
  msg := sprintf("Image registry not allowed: %s", [image()])
}

registry_allowed() {
  some reg
  reg := allowed_registries[_]
  startswith(image(), reg)
}

image() = img {
  # Supports Pod-specable resources (Deployment, CronJob, etc.)
  is_pod_specable(input)
  c := input.spec.template.spec.containers[_]
  img := c.image
} else = img {
  # Pod
  input.kind == "Pod"
  c := input.spec.containers[_]
  img := c.image
}

is_pod_specable(obj) {
  kinds := {"Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"}
  kinds[obj.kind]
}
