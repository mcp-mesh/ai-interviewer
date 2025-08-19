# Nginx Configuration ConfigMap
resource "kubernetes_config_map" "nginx_config" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  metadata {
    name      = "nginx-simple-config"
    namespace = var.namespace
  }

  data = {
    "nginx-k8s.conf" = file("${path.module}/../k8s/gateway/nginx-k8s.conf")
  }
}

# Nginx Lua Scripts ConfigMap
resource "kubernetes_config_map" "nginx_lua_scripts" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  metadata {
    name      = "nginx-lua-scripts"
    namespace = var.namespace
  }

  data = {
    "auth_check.lua"            = file("${path.module}/../k8s/gateway/lua/auth_check.lua")
    "oauth_callback_simple.lua" = file("${path.module}/../k8s/gateway/lua/oauth_callback_simple.lua")
    "oauth_initiate.lua"        = file("${path.module}/../k8s/gateway/lua/oauth_initiate.lua")
    "logout.lua"                = file("${path.module}/../k8s/gateway/lua/logout.lua")
  }
}

# SSL certificate secret for nginx (reads from Let's Encrypt certificates)
resource "kubernetes_secret" "nginx_ssl" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  metadata {
    name      = "interviews-ink-tls"
    namespace = var.namespace
  }

  type = "tls"

  data = {
    "tls.crt" = fileexists("${path.module}/../ssl-interviews-ink-fullchain.pem") ? file("${path.module}/../ssl-interviews-ink-fullchain.pem") : ""
    "tls.key" = fileexists("${path.module}/../ssl-interviews-ink-privkey.pem") ? file("${path.module}/../ssl-interviews-ink-privkey.pem") : ""
  }

  lifecycle {
    # Prevent Terraform from updating certificates if they exist
    # This allows manual certificate renewal without Terraform interference
    ignore_changes = [
      data["tls.crt"],
      data["tls.key"]
    ]
  }
}

# OAuth Configuration Secret is now in env-secrets.tf