#!/usr/bin/env bash
# Run this on the Digital Ocean droplet as root:
#   ssh root@147.182.191.226 'bash -s' < server-setup.sh

set -euo pipefail

DOMAIN="freestate.party"
WEBROOT="/var/www/$DOMAIN"

echo "==> Creating web root"
mkdir -p "$WEBROOT"

echo "==> Writing nginx config"
cat > /etc/nginx/sites-available/$DOMAIN <<'NGINX'
server {
    listen 80;
    listen [::]:80;
    server_name freestate.party www.freestate.party;

    root /var/www/freestate.party;
    index index.html;

    error_page 404 /404.html;

    location / {
        try_files $uri $uri/ =404;
    }

    # Cache static assets
    location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg|woff2?|ttf|mp4|webm)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX

echo "==> Enabling site"
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo "==> Testing nginx config"
nginx -t

echo "==> Reloading nginx"
systemctl reload nginx

echo "==> Installing certbot"
apt-get update -qq
apt-get install -y -qq certbot python3-certbot-nginx

echo "==> Getting SSL certificate"
certbot --nginx -d freestate.party -d www.freestate.party --non-interactive --agree-tos --email admin@freestate.party --redirect

echo "==> Done! Site is live at https://freestate.party"
