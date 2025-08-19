terraform {
  required_version = ">= 1.0"
  
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = "~> 1.14"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

# Provider configurations will use minikube's kubeconfig
provider "kubernetes" {
  config_path = "~/.kube/config"
  config_context = "minikube"
  
  # Allow plan even if context doesn't exist yet
  ignore_labels = ["minikube.k8s.io/version"]
}

provider "helm" {
  kubernetes {
    config_path = "~/.kube/config" 
    config_context = "minikube"
  }
}

provider "kubectl" {
  config_path = "~/.kube/config"
  config_context = "minikube"
}