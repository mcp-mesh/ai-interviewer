# MCP Registry Service
resource "kubernetes_deployment" "registry" {
  depends_on = [
    kubernetes_service.postgres,
    kubernetes_service.redis
  ]

  metadata {
    name      = "ai-interviewer-registry"
    namespace = var.namespace
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "ai-interviewer-registry"
      }
    }

    template {
      metadata {
        labels = {
          app = "ai-interviewer-registry"
        }
      }

      spec {
        container {
          name  = "registry"
          image = "mcpmesh/registry:0.5.3"

          port {
            container_port = 8000
          }

          # Registry configuration
          env {
            name  = "HOST"
            value = "0.0.0.0"
          }

          env {
            name  = "PORT"
            value = "8000"
          }

          env {
            name  = "MCP_MESH_LOG_LEVEL"
            value = "INFO"
          }

          env {
            name  = "MCP_MESH_DEBUG_MODE"
            value = "false"
          }

          # PostgreSQL connection
          env {
            name  = "DATABASE_URL"
            value = "postgres://ai_user:ai_password@ai-interviewer-postgres:5432/ai_interviewer?sslmode=disable"
          }

          # Redis connection for session storage and coordination
          env {
            name  = "REDIS_URL"
            value = "redis://ai-interviewer-redis:6379"
          }

          # Enable telemetry and tracing
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

          # OTLP tracing to Tempo
          env {
            name  = "TRACE_EXPORTER_TYPE"
            value = "otlp"
          }

          env {
            name  = "TELEMETRY_ENDPOINT"
            value = "ai-interviewer-tempo:4317"
          }

          env {
            name  = "TELEMETRY_PROTOCOL"
            value = "grpc"
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

resource "kubernetes_service" "registry" {
  depends_on = [kubernetes_deployment.registry]

  metadata {
    name      = "ai-interviewer-registry"
    namespace = var.namespace
  }

  spec {
    selector = {
      app = "ai-interviewer-registry"
    }

    port {
      port        = 8000
      target_port = 8000
    }

    type = "ClusterIP"
  }
}

# PDF Extractor Agent
resource "kubernetes_deployment" "pdf_extractor" {
  depends_on = [
    kubernetes_service.redis,
    kubernetes_service.minio
  ]

  metadata {
    name      = "ai-interviewer-pdf-extractor"
    namespace = var.namespace
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "ai-interviewer-pdf-extractor"
      }
    }

    template {
      metadata {
        labels = {
          app = "ai-interviewer-pdf-extractor"
        }
      }

      spec {
        container {
          name              = "pdf-extractor"
          image             = var.docker_images.pdf_extractor
          image_pull_policy = "Never"

          port {
            container_port = 8090
          }

          # Agent configuration
          env {
            name  = "AGENT_NAME"
            value = "pdf-extractor"
          }
          
          env {
            name  = "MCP_MESH_HTTP_PORT"
            value = "8090"
          }
          
          env {
            name  = "LOG_LEVEL"
            value = var.enable_debug ? "DEBUG" : "INFO"
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

          # Distributed tracing
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
          
          env {
            name  = "REDIS_URL"
            value = "redis://ai-interviewer-redis:6379"
          }

          # Processing limits
          env {
            name  = "PDF_MAX_FILE_SIZE_MB"
            value = "50"
          }
          
          env {
            name  = "PDF_MAX_PAGES"
            value = "100"
          }
          
          env {
            name  = "PDF_TIMEOUT_SECONDS"
            value = "300"
          }
          
          env {
            name  = "PDF_MAX_IMAGE_COUNT"
            value = "20"
          }
          
          env {
            name  = "PDF_MAX_IMAGE_SIZE_MB"
            value = "10"
          }

          # Security settings
          env {
            name  = "PDF_ALLOW_ENCRYPTED"
            value = "false"
          }
          
          env {
            name  = "PDF_SANITIZE_METADATA"
            value = "true"
          }
          
          env {
            name  = "PDF_VALIDATE_HEADERS"
            value = "true"
          }

          # Extraction configuration
          env {
            name  = "PDF_PRESERVE_FORMATTING"
            value = "true"
          }
          
          env {
            name  = "PDF_EXTRACT_IMAGES"
            value = "true"
          }
          
          env {
            name  = "PDF_EXTRACT_TABLES"
            value = "true"
          }
          
          env {
            name  = "PDF_IMAGE_FORMAT"
            value = "PNG"
          }
          
          env {
            name  = "PDF_TABLE_FORMAT"
            value = "json"
          }

          # Cache configuration
          env {
            name  = "PDF_CACHE_ENABLED"
            value = "true"
          }
          
          env {
            name  = "PDF_CACHE_TTL_SECONDS"
            value = "3600"
          }
          
          env {
            name  = "PDF_TEMP_DIR"
            value = "/app/temp"
          }
          
          env {
            name  = "PDF_OUTPUT_DIR"
            value = "/app/output"
          }

          # Performance
          env {
            name  = "METRICS_ENABLED"
            value = "true"
          }

          # S3/MinIO configuration
          env {
            name  = "S3_ENDPOINT"
            value = "http://ai-interviewer-minio:9000"
          }
          
          env {
            name = "S3_ACCESS_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.database_credentials.metadata[0].name
                key  = "MINIO_ACCESS_KEY"
              }
            }
          }
          
          env {
            name = "S3_SECRET_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.database_credentials.metadata[0].name
                key  = "MINIO_SECRET_KEY"
              }
            }
          }
          
          env {
            name  = "S3_BUCKET_NAME"
            value = "ai-interviewer-uploads"
          }
          
          env {
            name  = "S3_REGION"
            value = "us-east-1"
          }

          # Volume mounts for PDF processing
          volume_mount {
            name       = "pdf-temp"
            mount_path = "/app/temp"
          }
          
          volume_mount {
            name       = "pdf-output"
            mount_path = "/app/output"
          }
          
          volume_mount {
            name       = "pdf-logs"
            mount_path = "/app/logs"
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

        # Volumes for PDF processing
        volume {
          name = "pdf-temp"
          empty_dir {}
        }

        volume {
          name = "pdf-output"
          empty_dir {}
        }

        volume {
          name = "pdf-logs"
          empty_dir {}
        }
      }
    }
  }
}

# Interview Agent
resource "kubernetes_deployment" "interview_agent" {
  depends_on = [
    kubernetes_service.redis
  ]

  metadata {
    name      = "ai-interviewer-interview-agent"
    namespace = var.namespace
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "ai-interviewer-interview-agent"
      }
    }

    template {
      metadata {
        labels = {
          app = "ai-interviewer-interview-agent"
        }
      }

      spec {
        container {
          name              = "interview-agent"
          image             = var.docker_images.interview_agent
          image_pull_policy = "Never"

          port {
            container_port = 8090
          }

          # Agent configuration
          env {
            name  = "AGENT_NAME"
            value = "interview-agent"
          }
          
          env {
            name  = "MCP_MESH_HTTP_PORT"
            value = "8090"
          }
          
          env {
            name  = "LOG_LEVEL"
            value = var.enable_debug ? "DEBUG" : "INFO"
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

          # Enable distributed tracing for MCP agent
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
          
          env {
            name  = "REDIS_URL"
            value = "redis://ai-interviewer-redis:6379"
          }

          # Redis configuration for session management
          env {
            name  = "REDIS_HOST"
            value = "ai-interviewer-redis"
          }
          
          env {
            name  = "REDIS_PORT"
            value = "6379"
          }
          
          env {
            name  = "REDIS_DB"
            value = "0"
          }
          
          env {
            name  = "REDIS_PASSWORD"
            value = ""
          }

          # Legacy MCP Registry URL (for compatibility)
          env {
            name  = "MCP_REGISTRY_URL"
            value = "http://ai-interviewer-registry:8000"
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
      }
    }
  }
}

# LLM Agent (Claude)
resource "kubernetes_deployment" "llm_agent" {
  depends_on = [
    kubernetes_service.redis
  ]

  metadata {
    name      = "ai-interviewer-llm-agent"
    namespace = var.namespace
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "ai-interviewer-llm-agent"
      }
    }

    template {
      metadata {
        labels = {
          app = "ai-interviewer-llm-agent"
        }
      }

      spec {
        container {
          name              = "llm-agent"
          image             = var.docker_images.llm_agent
          image_pull_policy = "Never"

          port {
            container_port = 8090
          }

          # Agent configuration
          env {
            name  = "AGENT_NAME"
            value = "llm-claude-agent"
          }
          
          env {
            name  = "MCP_MESH_HTTP_PORT"
            value = "8090"
          }
          
          env {
            name  = "LOG_LEVEL"
            value = var.enable_debug ? "DEBUG" : "INFO"
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

          # Enable distributed tracing for MCP agent
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
          
          env {
            name  = "REDIS_URL"
            value = "redis://ai-interviewer-redis:6379"
          }

          # Claude API configuration
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
            name  = "CLAUDE_MODEL"
            value = "claude-3-5-sonnet-20241022"
          }
          
          env {
            name  = "CLAUDE_MAX_TOKENS"
            value = "4000"
          }
          
          env {
            name  = "CLAUDE_TEMPERATURE"
            value = "0.7"
          }

          # Performance and reliability
          env {
            name  = "RETRY_ATTEMPTS"
            value = "3"
          }
          
          env {
            name  = "TIMEOUT_SECONDS"
            value = "120"
          }

          # Legacy MCP Registry URL (for compatibility)
          env {
            name  = "MCP_REGISTRY_URL"
            value = "http://ai-interviewer-registry:8000"
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
      }
    }
  }
}

# OpenAI LLM Agent
resource "kubernetes_deployment" "openai_llm_agent" {
  depends_on = [
    kubernetes_service.redis
  ]

  metadata {
    name      = "ai-interviewer-openai-llm-agent"
    namespace = var.namespace
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "ai-interviewer-openai-llm-agent"
      }
    }

    template {
      metadata {
        labels = {
          app = "ai-interviewer-openai-llm-agent"
        }
      }

      spec {
        container {
          name              = "openai-llm-agent"
          image             = var.docker_images.openai_llm_agent
          image_pull_policy = "Never"

          port {
            container_port = 8090
          }

          # Agent configuration
          env {
            name  = "AGENT_NAME"
            value = "llm-openai-agent"
          }
          
          env {
            name  = "MCP_MESH_HTTP_PORT"
            value = "8090"
          }
          
          env {
            name  = "LOG_LEVEL"
            value = var.enable_debug ? "DEBUG" : "INFO"
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

          # Enable distributed tracing for MCP agent
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
          
          env {
            name  = "REDIS_URL"
            value = "redis://ai-interviewer-redis:6379"
          }

          # OpenAI API configuration
          env {
            name = "OPENAI_API_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.api_keys.metadata[0].name
                key  = "OPENAI_API_KEY"
              }
            }
          }
          
          env {
            name  = "OPENAI_MODEL"
            value = "gpt-4o"
          }
          
          env {
            name  = "OPENAI_MAX_TOKENS"
            value = "4000"
          }
          
          env {
            name  = "OPENAI_TEMPERATURE"
            value = "0.7"
          }

          # Performance and reliability
          env {
            name  = "RETRY_ATTEMPTS"
            value = "3"
          }
          
          env {
            name  = "TIMEOUT_SECONDS"
            value = "120"
          }

          # Legacy MCP Registry URL (for compatibility)
          env {
            name  = "MCP_REGISTRY_URL"
            value = "http://ai-interviewer-registry:8000"
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
      }
    }
  }
}