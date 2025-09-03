# Create namespace
resource "kubernetes_namespace" "ai_interviewer" {
  depends_on = [null_resource.minikube_setup]

  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/name"    = "ai-interviewer"
      "app.kubernetes.io/part-of" = "ai-interviewer-platform"
    }
  }
}