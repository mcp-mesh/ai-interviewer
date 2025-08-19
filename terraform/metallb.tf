# Install MetalLB using Helm
resource "helm_release" "metallb" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  name       = "metallb"
  repository = "https://metallb.github.io/metallb"
  chart      = "metallb"
  namespace  = "metallb-system"
  version    = "0.14.5"

  create_namespace = true

  # Wait for MetalLB to be ready before configuring
  wait = true
}

# Wait for MetalLB controller to be ready
resource "null_resource" "wait_for_metallb" {
  depends_on = [helm_release.metallb]

  provisioner "local-exec" {
    command = "kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=controller -n metallb-system --timeout=300s"
  }
}

# MetalLB IP Address Pool
resource "kubectl_manifest" "metallb_ippool" {
  depends_on = [null_resource.wait_for_metallb]

  yaml_body = yamlencode({
    apiVersion = "metallb.io/v1beta1"
    kind       = "IPAddressPool"
    metadata = {
      name      = "default-pool"
      namespace = "metallb-system"
    }
    spec = {
      addresses = [var.metallb_ip_range]
    }
  })
}

# MetalLB L2 Advertisement
resource "kubectl_manifest" "metallb_l2_advertisement" {
  depends_on = [kubectl_manifest.metallb_ippool]

  yaml_body = yamlencode({
    apiVersion = "metallb.io/v1beta1"
    kind       = "L2Advertisement"
    metadata = {
      name      = "default-l2-advertisement"
      namespace = "metallb-system"
    }
    spec = {
      ipAddressPools = ["default-pool"]
    }
  })
}