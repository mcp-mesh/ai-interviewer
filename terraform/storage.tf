# MinIO Object Storage
resource "kubernetes_deployment" "minio" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  metadata {
    name      = "ai-interviewer-minio"
    namespace = var.namespace
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "ai-interviewer-minio"
      }
    }

    template {
      metadata {
        labels = {
          app = "ai-interviewer-minio"
        }
      }

      spec {
        container {
          name  = "minio"
          image = "minio/minio:RELEASE.2023-09-04T19-57-37Z"

          command = ["minio", "server", "/data", "--console-address", ":9001"]

          env {
            name  = "MINIO_ROOT_USER"
            value = "minioadmin"
          }

          env {
            name  = "MINIO_ROOT_PASSWORD"
            value = "minioadmin"
          }

          port {
            name           = "api"
            container_port = 9000
          }

          port {
            name           = "console"
            container_port = 9001
          }

          volume_mount {
            name       = "minio-data"
            mount_path = "/data"
          }

          resources {
            requests = {
              memory = "256Mi"
              cpu    = "250m"
            }
            limits = {
              memory = "512Mi"
              cpu    = "500m"
            }
          }

          liveness_probe {
            http_get {
              path = "/minio/health/live"
              port = 9000
            }
            initial_delay_seconds = 30
            period_seconds        = 30
          }
        }

        volume {
          name = "minio-data"
          empty_dir {}
        }
      }
    }
  }
}

resource "kubernetes_service" "minio" {
  depends_on = [kubernetes_deployment.minio]

  metadata {
    name      = "ai-interviewer-minio"
    namespace = var.namespace
  }

  spec {
    selector = {
      app = "ai-interviewer-minio"
    }

    port {
      name        = "api"
      port        = 9000
      target_port = 9000
    }

    port {
      name        = "console"
      port        = 9001
      target_port = 9001
    }

    type = "ClusterIP"
  }
}