# Admin Frontend Deployment Guide

## Overview
This guide covers deploying the `admin_front` Next.js application as an independent service in production.

## Architecture
- **Frontend**: Next.js app running on `localhost:3031`
- **Backend**: FastAPI running on `localhost:8002`
- **Reverse Proxy**: Nginx routing requests:
  - `https://dreamseedai.com/admin/*` → Next.js frontend
  - `https://dreamseedai.com/api/admin/*` → FastAPI backend

## Prerequisites
- Node.js 18+ installed
- npm installed
- Nginx installed and configured
- SSL certificates for dreamseedai.com
- Backend API running on port 8002

---

## Deployment Steps

### 1. Build the Application

```bash
cd /home/won/projects/dreamseed_monorepo/admin_front

# Install dependencies
npm install

# Build for production
NODE_ENV=production npm run build

# Verify build
ls -la .next/
```

### 2. Install Systemd Service

```bash
# Copy service file
sudo cp /home/won/projects/dreamseed_monorepo/infra/systemd/admin-front.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable admin-front

# Start service
sudo systemctl start admin-front

# Check status
sudo systemctl status admin-front
```

**Verify service is running:**
```bash
# Check logs
sudo journalctl -u admin-front -f

# Check if port 3031 is listening
sudo lsof -i :3031

# Test locally
curl http://localhost:3031/
```

### 3. Configure Nginx

**Option A: Merge into existing dreamseedai.com config**

Edit your existing `/etc/nginx/sites-available/dreamseedai.com` (or similar) and add these location blocks:

```nginx
# Add inside your existing server { listen 443 ssl; ... } block

# Backend API
location /api/admin/ {
    proxy_pass http://127.0.0.1:8002/api/admin/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 120s;
}

# Admin Frontend
location /admin/ {
    proxy_pass http://127.0.0.1:3031/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
    proxy_buffering off;
}

# Next.js static files
location /_next/ {
    proxy_pass http://127.0.0.1:3031/_next/;
    proxy_http_version 1.1;
    expires 365d;
    add_header Cache-Control "public, max-age=31536000, immutable";
}
```

**Option B: Use standalone config file**

```bash
# Copy complete config
sudo cp /home/won/projects/dreamseed_monorepo/infra/nginx/admin.dreamseedai.com.conf /etc/nginx/sites-available/

# Create symlink (if using sites-enabled pattern)
sudo ln -s /etc/nginx/sites-available/admin.dreamseedai.com.conf /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 4. Verify Deployment

```bash
# Check frontend
curl -I https://dreamseedai.com/admin/

# Check API
curl https://dreamseedai.com/api/admin/questions?limit=1

# Check in browser
# Navigate to: https://dreamseedai.com/admin/questions
```

---

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u admin-front -n 50

# Check permissions
ls -la /home/won/projects/dreamseed_monorepo/admin_front/.next/

# Verify environment variables
systemctl show admin-front | grep Environment
```

### API calls failing
```bash
# Check backend is running
curl http://localhost:8002/api/admin/questions?limit=1

# Check nginx proxy
sudo nginx -t
sudo tail -f /var/log/nginx/error.log

# Verify environment variable in frontend
curl http://localhost:3031/api/admin/questions?limit=1
```

### Port 3031 already in use
```bash
# Find what's using the port
sudo lsof -i :3031

# Kill the process
sudo kill <PID>

# Or change port in:
# - .env.production
# - systemd service file
# - nginx config
```

### Build fails
```bash
cd /home/won/projects/dreamseed_monorepo/admin_front

# Clear cache
rm -rf .next node_modules package-lock.json

# Reinstall
npm install

# Try build again
npm run build
```

---

## Maintenance

### Updating the application
```bash
# Pull latest code
cd /home/won/projects/dreamseed_monorepo
git pull

# Rebuild
cd admin_front
npm install
npm run build

# Restart service
sudo systemctl restart admin-front

# Verify
sudo systemctl status admin-front
```

### Viewing logs
```bash
# Service logs
sudo journalctl -u admin-front -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log | grep '/admin'

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Stop/Start service
```bash
# Stop
sudo systemctl stop admin-front

# Start
sudo systemctl start admin-front

# Restart
sudo systemctl restart admin-front

# Status
sudo systemctl status admin-front
```

---

## Environment Variables

### Development (.env.development)
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8002/api/admin
NODE_ENV=development
PORT=3031
```

### Production (.env.production)
```
NEXT_PUBLIC_API_BASE_URL=https://dreamseedai.com/api/admin
NODE_ENV=production
PORT=3031
```

---

## Security Checklist

- [ ] SSL certificates are valid and up to date
- [ ] Backend API is only accessible via localhost (not exposed publicly)
- [ ] Nginx reverse proxy is configured with proper headers
- [ ] Service runs as non-root user (won)
- [ ] Firewall allows only ports 80/443
- [ ] Log rotation is configured
- [ ] Regular backups of database

---

## Performance Tuning

### Next.js
```bash
# Already configured in next.config.js:
# - Standalone output
# - Image optimization
# - Minification enabled
```

### Nginx
```nginx
# Add to nginx.conf
client_max_body_size 10M;
keepalive_timeout 65;
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

---

## Automated Deployment Script

For quick deployment, use the provided script:

```bash
/home/won/projects/dreamseed_monorepo/infra/deploy/deploy_admin_front.sh
```

This script will:
1. Build the Next.js app
2. Show you the manual steps for systemd and nginx setup

---

## Support

For issues or questions:
- Check logs: `sudo journalctl -u admin-front -f`
- Review nginx config: `sudo nginx -t`
- Test API connectivity: `curl http://localhost:8002/api/admin/questions?limit=1`
