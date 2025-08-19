# PostgreSQL Database
resource "kubernetes_deployment" "postgres" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  metadata {
    name      = "ai-interviewer-postgres"
    namespace = var.namespace
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "ai-interviewer-postgres"
      }
    }

    template {
      metadata {
        labels = {
          app = "ai-interviewer-postgres"
        }
      }

      spec {
        container {
          name  = "postgres"
          image = "postgres:15"

          env {
            name  = "POSTGRES_DB"
            value = "ai_interviewer"
          }

          env {
            name  = "POSTGRES_USER"
            value = "ai_user"
          }

          env {
            name  = "POSTGRES_PASSWORD"
            value = "ai_password"
          }

          port {
            container_port = 5432
          }

          volume_mount {
            name       = "postgres-data"
            mount_path = "/var/lib/postgresql/data"
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
        }

        volume {
          name = "postgres-data"
          empty_dir {}
        }
      }
    }
  }
}

resource "kubernetes_service" "postgres" {
  depends_on = [kubernetes_deployment.postgres]

  metadata {
    name      = "ai-interviewer-postgres"
    namespace = var.namespace
  }

  spec {
    selector = {
      app = "ai-interviewer-postgres"
    }

    port {
      port        = 5432
      target_port = 5432
    }

    type = "ClusterIP"
  }
}

# Redis Cache
resource "kubernetes_deployment" "redis" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  metadata {
    name      = "ai-interviewer-redis"
    namespace = var.namespace
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "ai-interviewer-redis"
      }
    }

    template {
      metadata {
        labels = {
          app = "ai-interviewer-redis"
        }
      }

      spec {
        container {
          name  = "redis"
          image = "redis:7-alpine"

          port {
            container_port = 6379
          }

          resources {
            requests = {
              memory = "128Mi"
              cpu    = "100m"
            }
            limits = {
              memory = "256Mi"
              cpu    = "200m"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "redis" {
  depends_on = [kubernetes_deployment.redis]

  metadata {
    name      = "ai-interviewer-redis"
    namespace = var.namespace
  }

  spec {
    selector = {
      app = "ai-interviewer-redis"
    }

    port {
      port        = 6379
      target_port = 6379
    }

    type = "ClusterIP"
  }
}