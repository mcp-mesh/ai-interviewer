# Backend Deployment
resource "kubernetes_deployment" "backend" {
  depends_on = [
    kubernetes_service.postgres,
    kubernetes_service.redis,
    kubernetes_service.minio
  ]

  metadata {
    name      = "ai-interviewer-backend"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/name"    = "ai-interviewer-backend"
      "app.kubernetes.io/part-of" = "ai-interviewer"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        "app.kubernetes.io/name" = "ai-interviewer-backend"
      }
    }

    template {
      metadata {
        labels = {
          "app.kubernetes.io/name" = "ai-interviewer-backend"
        }
      }

      spec {
        container {
          name              = "backend"
          image             = var.docker_images.backend
          image_pull_policy = "Never"

          port {
            name           = "http"
            container_port = 8080
          }

          # Database connection from secrets
          env {
            name = "POSTGRES_USER"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.database_credentials.metadata[0].name
                key  = "POSTGRES_USER"
              }
            }
          }

          env {
            name = "POSTGRES_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.database_credentials.metadata[0].name
                key  = "POSTGRES_PASSWORD"
              }
            }
          }

          env {
            name = "POSTGRES_DB"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.database_credentials.metadata[0].name
                key  = "POSTGRES_DB"
              }
            }
          }

          # Derived DATABASE_URL
          env {
            name  = "DATABASE_URL"
            value = "postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@ai-interviewer-postgres:5432/$(POSTGRES_DB)"
          }

          env {
            name  = "REDIS_URL"
            value = "redis://ai-interviewer-redis:6379"
          }

          # MinIO credentials from secrets
          env {
            name = "MINIO_ACCESS_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.database_credentials.metadata[0].name
                key  = "MINIO_ACCESS_KEY"
              }
            }
          }

          env {
            name = "MINIO_SECRET_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.database_credentials.metadata[0].name
                key  = "MINIO_SECRET_KEY"
              }
            }
          }

          env {
            name  = "MINIO_ENDPOINT"
            value = "ai-interviewer-minio:9000"
          }

          # FastAPI application config
          env {
            name = "CLAUDE_API_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.api_keys.metadata[0].name
                key  = "ANTHROPIC_API_KEY"
              }
            }
          }

          env {
            name  = "DEV_MODE"
            value = var.enable_debug ? "true" : "false"
          }

          # MCP Mesh integration
          env {
            name  = "MCP_MESH_ENABLED"
            value = "true"
          }

          env {
            name  = "MCP_MESH_REGISTRY_URL"
            value = "http://ai-interviewer-registry:8000"
          }

          env {
            name  = "MCP_MESH_LOG_LEVEL"
            value = "DEBUG"
          }

          env {
            name  = "MCP_MESH_DEBUG_MODE"
            value = "true"
          }

          env {
            name  = "MCP_MESH_HTTP_PORT"
            value = "8080"
          }

          env {
            name  = "MCP_MESH_API_NAME"
            value = "interview-api"
          }

          # Enable distributed tracing for API service
          env {
            name  = "MCP_MESH_DISTRIBUTED_TRACING_ENABLED"
            value = "true"
          }

          env {
            name  = "MCP_MESH_TELEMETRY_ENABLED"
            value = "true"
          }

          env {
            name  = "MCP_MESH_REDIS_TRACE_PUBLISHING"
            value = "true"
          }

          # MinIO configuration (additional)
          env {
            name  = "MINIO_HOST"
            value = "ai-interviewer-minio:9000"
          }

          env {
            name  = "BUCKET_NAME"
            value = "ai-interviewer-uploads"
          }

          # Legacy MCP Registry URL (for compatibility)
          env {
            name  = "MCP_REGISTRY_URL"
            value = "http://ai-interviewer-registry:8000"
          }

          # API Keys from secrets
          env {
            name = "ANTHROPIC_API_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.api_keys.metadata[0].name
                key  = "ANTHROPIC_API_KEY"
              }
            }
          }

          env {
            name = "OPENAI_API_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.api_keys.metadata[0].name
                key  = "OPENAI_API_KEY"
              }
            }
          }

          # reCAPTCHA Keys from secrets
          env {
            name = "RECAPTCHA_SITE_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.recaptcha_keys.metadata[0].name
                key  = "RECAPTCHA_SITE_KEY"
              }
            }
          }

          env {
            name = "RECAPTCHA_SECRET_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.recaptcha_keys.metadata[0].name
                key  = "RECAPTCHA_SECRET_KEY"
              }
            }
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
              path = "/health"
              port = 8080
            }
            initial_delay_seconds = 30
            period_seconds        = 30
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = 8080
            }
            initial_delay_seconds = 5
            period_seconds        = 5
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "backend" {
  depends_on = [kubernetes_deployment.backend]

  metadata {
    name      = "ai-interviewer-backend"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/name" = "ai-interviewer-backend"
    }
  }

  spec {
    selector = {
      "app.kubernetes.io/name" = "ai-interviewer-backend"
    }

    port {
      name        = "http"
      port        = 8080
      target_port = 8080
    }

    type = "ClusterIP"
  }
}