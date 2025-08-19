# SSL Certificate Management

This project uses Let's Encrypt SSL certificates for the domains `interviews.ink` and `www.interviews.ink`.

## Certificate Files

- `ssl-interviews-ink-fullchain.pem` - Public certificate chain (safe to commit)
- `ssl-interviews-ink-privkey.pem` - Private key (excluded from git via .gitignore)

## Certificate Management

### Initial Setup
Certificates were generated using certbot with DNS challenge:
```bash
sudo certbot certonly --manual --preferred-challenges dns -d interviews.ink -d www.interviews.ink --email dhyan.raj@gmail.com --agree-tos --no-eff-email
```

### Terraform Integration
Terraform automatically reads the certificate files and creates the Kubernetes secret:
```hcl
resource "kubernetes_secret" "nginx_ssl" {
  metadata {
    name      = "interviews-ink-tls"
    namespace = var.namespace
  }
  type = "tls"
  data = {
    "tls.crt" = file("${path.module}/../ssl-interviews-ink-fullchain.pem")
    "tls.key" = file("${path.module}/../ssl-interviews-ink-privkey.pem")
  }
}
```

### Certificate Renewal
Certificates expire every 3 months. To renew:

1. Run certbot renewal:
   ```bash
   sudo certbot renew --manual
   ```

2. Copy new certificates to project root:
   ```bash
   sudo cp /etc/letsencrypt/live/interviews.ink/fullchain.pem ./ssl-interviews-ink-fullchain.pem
   sudo cp /etc/letsencrypt/live/interviews.ink/privkey.pem ./ssl-interviews-ink-privkey.pem
   sudo chown $USER:$USER ./ssl-interviews-ink-*.pem
   ```

3. Apply with Terraform:
   ```bash
   cd terraform
   terraform apply -target=kubernetes_secret.nginx_ssl
   ```

4. Restart nginx deployment:
   ```bash
   kubectl rollout restart deployment ai-interviewer-nginx-gateway -n ai-interviewer
   ```

## Security Notes

- Private key is excluded from version control
- Public certificate can be safely committed
- Terraform lifecycle rules prevent accidental certificate overwrites
- Certificates are valid for interviews.ink and www.interviews.ink

## Current Certificate
- **Issuer**: Let's Encrypt (E5)
- **Valid**: Aug 19, 2025 - Nov 17, 2025
- **Domains**: interviews.ink, www.interviews.ink