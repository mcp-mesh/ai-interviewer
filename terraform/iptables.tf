# IPTables Configuration for External Access
# Sets up port forwarding from public IP to MetalLB LoadBalancer

# Get the public IP and MetalLB IP
data "external" "network_info" {
  program = ["bash", "-c", <<-EOF
    PUBLIC_IP=$(curl -s -4 ifconfig.me || curl -s ipv4.icanhazip.com || echo "unknown")
    METALLB_IP="192.168.49.100"
    
    cat <<JSON
{
  "public_ip": "$PUBLIC_IP",
  "metallb_ip": "$METALLB_IP",
  "main_interface": "eth0",
  "minikube_network": "192.168.49.0/24"
}
JSON
EOF
  ]
}

# Create iptables backup before applying rules
resource "null_resource" "iptables_backup" {
  provisioner "local-exec" {
    command = <<-EOF
      echo "💾 Creating iptables backup..."
      BACKUP_FILE="/tmp/iptables-backup-terraform-$(date +%Y%m%d-%H%M%S).txt"
      sudo iptables-save > "$BACKUP_FILE"
      
      # Store the backup file path for destroy
      echo "$BACKUP_FILE" > /tmp/terraform-iptables-backup-path.txt
      echo "✅ Backup created: $BACKUP_FILE"
    EOF
  }

  triggers = {
    minikube_id = var.minikube_memory # Trigger when minikube changes
  }
}

# Apply iptables rules for external access
resource "null_resource" "iptables_setup" {
  depends_on = [
    null_resource.iptables_backup,
    kubectl_manifest.metallb_l2_advertisement,
    kubernetes_service.nginx_gateway
  ]

  provisioner "local-exec" {
    command = <<-EOF
      set -e
      
      PUBLIC_IP="${data.external.network_info.result.public_ip}"
      METALLB_IP="${data.external.network_info.result.metallb_ip}"
      MAIN_INTERFACE="${data.external.network_info.result.main_interface}"
      MINIKUBE_NETWORK="${data.external.network_info.result.minikube_network}"
      
      echo "🔧 Setting up iptables rules for external access..."
      echo "  Public IP: $PUBLIC_IP"
      echo "  MetalLB IP: $METALLB_IP"
      
      # Test connectivity before applying rules
      echo "🔍 Testing connectivity..."
      ping -c 1 -W 5 8.8.8.8 > /dev/null || {
        echo "❌ No internet connectivity - aborting iptables setup"
        exit 1
      }
      
      # Get NodePort values from service
      HTTP_NODEPORT=$(kubectl get svc -n ai-interviewer ai-interviewer-nginx-gateway -o jsonpath='{.spec.ports[?(@.name=="http")].nodePort}')
      HTTPS_NODEPORT=$(kubectl get svc -n ai-interviewer ai-interviewer-nginx-gateway -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')
      MINIKUBE_IP="192.168.49.2"
      
      echo "  NodePorts: HTTP=$HTTP_NODEPORT, HTTPS=$HTTPS_NODEPORT"
      
      # Step 1: DNAT rules (port forwarding to NodePorts)
      echo "📡 Setting up DNAT rules..."
      sudo iptables -t nat -A PREROUTING -d $PUBLIC_IP -p tcp --dport 443 -j DNAT --to-destination $MINIKUBE_IP:$HTTPS_NODEPORT
      sudo iptables -t nat -A PREROUTING -d $PUBLIC_IP -p tcp --dport 80 -j DNAT --to-destination $MINIKUBE_IP:$HTTP_NODEPORT
      sudo iptables -t nat -A OUTPUT -d $PUBLIC_IP -p tcp --dport 443 -j DNAT --to-destination $MINIKUBE_IP:$HTTPS_NODEPORT
      sudo iptables -t nat -A OUTPUT -d $PUBLIC_IP -p tcp --dport 80 -j DNAT --to-destination $MINIKUBE_IP:$HTTP_NODEPORT
      
      # Step 2: MASQUERADE rules (NAT) - specific to minikube network only
      echo "📡 Setting up MASQUERADE rules..."
      sudo iptables -t nat -A POSTROUTING -d $MINIKUBE_NETWORK -j MASQUERADE
      sudo iptables -t nat -A POSTROUTING -s $MINIKUBE_NETWORK -o $MAIN_INTERFACE -j MASQUERADE
      
      # Step 3: FORWARD rules (traffic flow)
      echo "📡 Setting up FORWARD rules..."
      MINIKUBE_BRIDGE=$(docker network ls -q -f name=minikube | head -1)
      if [ -n "$MINIKUBE_BRIDGE" ]; then
        BRIDGE_NAME="br-$MINIKUBE_BRIDGE"
        # Allow forwarding between external interface and minikube bridge
        sudo iptables -I FORWARD 1 -i $MAIN_INTERFACE -o $BRIDGE_NAME -j ACCEPT
        sudo iptables -I FORWARD 2 -i $BRIDGE_NAME -o $MAIN_INTERFACE -j ACCEPT
      fi
      
      # Ensure forwarding is enabled
      sudo sysctl -w net.ipv4.ip_forward=1
      
      # Allow established connections
      sudo iptables -I FORWARD 1 -m state --state ESTABLISHED,RELATED -j ACCEPT
      
      # Final connectivity test
      echo "🔍 Testing connectivity after rules..."
      ping -c 1 -W 5 8.8.8.8 > /dev/null || {
        echo "❌ Connectivity lost! Rules may need manual cleanup"
        exit 1
      }
      
      echo "✅ IPTables configuration complete!"
      echo "🎯 External access URL: https://$PUBLIC_IP/"
      echo "🧪 Test: curl -k https://$PUBLIC_IP/health"
    EOF

    on_failure = fail
  }

  # Cleanup on destroy
  provisioner "local-exec" {
    when    = destroy
    command = <<-EOF
      echo "🧹 Cleaning up iptables rules..."
      
      # Get the Terraform-created backup file path
      BACKUP_PATH_FILE="/tmp/terraform-iptables-backup-path.txt"
      
      if [ -f "$BACKUP_PATH_FILE" ]; then
        BACKUP_FILE=$(cat "$BACKUP_PATH_FILE")
        echo "🔄 Using Terraform backup file: $BACKUP_FILE"
      else
        # Fallback to earliest backup file (should be cleanest)
        BACKUP_FILE=$(ls -t /tmp/iptables-backup-*.txt 2>/dev/null | tail -1)
        echo "🔄 Using earliest backup file: $BACKUP_FILE"
      fi
      
      if [ -n "$BACKUP_FILE" ] && [ -f "$BACKUP_FILE" ]; then
        echo "🔄 Restoring iptables from backup: $BACKUP_FILE"
        sudo iptables-restore < "$BACKUP_FILE" && {
          echo "✅ Successfully restored iptables from backup"
          # Clean up the backup path file
          rm -f "$BACKUP_PATH_FILE" 2>/dev/null || true
        } || {
          echo "⚠️  Backup restore failed, attempting manual cleanup..."
          
          # Get current network info for manual cleanup
          PUBLIC_IP=$(curl -s -4 ifconfig.me || curl -s ipv4.icanhazip.com || echo "91.99.183.40")
          MINIKUBE_IP="192.168.49.2"  # Actual minikube node IP
          MINIKUBE_NETWORK="192.168.49.0/24"
          
          # Get current NodePorts if possible
          HTTP_NODEPORT=$(kubectl get svc -n ai-interviewer ai-interviewer-nginx-gateway -o jsonpath='{.spec.ports[?(@.name=="http")].nodePort}' 2>/dev/null || echo "30864")
          HTTPS_NODEPORT=$(kubectl get svc -n ai-interviewer ai-interviewer-nginx-gateway -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}' 2>/dev/null || echo "31451")
          
          echo "Cleaning up with: PUBLIC_IP=$PUBLIC_IP, MINIKUBE_IP=$MINIKUBE_IP, HTTP_NODEPORT=$HTTP_NODEPORT, HTTPS_NODEPORT=$HTTPS_NODEPORT"
          
          # Remove DNAT rules (using actual NodePorts that were created)
          sudo iptables -t nat -D PREROUTING -d $PUBLIC_IP -p tcp --dport 443 -j DNAT --to-destination $MINIKUBE_IP:$HTTPS_NODEPORT 2>/dev/null || true
          sudo iptables -t nat -D PREROUTING -d $PUBLIC_IP -p tcp --dport 80 -j DNAT --to-destination $MINIKUBE_IP:$HTTP_NODEPORT 2>/dev/null || true
          sudo iptables -t nat -D OUTPUT -d $PUBLIC_IP -p tcp --dport 443 -j DNAT --to-destination $MINIKUBE_IP:$HTTPS_NODEPORT 2>/dev/null || true
          sudo iptables -t nat -D OUTPUT -d $PUBLIC_IP -p tcp --dport 80 -j DNAT --to-destination $MINIKUBE_IP:$HTTP_NODEPORT 2>/dev/null || true
          
          # Remove MASQUERADE rules
          sudo iptables -t nat -D POSTROUTING -d $MINIKUBE_NETWORK -j MASQUERADE 2>/dev/null || true
          sudo iptables -t nat -D POSTROUTING -s $MINIKUBE_NETWORK -o eth0 -j MASQUERADE 2>/dev/null || true
          
          # Remove FORWARD rules 
          sudo iptables -D FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT 2>/dev/null || true
          
          # Try to remove bridge-specific FORWARD rules
          MINIKUBE_BRIDGE=$(docker network ls -q -f name=minikube 2>/dev/null | head -1)
          if [ -n "$MINIKUBE_BRIDGE" ]; then
            BRIDGE_NAME="br-$MINIKUBE_BRIDGE"
            sudo iptables -D FORWARD -i eth0 -o $BRIDGE_NAME -j ACCEPT 2>/dev/null || true
            sudo iptables -D FORWARD -i $BRIDGE_NAME -o eth0 -j ACCEPT 2>/dev/null || true
          fi
          
          echo "✅ Manual cleanup completed"
        }
      else
        echo "⚠️  No backup file found"
        echo "🔧 Attempting complete iptables flush as fallback..."
        sudo iptables -F 2>/dev/null || true
        sudo iptables -t nat -F 2>/dev/null || true
        echo "✅ iptables tables flushed"
      fi
    EOF

    on_failure = continue
  }

  triggers = {
    minikube_id = var.minikube_memory
    public_ip   = data.external.network_info.result.public_ip
    metallb_ip  = data.external.network_info.result.metallb_ip
  }
}

# Output the access information
output "external_access" {
  description = "External access information"
  value = {
    public_ip    = data.external.network_info.result.public_ip
    metallb_ip   = data.external.network_info.result.metallb_ip
    https_url    = "https://${data.external.network_info.result.public_ip}/"
    health_check = "curl -k https://${data.external.network_info.result.public_ip}/health"
  }

  depends_on = [null_resource.iptables_setup]
}