#!/bin/bash
# Safe iptables setup for AI Interviewer - adapted for your cloud VM
# Based on k8s/Makefile but with safety checks and your specific network

set -e  # Exit on any error

# Your network configuration (detected)
VM_PUBLIC_IP="91.99.183.40"
METALLB_IP="192.168.49.100"
MAIN_INTERFACE="eth0"
MINIKUBE_BRIDGE="br-8b84705a8843"

echo "🔧 Safe iptables setup for AI Interviewer"
echo ""
echo "📋 Configuration:"
echo "  VM Public IP: $VM_PUBLIC_IP"
echo "  MetalLB IP: $METALLB_IP"
echo "  Main Interface: $MAIN_INTERFACE"
echo "  Minikube Bridge: $MINIKUBE_BRIDGE"
echo ""

# Safety function
test_connectivity() {
    echo "🔍 Testing internet connectivity..."
    if ping -c 1 -W 5 8.8.8.8 >/dev/null 2>&1; then
        echo "✅ Internet connectivity OK"
        return 0
    else
        echo "❌ Internet connectivity LOST!"
        return 1
    fi
}

# Emergency rollback function (if called manually)
emergency_rollback() {
    echo "🚨 EMERGENCY ROLLBACK - Removing all rules..."
    
    # Remove DNAT rules
    sudo iptables -t nat -D PREROUTING -d $VM_PUBLIC_IP -p tcp --dport 443 -j DNAT --to-destination $METALLB_IP:443 2>/dev/null || true
    sudo iptables -t nat -D PREROUTING -d $VM_PUBLIC_IP -p tcp --dport 80 -j DNAT --to-destination $METALLB_IP:80 2>/dev/null || true
    sudo iptables -t nat -D OUTPUT -d $VM_PUBLIC_IP -p tcp --dport 443 -j DNAT --to-destination $METALLB_IP:443 2>/dev/null || true
    sudo iptables -t nat -D OUTPUT -d $VM_PUBLIC_IP -p tcp --dport 80 -j DNAT --to-destination $METALLB_IP:80 2>/dev/null || true
    
    # Remove MASQUERADE rules
    sudo iptables -t nat -D POSTROUTING -d 192.168.49.0/24 -j MASQUERADE 2>/dev/null || true
    sudo iptables -t nat -D POSTROUTING -s 192.168.49.0/24 -o $MAIN_INTERFACE -j MASQUERADE 2>/dev/null || true
    
    echo "🔄 Testing connectivity after rollback..."
    test_connectivity && echo "✅ Connectivity restored!" || echo "❌ May need full restore: sudo iptables-restore < /tmp/iptables-backup-*.txt"
}

# Backup current rules
echo "💾 Backing up current iptables rules..."
sudo iptables-save > /tmp/iptables-backup-$(date +%Y%m%d-%H%M%S).txt
echo "✅ Backup saved to /tmp/iptables-backup-$(date +%Y%m%d-%H%M%S).txt"
echo ""

# Test current connectivity
test_connectivity || exit 1
echo ""

echo "⚠️  WARNING: This will modify your iptables rules"
echo "⚠️  This configures traffic forwarding from $VM_PUBLIC_IP to $METALLB_IP"
echo "⚠️  Press Ctrl+C within 10 seconds to cancel..."
echo ""
for i in {10..1}; do
    echo -n "$i "
    sleep 1
done
echo ""
echo ""

echo "📡 Step 1: Setting up DNAT rules (port forwarding)..."
sudo iptables -t nat -A PREROUTING -d $VM_PUBLIC_IP -p tcp --dport 443 -j DNAT --to-destination $METALLB_IP:443
sudo iptables -t nat -A PREROUTING -d $VM_PUBLIC_IP -p tcp --dport 80 -j DNAT --to-destination $METALLB_IP:80
sudo iptables -t nat -A OUTPUT -d $VM_PUBLIC_IP -p tcp --dport 443 -j DNAT --to-destination $METALLB_IP:443
sudo iptables -t nat -A OUTPUT -d $VM_PUBLIC_IP -p tcp --dport 80 -j DNAT --to-destination $METALLB_IP:80
echo "✅ DNAT rules applied"

# Test connectivity after DNAT
test_connectivity || {
    echo "🚨 Connectivity lost after DNAT rules! Rolling back..."
    echo "🔄 Removing DNAT rules..."
    sudo iptables -t nat -D PREROUTING -d $VM_PUBLIC_IP -p tcp --dport 443 -j DNAT --to-destination $METALLB_IP:443 2>/dev/null || true
    sudo iptables -t nat -D PREROUTING -d $VM_PUBLIC_IP -p tcp --dport 80 -j DNAT --to-destination $METALLB_IP:80 2>/dev/null || true
    sudo iptables -t nat -D OUTPUT -d $VM_PUBLIC_IP -p tcp --dport 443 -j DNAT --to-destination $METALLB_IP:443 2>/dev/null || true
    sudo iptables -t nat -D OUTPUT -d $VM_PUBLIC_IP -p tcp --dport 80 -j DNAT --to-destination $METALLB_IP:80 2>/dev/null || true
    exit 1
}

echo "📡 Step 2: Setting up MASQUERADE rules (NAT) - SPECIFIC RULES ONLY..."
# IMPORTANT: Only masquerade traffic to minikube network, NOT all traffic
MINIKUBE_NETWORK="192.168.49.0/24"
sudo iptables -t nat -A POSTROUTING -d $MINIKUBE_NETWORK -j MASQUERADE
sudo iptables -t nat -A POSTROUTING -s $MINIKUBE_NETWORK -o $MAIN_INTERFACE -j MASQUERADE
echo "✅ MASQUERADE rules applied (restricted to minikube network only)"

# Test connectivity after MASQUERADE
test_connectivity || {
    echo "🚨 Connectivity lost after MASQUERADE rules! Rolling back..."
    echo "🔄 Removing MASQUERADE rules..."
    sudo iptables -t nat -D POSTROUTING -d $MINIKUBE_NETWORK -j MASQUERADE 2>/dev/null || true
    sudo iptables -t nat -D POSTROUTING -s $MINIKUBE_NETWORK -o $MAIN_INTERFACE -j MASQUERADE 2>/dev/null || true
    echo "⚠️  If connectivity still lost, restore from backup: sudo iptables-restore < /tmp/iptables-backup-*.txt"
    exit 1
}

echo "📡 Step 3: Setting up FORWARD rules (traffic flow)..."
sudo iptables -I FORWARD 1 -i $MAIN_INTERFACE -o $MINIKUBE_BRIDGE -d $METALLB_IP -p tcp --dport 443 -j ACCEPT
sudo iptables -I FORWARD 2 -i $MINIKUBE_BRIDGE -o $MAIN_INTERFACE -s $METALLB_IP -p tcp --sport 443 -j ACCEPT
sudo iptables -I FORWARD 3 -i $MAIN_INTERFACE -o $MINIKUBE_BRIDGE -d $METALLB_IP -p tcp --dport 80 -j ACCEPT
sudo iptables -I FORWARD 4 -i $MINIKUBE_BRIDGE -o $MAIN_INTERFACE -s $METALLB_IP -p tcp --sport 80 -j ACCEPT
sudo iptables -A FORWARD -d $METALLB_IP -p tcp -m multiport --dports 80,443 -j ACCEPT
sudo iptables -A FORWARD -s $METALLB_IP -p tcp -m multiport --sports 80,443 -j ACCEPT
echo "✅ FORWARD rules applied"

# Final connectivity test
echo ""
echo "🔍 Final connectivity test..."
test_connectivity || {
    echo "🚨 Connectivity lost after FORWARD rules!"
    echo "⚠️  Manual cleanup may be required. Check backup file."
    exit 1
}

echo ""
echo "✅ iptables configuration complete!"
echo ""
echo "🎯 Test your application:"
echo "  External URL: https://$VM_PUBLIC_IP/"
echo "  Health check: https://$VM_PUBLIC_IP/health"
echo ""
echo "🧪 Test commands:"
echo "  curl -k https://$VM_PUBLIC_IP/health"
echo "  curl -k https://$VM_PUBLIC_IP/"
echo ""
echo "💡 To make rules persistent:"
echo "  sudo apt install iptables-persistent"
echo "  sudo netfilter-persistent save"
echo ""
echo "🔄 To remove rules, use the backup file:"
echo "  sudo iptables-restore < /tmp/iptables-backup-*.txt"