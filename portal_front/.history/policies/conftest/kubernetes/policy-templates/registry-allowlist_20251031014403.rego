package main

# Template: allow only these image registries. Copy to active policy folder and set your org's registries.
allowed_registries := {
  "registry.k8s.io",
  "gcr.io/your-project",
  "ghcr.io/your-org",
}

deny contains msg if {
  img := image()
  not registry_allowed(img)
  msg := sprintf("Image registry not allowed: %s", [img])
}

registry_allowed(img) if {
  some reg
  reg := allowed_registries[_]
  startswith(img, reg)
}

image() = img if {
  # Supports Pod-specable resources (Deployment, CronJob, etc.)
  is_pod_specable(input)
  c := input.spec.template.spec.containers[_]
  img := c.image
} else = img if {
  # Pod
  input.kind == "Pod"
  c := input.spec.containers[_]
  img := c.image
}

is_pod_specable(obj) if {
  kinds := {"Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"}
  kinds[obj.kind]
}
