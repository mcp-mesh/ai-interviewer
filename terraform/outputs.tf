output "minikube_ip" {
  description = "Minikube cluster IP address"
  value       = "192.168.49.2"
}

output "application_url" {
  description = "Main application URL"
  value       = "https://192.168.49.100"
}

output "grafana_url" {
  description = "Grafana dashboard URL"
  value       = "https://192.168.49.100/grafana/"
}

# External access URLs (from iptables.tf)
output "external_urls" {
  description = "Public external access URLs"
  value = {
    main_app     = try(data.external.network_info.result.public_ip != "unknown" ? "https://${data.external.network_info.result.public_ip}/" : "External IP not detected", "External access not configured")
    grafana      = try(data.external.network_info.result.public_ip != "unknown" ? "https://${data.external.network_info.result.public_ip}/grafana/" : "External IP not detected", "External access not configured")
    health_check = try(data.external.network_info.result.public_ip != "unknown" ? "curl -k https://${data.external.network_info.result.public_ip}/health" : "External IP not detected", "External access not configured")
  }
}

output "registry_url" {
  description = "MCP Registry URL"
  value       = "https://192.168.49.100/registry/"
}

output "grafana_credentials" {
  description = "Grafana login credentials"
  value = {
    username = "admin"
    password = "admin"
  }
  sensitive = true
}

output "database_connections" {
  description = "Database connection strings"
  value = {
    postgres = "postgresql://ai_user:ai_password@ai-interviewer-postgres:5432/ai_interviewer"
    redis    = "redis://ai-interviewer-redis:6379"
    minio    = "http://ai-interviewer-minio:9000"
  }
  sensitive = true
}

output "services_status" {
  description = "Quick status check commands"
  value = {
    check_pods    = "kubectl get pods -n ${var.namespace}"
    check_services = "kubectl get services -n ${var.namespace}"
    check_ingress = "kubectl get service ai-interviewer-nginx-gateway -n ${var.namespace}"
    port_forward_backend = "kubectl port-forward -n ${var.namespace} service/ai-interviewer-backend 8080:8080"
  }
}

output "useful_commands" {
  description = "Useful kubectl commands for management"
  value = {
    restart_nginx = "kubectl rollout restart deployment ai-interviewer-nginx-gateway -n ${var.namespace}"
    restart_backend = "kubectl rollout restart deployment ai-interviewer-backend -n ${var.namespace}"
    view_logs_nginx = "kubectl logs -n ${var.namespace} -l app.kubernetes.io/name=ai-interviewer-nginx-gateway -f"
    view_logs_backend = "kubectl logs -n ${var.namespace} -l app.kubernetes.io/name=ai-interviewer-backend -f"
    exec_into_backend = "kubectl exec -n ${var.namespace} -it deployment/ai-interviewer-backend -- /bin/bash"
  }
}