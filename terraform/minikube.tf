# Minikube setup using null_resource (since there's no direct minikube provider)
resource "null_resource" "minikube_setup" {
  # Triggers for recreation
  triggers = {
    memory = var.minikube_memory
    cpus   = var.minikube_cpus
  }

  # Stop and delete existing minikube if it exists
  provisioner "local-exec" {
    command = "minikube delete || true"
  }

  # Start minikube with specified resources
  provisioner "local-exec" {
    command = "minikube start --memory=${var.minikube_memory} --cpus=${var.minikube_cpus} --driver=docker"
  }

  # Enable required addons
  provisioner "local-exec" {
    command = "minikube addons enable metrics-server"
  }

  # Wait for cluster to be ready
  provisioner "local-exec" {
    command = "kubectl wait --for=condition=Ready nodes --all --timeout=300s"
  }
}

# Build all Docker images using k8s Makefile
resource "null_resource" "build_images" {
  depends_on = [null_resource.minikube_setup]

  triggers = {
    # Rebuild when any image version changes
    images_hash = join(",", values(var.docker_images))
  }

  provisioner "local-exec" {
    # Run from terraform directory, navigate to ai-interviewer parent
    working_dir = ".."
    command = <<-EOF
      # Set minikube docker context
      eval $(minikube docker-env)
      
      # Build all images using the same logic as k8s Makefile
      echo "🏗️ Building backend image..."
      docker build -f backend/Dockerfile -t ai-interviewer/backend:latest .
      
      echo "🏗️ Building PDF extractor agent..."
      docker build -f services/pdf_extractor_agent/Dockerfile -t ai-interviewer/pdf-extractor:latest .
      
      echo "🏗️ Building interview agent..."
      docker build -f services/interview_agent/Dockerfile -t ai-interviewer/interview-agent:latest .
      
      echo "🏗️ Building LLM agent..."
      docker build -f services/llm_agent/Dockerfile -t ai-interviewer/llm-agent:latest .
      
      echo "🏗️ Building OpenAI LLM agent..."
      docker build -f services/openai_llm_agent/Dockerfile -t ai-interviewer/openai-llm-agent:latest .
      
      echo "🏗️ Building frontend first..."
      cd frontend && npm ci && npm run build && cd ..
      
      echo "🏗️ Building nginx gateway with UI..."
      docker build -f k8s/gateway/Dockerfile -t ai-interviewer/nginx-gateway:latest .
      
      echo "✅ All images built successfully"
    EOF
  }
}

# Load Docker images into minikube (now depends on build)
resource "null_resource" "load_images" {
  for_each = var.docker_images
  
  depends_on = [null_resource.build_images]

  triggers = {
    image = each.value
  }

  provisioner "local-exec" {
    command = "minikube image load ${each.value}"
    on_failure = continue
  }
}