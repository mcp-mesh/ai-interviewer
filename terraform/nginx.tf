# Nginx Gateway Deployment
resource "kubernetes_deployment" "nginx_gateway" {
  depends_on = [
    kubernetes_config_map.nginx_config,
    kubernetes_config_map.nginx_lua_scripts,
    kubernetes_secret.nginx_ssl,
    kubernetes_secret.oauth_config,
    kubernetes_service.redis
  ]

  metadata {
    name      = "ai-interviewer-nginx-gateway"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/name"      = "ai-interviewer-nginx-gateway"
      "app.kubernetes.io/component" = "gateway"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        "app.kubernetes.io/name"      = "ai-interviewer-nginx-gateway"
        "app.kubernetes.io/component" = "gateway"
      }
    }

    template {
      metadata {
        labels = {
          "app.kubernetes.io/name"      = "ai-interviewer-nginx-gateway"
          "app.kubernetes.io/component" = "gateway"
        }
      }

      spec {
        init_container {
          name  = "create-temp-dirs"
          image = "busybox:1.35"
          command = [
            "sh", "-c",
            "mkdir -p /tmp/nginx/client_body_temp /tmp/nginx/proxy_temp /tmp/nginx/fastcgi_temp /tmp/nginx/uwsgi_temp /tmp/nginx/scgi_temp && chmod -R 777 /tmp/nginx"
          ]
          volume_mount {
            name       = "nginx-temp"
            mount_path = "/tmp/nginx"
          }
        }

        container {
          name              = "nginx"
          image             = var.docker_images.frontend
          image_pull_policy = "Never"

          port {
            name           = "http"
            container_port = 80
          }

          port {
            name           = "https"
            container_port = 443
          }

          env_from {
            secret_ref {
              name = "oauth-credentials"
            }
          }

          env {
            name  = "DEV_MODE"
            value = "false"
          }

          volume_mount {
            name       = "nginx-config"
            mount_path = "/usr/local/openresty/nginx/conf/nginx.conf"
            sub_path   = "nginx-k8s.conf"
          }

          volume_mount {
            name       = "nginx-lua-scripts"
            mount_path = "/etc/nginx/lua"
          }

          volume_mount {
            name       = "nginx-ssl-certs"
            mount_path = "/etc/ssl/certs"
            read_only  = true
          }

          volume_mount {
            name       = "nginx-ssl-private"
            mount_path = "/etc/ssl/private"
            read_only  = true
          }


          volume_mount {
            name       = "nginx-temp"
            mount_path = "/tmp/nginx"
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
              port = 80
            }
            initial_delay_seconds = 30
            period_seconds        = 30
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = 80
            }
            initial_delay_seconds = 5
            period_seconds        = 5
          }
        }


        volume {
          name = "nginx-config"
          config_map {
            name = kubernetes_config_map.nginx_config.metadata[0].name
          }
        }

        volume {
          name = "nginx-lua-scripts"
          config_map {
            name = "nginx-lua-scripts"
          }
        }

        volume {
          name = "nginx-ssl-certs"
          secret {
            secret_name = "interviews-ink-tls"
            items {
              key  = "tls.crt"
              path = "server.crt"
            }
          }
        }

        volume {
          name = "nginx-ssl-private"
          secret {
            secret_name = "interviews-ink-tls"
            items {
              key  = "tls.key"
              path = "server.key"
            }
          }
        }


        volume {
          name = "nginx-temp"
          empty_dir {}
        }
      }
    }
  }
}

# Nginx Gateway Service with LoadBalancer
resource "kubernetes_service" "nginx_gateway" {
  depends_on = [kubernetes_deployment.nginx_gateway]

  metadata {
    name      = "ai-interviewer-nginx-gateway"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/name"      = "ai-interviewer-nginx-gateway"
      "app.kubernetes.io/component" = "gateway"
    }
    annotations = {
      "metallb.universe.tf/address-pool" = "default"
    }
  }

  spec {
    selector = {
      "app.kubernetes.io/name"      = "ai-interviewer-nginx-gateway"
      "app.kubernetes.io/component" = "gateway"
    }

    port {
      name        = "http"
      port        = 80
      target_port = 80
      protocol    = "TCP"
    }

    port {
      name        = "https"
      port        = 443
      target_port = 443
      protocol    = "TCP"
    }

    type                    = "LoadBalancer"
    external_traffic_policy = "Cluster"
  }
}