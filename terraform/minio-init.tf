# MinIO Bucket Initialization
# Creates necessary buckets for the AI Interviewer application

resource "null_resource" "minio_buckets" {
  depends_on = [
    kubernetes_deployment.minio,
    kubernetes_service.minio
  ]

  provisioner "local-exec" {
    command = <<-EOF
      echo "🪣 Creating MinIO buckets..."
      
      # Wait for MinIO to be ready
      sleep 10
      
      # Create buckets using kubectl exec
      kubectl exec -n ${var.namespace} deployment/ai-interviewer-minio -- sh -c "
        mc alias set local http://localhost:9000 minioadmin minioadmin &&
        mc mb local/ai-interviewer-uploads --ignore-existing &&
        mc mb local/resumes --ignore-existing &&
        mc mb local/interviews --ignore-existing &&
        mc mb local/recordings --ignore-existing &&
        mc mb local/transcripts --ignore-existing &&
        echo '✅ MinIO buckets created successfully' &&
        mc anonymous set download local/ai-interviewer-uploads &&
        echo '✅ MinIO bucket policies configured' &&
        mc ls local
      " || echo "⚠️  Failed to create some buckets (they may already exist)"
    EOF
  }

  triggers = {
    namespace = var.namespace
  }
}