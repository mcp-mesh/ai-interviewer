# Tempo (Distributed Tracing)
resource "kubernetes_deployment" "tempo" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  metadata {
    name      = "ai-interviewer-tempo"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/name"      = "ai-interviewer-tempo"
      "app.kubernetes.io/component" = "observability"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        "app.kubernetes.io/name"      = "ai-interviewer-tempo"
        "app.kubernetes.io/component" = "observability"
      }
    }

    template {
      metadata {
        labels = {
          "app.kubernetes.io/name"      = "ai-interviewer-tempo"
          "app.kubernetes.io/component" = "observability"
        }
      }

      spec {
        container {
          name  = "tempo"
          image = "grafana/tempo:2.2.4"

          args = [
            "-config.file=/etc/tempo/tempo.yaml",
            "-mem-ballast-size-mbs=1024"
          ]

          port {
            name           = "tempo"
            container_port = 3200
          }

          port {
            name           = "otlp-grpc"
            container_port = 4317
          }

          port {
            name           = "otlp-http"
            container_port = 4318
          }

          volume_mount {
            name       = "tempo-config"
            mount_path = "/etc/tempo"
          }

          volume_mount {
            name       = "tempo-data"
            mount_path = "/var/tempo"
          }

          resources {
            requests = {
              memory = "512Mi"
              cpu    = "250m"
            }
            limits = {
              memory = "1Gi"
              cpu    = "500m"
            }
          }
        }

        volume {
          name = "tempo-config"
          config_map {
            name = "ai-interviewer-tempo-config"
          }
        }

        volume {
          name = "tempo-data"
          empty_dir {}
        }
      }
    }
  }
}

resource "kubernetes_service" "tempo" {
  depends_on = [kubernetes_deployment.tempo]

  metadata {
    name      = "ai-interviewer-tempo"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/name"      = "ai-interviewer-tempo"
      "app.kubernetes.io/component" = "observability"
    }
  }

  spec {
    selector = {
      "app.kubernetes.io/name"      = "ai-interviewer-tempo"
      "app.kubernetes.io/component" = "observability"
    }

    port {
      name        = "tempo"
      port        = 3200
      target_port = 3200
    }

    port {
      name        = "otlp-grpc"
      port        = 4317
      target_port = 4317
    }

    port {
      name        = "otlp-http"
      port        = 4318
      target_port = 4318
    }

    type = "ClusterIP"
  }
}

# Tempo Configuration
resource "kubernetes_config_map" "tempo_config" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  metadata {
    name      = "ai-interviewer-tempo-config"
    namespace = var.namespace
  }

  data = {
    "tempo.yaml" = yamlencode({
      server = {
        http_listen_port = 3200
      }
      distributor = {
        receivers = {
          otlp = {
            protocols = {
              grpc = {
                endpoint = "0.0.0.0:4317"
              }
              http = {
                endpoint = "0.0.0.0:4318"
              }
            }
          }
        }
      }
      ingester = {
        trace_idle_period  = "10s"
        max_block_bytes    = 1048576
        max_block_duration = "5m"
      }
      compactor = {
        compaction = {
          compaction_window         = "1h"
          max_compaction_objects    = 1000000
          block_retention           = "1h"
          compacted_block_retention = "10m"
        }
      }
      storage = {
        trace = {
          backend = "local"
          local = {
            path = "/var/tempo/traces"
          }
        }
      }
    })
  }
}

# Grafana Deployment
resource "kubernetes_deployment" "grafana" {
  depends_on = [kubernetes_service.tempo]

  metadata {
    name      = "ai-interviewer-grafana"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/name"      = "ai-interviewer-grafana"
      "app.kubernetes.io/component" = "observability"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        "app.kubernetes.io/name"      = "ai-interviewer-grafana"
        "app.kubernetes.io/component" = "observability"
      }
    }

    template {
      metadata {
        labels = {
          "app.kubernetes.io/name"      = "ai-interviewer-grafana"
          "app.kubernetes.io/component" = "observability"
        }
      }

      spec {
        container {
          name  = "grafana"
          image = "grafana/grafana:11.4.0"

          port {
            name           = "http"
            container_port = 3000
          }

          env {
            name  = "GF_SECURITY_ADMIN_USER"
            value = "admin"
          }

          env {
            name  = "GF_SECURITY_ADMIN_PASSWORD"
            value = "admin"
          }

          env {
            name  = "GF_USERS_ALLOW_SIGN_UP"
            value = "false"
          }

          env {
            name  = "GF_FEATURE_TOGGLES_ENABLE"
            value = "traceqlEditor"
          }

          env {
            name  = "GF_SERVER_ROOT_URL"
            value = "/grafana/"
          }

          env {
            name  = "GF_SERVER_SERVE_FROM_SUB_PATH"
            value = "true"
          }

          volume_mount {
            name       = "grafana-config"
            mount_path = "/etc/grafana/grafana.ini"
            sub_path   = "grafana.ini"
          }

          volume_mount {
            name       = "grafana-datasources"
            mount_path = "/etc/grafana/provisioning/datasources"
          }

          volume_mount {
            name       = "grafana-dashboards-config"
            mount_path = "/etc/grafana/provisioning/dashboards"
          }

          volume_mount {
            name       = "grafana-dashboard"
            mount_path = "/var/lib/grafana/dashboards"
          }

          volume_mount {
            name       = "grafana-data"
            mount_path = "/var/lib/grafana"
          }

          resources {
            requests = {
              memory = "256Mi"
              cpu    = "100m"
            }
            limits = {
              memory = "512Mi"
              cpu    = "500m"
            }
          }

          liveness_probe {
            http_get {
              path = "/api/health"
              port = 3000
            }
            initial_delay_seconds = 30
            period_seconds        = 10
          }

          readiness_probe {
            http_get {
              path = "/api/health"
              port = 3000
            }
            initial_delay_seconds = 5
            period_seconds        = 5
          }
        }

        volume {
          name = "grafana-config"
          config_map {
            name = "ai-interviewer-grafana-config"
          }
        }

        volume {
          name = "grafana-datasources"
          config_map {
            name = "ai-interviewer-grafana-datasources"
          }
        }

        volume {
          name = "grafana-dashboards-config"
          config_map {
            name = "ai-interviewer-grafana-dashboards-config"
          }
        }

        volume {
          name = "grafana-dashboard"
          config_map {
            name = "ai-interviewer-grafana-dashboard"
          }
        }

        volume {
          name = "grafana-data"
          empty_dir {}
        }
      }
    }
  }
}

resource "kubernetes_service" "grafana" {
  depends_on = [kubernetes_deployment.grafana]

  metadata {
    name      = "ai-interviewer-grafana"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/name"      = "ai-interviewer-grafana"
      "app.kubernetes.io/component" = "observability"
    }
  }

  spec {
    selector = {
      "app.kubernetes.io/name"      = "ai-interviewer-grafana"
      "app.kubernetes.io/component" = "observability"
    }

    port {
      name        = "http"
      port        = 3000
      target_port = 3000
    }

    type = "ClusterIP"
  }
}

# Grafana Configuration ConfigMaps
resource "kubernetes_config_map" "grafana_config" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  metadata {
    name      = "ai-interviewer-grafana-config"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/name"      = "ai-interviewer-grafana"
      "app.kubernetes.io/component" = "observability"
    }
  }

  data = {
    "grafana.ini" = file("${path.module}/../k8s/base/observability/grafana-config-configmap.yaml")
  }
}

# Grafana Datasources ConfigMap
resource "kubernetes_config_map" "grafana_datasources" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  metadata {
    name      = "ai-interviewer-grafana-datasources"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/name"      = "ai-interviewer-grafana"
      "app.kubernetes.io/component" = "observability"
    }
  }

  data = {
    "datasources.yaml" = yamlencode({
      apiVersion = 1
      datasources = [
        {
          name      = "Tempo"
          type      = "tempo"
          access    = "proxy"
          url       = "http://ai-interviewer-tempo:3200"
          uid       = "tempo"
          isDefault = false
          editable  = true
        }
      ]
    })
  }
}

# Grafana Dashboards Config ConfigMap
resource "kubernetes_config_map" "grafana_dashboards_config" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  metadata {
    name      = "ai-interviewer-grafana-dashboards-config"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/name"      = "ai-interviewer-grafana"
      "app.kubernetes.io/component" = "observability"
    }
  }

  data = {
    "dashboards.yaml" = yamlencode({
      apiVersion = 1
      providers = [
        {
          name                  = "default"
          orgId                 = 1
          folder                = ""
          type                  = "file"
          disableDeletion       = false
          updateIntervalSeconds = 10
          allowUiUpdates        = true
          options = {
            path = "/var/lib/grafana/dashboards"
          }
        }
      ]
    })
  }
}

# Grafana Dashboard ConfigMap
resource "kubernetes_config_map" "grafana_dashboard" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  metadata {
    name      = "ai-interviewer-grafana-dashboard"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/name"      = "ai-interviewer-grafana"
      "app.kubernetes.io/component" = "observability"
    }
  }

  data = {
    "mcp-mesh-overview.json" = jsonencode({
      annotations = {
        list = [
          {
            builtIn = 1
            datasource = {
              type = "grafana"
              uid  = "-- Grafana --"
            }
            enable    = true
            hide      = true
            iconColor = "rgba(0, 211, 255, 1)"
            name      = "Annotations & Alerts"
            type      = "dashboard"
          }
        ]
      }
      editable             = true
      fiscalYearStartMonth = 0
      graphTooltip         = 0
      id                   = null
      links                = []
      liveNow              = false
      panels = [
        {
          id    = 1
          type  = "piechart"
          title = "MCP Mesh Distributed Tracing Overview"
          gridPos = {
            x = 0
            y = 0
            h = 8
            w = 24
          }
          fieldConfig = {
            defaults = {
              custom = {
                hideFrom = {
                  tooltip = false
                  viz     = false
                  legend  = false
                  vis     = false
                }
              }
              color = {
                mode = "palette-classic"
              }
              mappings = []
              unit     = "µs"
            }
            overrides = []
          }
          transformations = [
            {
              id = "groupBy"
              options = {
                fields = {
                  Duration = {
                    aggregations = [
                      "sum"
                    ]
                    operation = "aggregate"
                  }
                  Service = {
                    aggregations = []
                    operation    = "groupby"
                  }
                  nested = {
                    aggregations = []
                  }
                  traceDuration = {
                    aggregations = [
                      "max"
                    ]
                    operation = "aggregate"
                  }
                  traceID = {
                    aggregations = []
                    operation    = null
                  }
                  traceName = {
                    aggregations = []
                  }
                  traceService = {
                    aggregations = [
                      "count"
                    ]
                    operation = "groupby"
                  }
                }
              }
            }
          ]
          pluginVersion = "11.4.0"
          targets = [
            {
              datasource = {
                type = "tempo"
                uid  = "tempo"
              }
              limit     = 20
              query     = "{}"
              queryType = "traceql"
              refId     = "A"
              tableType = "traces"
            }
          ]
          datasource = {
            type = "tempo"
            uid  = "tempo"
          }
          options = {
            reduceOptions = {
              values = true
              calcs = [
                "lastNotNull"
              ]
              fields = "/.*/"
            }
            pieType = "pie"
            tooltip = {
              mode = "single"
              sort = "none"
            }
            legend = {
              showLegend  = true
              displayMode = "list"
              placement   = "bottom"
            }
            displayLabels = [
              "name"
            ]
          }
        },
        {
          id    = 2
          type  = "barchart"
          title = "Service Activity Summary"
          gridPos = {
            x = 0
            y = 8
            h = 8
            w = 24
          }
          fieldConfig = {
            defaults = {
              custom = {
                lineWidth      = 1
                fillOpacity    = 80
                gradientMode   = "none"
                axisPlacement  = "auto"
                axisLabel      = ""
                axisColorMode  = "text"
                axisBorderShow = false
                scaleDistribution = {
                  type = "linear"
                }
                axisCenteredZero = false
                hideFrom = {
                  tooltip = false
                  viz     = false
                  legend  = false
                  vis     = false
                }
                thresholdsStyle = {
                  mode = "off"
                }
                axisGridShow = true
              }
              color = {
                mode = "palette-classic"
              }
              mappings = []
              thresholds = {
                mode = "absolute"
                steps = [
                  {
                    color = "green"
                    value = null
                  },
                  {
                    color = "red"
                    value = 80
                  }
                ]
              }
            }
            overrides = []
          }
          transformations = [
            {
              id = "groupBy"
              options = {
                fields = {
                  Service = {
                    aggregations = []
                    operation    = "groupby"
                  }
                  traceName = {
                    aggregations = []
                    operation    = "groupby"
                  }
                  traceDuration = {
                    aggregations = [
                      "lastNotNull"
                    ]
                    operation = "aggregate"
                  }
                  traceService = {
                    aggregations = []
                    operation    = null
                  }
                  nested = {
                    aggregations = []
                    operation    = null
                  }
                }
              }
            }
          ]
          pluginVersion = "11.4.0"
          targets = [
            {
              datasource = {
                type = "tempo"
                uid  = "tempo"
              }
              query     = "{}"
              refId     = "A"
              queryType = "traceql"
              limit     = 20
              tableType = "traces"
            }
          ]
          datasource = {
            type = "tempo"
            uid  = "tempo"
          }
          options = {
            orientation        = "vertical"
            xTickLabelRotation = 0
            xTickLabelSpacing  = 0
            showValue          = "always"
            stacking           = "normal"
            groupWidth         = 0.7
            barWidth           = 0.97
            barRadius          = 0
            fullHighlight      = false
            tooltip = {
              mode = "single"
              sort = "none"
            }
            legend = {
              showLegend  = true
              displayMode = "list"
              placement   = "bottom"
              calcs       = []
            }
          }
        },
        {
          datasource = {
            type = "tempo"
            uid  = "tempo"
          }
          fieldConfig = {
            defaults = {
              color = {
                mode = "palette-classic"
              }
              custom = {
                cellOptions = {
                  type = "auto"
                }
                inspect = false
              }
              mappings = []
              thresholds = {
                mode = "absolute"
                steps = [
                  {
                    color = "green"
                    value = null
                  },
                  {
                    color = "red"
                    value = 80
                  }
                ]
              }
            }
            overrides = []
          }
          gridPos = {
            h = 8
            w = 24
            x = 0
            y = 16
          }
          id = 3
          options = {
            showHeader = true
            cellHeight = "sm"
            footer = {
              show      = false
              reducer   = ["sum"]
              countRows = false
              fields    = ""
            }
          }
          pluginVersion = "11.4.0"
          targets = [
            {
              datasource = {
                type = "tempo"
                uid  = "tempo"
              }
              query = "{}"
              refId = "A"
            }
          ]
          title = "Recent Trace Activity"
          type  = "table"
        }
      ]
      refresh       = "5s"
      schemaVersion = 39
      tags          = ["mcp-mesh", "distributed-tracing", "observability"]
      templating = {
        list = []
      }
      time = {
        from = "now-5m"
        to   = "now"
      }
      timepicker = {}
      timezone   = ""
      title      = "MCP Mesh Distributed Tracing"
      uid        = "mcp-mesh-overview"
      version    = 1
      weekStart  = ""
    })
  }
}