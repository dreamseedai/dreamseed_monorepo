# Admin Frontend Production Deployment - Summary

## 📋 Overview
This document summarizes all files created for deploying the `admin_front` Next.js application to production at `https://dreamseedai.com/admin/`.

---

## 📁 Files Created/Modified

### 1. Environment Configuration
- **`admin_front/.env.production`** - Production environment variables
- **`admin_front/.env.development`** - Development environment variables

### 2. Application Configuration
- **`admin_front/next.config.js`** - Next.js production configuration

### 3. API Configuration Updates
- **`admin_front/lib/questions.ts`** - Updated to use env variable
- **`admin_front/lib/topics.ts`** - Updated to use env variable
- **`admin_front/lib/meta.ts`** - Updated to use env variable

### 4. Infrastructure
- **`infra/systemd/admin-front.service`** - Systemd service file
- **`infra/nginx/admin.dreamseedai.com.conf`** - Nginx reverse proxy config

### 5. Deployment Scripts
- **`infra/deploy/deploy_admin_front.sh`** - Full deployment script
- **`admin_front/quick-deploy.sh`** - Quick rebuild script

### 6. Documentation
- **`admin_front/DEPLOYMENT.md`** - Complete deployment guide
- **`admin_front/DEPLOYMENT_SUMMARY.md`** - This file

---

## 🚀 Quick Start

### Build Locally First (Test)
```bash
cd /home/won/projects/dreamseed_monorepo/admin_front
npm install
npm run build
npm start  # Test on localhost:3031
```

### Deploy to Production
```bash
# 1. Build
cd /home/won/projects/dreamseed_monorepo/admin_front
npm install
NODE_ENV=production npm run build

# 2. Install systemd service
sudo cp /home/won/projects/dreamseed_monorepo/infra/systemd/admin-front.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable admin-front
sudo systemctl start admin-front

# 3. Configure Nginx (merge into existing config)
# Edit /etc/nginx/sites-available/dreamseedai.com
# Add the location blocks from infra/nginx/admin.dreamseedai.com.conf
sudo nginx -t
sudo systemctl reload nginx

# 4. Verify
curl https://dreamseedai.com/admin/
curl https://dreamseedai.com/api/admin/questions?limit=1
```

---

## 🔧 Configuration Details

### Environment Variables (Production)
```bash
NEXT_PUBLIC_API_BASE_URL=https://dreamseedai.com/api/admin
NODE_ENV=production
PORT=3031
```

### Service Details
- **Service Name**: `admin-front`
- **User**: `won`
- **Port**: `3031`
- **Working Directory**: `/home/won/projects/dreamseed_monorepo/admin_front`

### Nginx Routing
- `https://dreamseedai.com/admin/*` → `http://localhost:3031/`
- `https://dreamseedai.com/api/admin/*` → `http://localhost:8002/api/admin/`
- `https://dreamseedai.com/_next/*` → `http://localhost:3031/_next/` (static assets)

---

## 🔍 Verification Checklist

After deployment, verify:

- [ ] Service is running: `sudo systemctl status admin-front`
- [ ] Port 3031 is listening: `sudo lsof -i :3031`
- [ ] Frontend responds: `curl http://localhost:3031/`
- [ ] Nginx routes correctly: `curl https://dreamseedai.com/admin/`
- [ ] API is accessible: `curl https://dreamseedai.com/api/admin/questions?limit=1`
- [ ] Browser access: Visit `https://dreamseedai.com/admin/questions`
- [ ] Dark mode toggle works
- [ ] TinyMCE editors load properly
- [ ] CRUD operations work (create/edit/delete questions)

---

## 📊 Architecture

```
Browser Request
    ↓
https://dreamseedai.com/admin/*
    ↓
Nginx (Port 443)
    ↓
Reverse Proxy
    ↓
Next.js (localhost:3031) ←→ FastAPI (localhost:8002)
    ↓                            ↓
Serve React UI              PostgreSQL DB
```

---

## 🐛 Common Issues & Solutions

### Issue: Service won't start
```bash
sudo journalctl -u admin-front -n 50
# Check for Node.js version, missing dependencies, port conflicts
```

### Issue: 502 Bad Gateway
```bash
# Check if service is running
sudo systemctl status admin-front

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Issue: API calls return 404
```bash
# Verify backend is running
curl http://localhost:8002/api/admin/questions?limit=1

# Check nginx proxy configuration
sudo nginx -t
```

### Issue: Environment variables not working
```bash
# Restart service to pick up changes
sudo systemctl restart admin-front

# Verify in systemd
systemctl show admin-front | grep Environment
```

---

## 🔄 Update Workflow

When you make code changes:

```bash
# 1. Pull latest code
cd /home/won/projects/dreamseed_monorepo
git pull

# 2. Rebuild frontend
cd admin_front
npm install  # If dependencies changed
npm run build

# 3. Restart service
sudo systemctl restart admin-front

# 4. Verify
sudo systemctl status admin-front
curl https://dreamseedai.com/admin/
```

---

## 📝 Logs

### View service logs
```bash
sudo journalctl -u admin-front -f
```

### View nginx logs
```bash
sudo tail -f /var/log/nginx/access.log | grep '/admin'
sudo tail -f /var/log/nginx/error.log
```

### View application logs (if configured)
```bash
sudo tail -f /var/log/admin-front.log
sudo tail -f /var/log/admin-front-error.log
```

---

## 🔐 Security Notes

- Service runs as user `won` (non-root)
- Backend API only accessible via localhost
- HTTPS enforced via Nginx
- CORS configured in FastAPI backend
- Security headers added in Nginx config

---

## ✨ Features Deployed

- ✅ Questions list with search, filters, pagination
- ✅ Question editor with TinyMCE + MathML support
- ✅ Dark mode toggle with persistent state
- ✅ IRT parameters (difficulty, discrimination, guessing)
- ✅ Topic management with caching
- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Legacy data compatibility
- ✅ Auto-height text editors
- ✅ Real-time validation

---

## 📞 Support

For issues:
1. Check logs: `sudo journalctl -u admin-front -f`
2. Verify configuration: `sudo nginx -t`
3. Test API: `curl http://localhost:8002/api/admin/questions?limit=1`
4. Review deployment guide: `admin_front/DEPLOYMENT.md`

---

**Deployment Date**: 2025-11-17
**Version**: 1.0.0
**Status**: Ready for production deployment
