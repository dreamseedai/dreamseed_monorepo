# Admin Frontend - Quick Deployment Guide

## 🚀 One-Command Deployment

```bash
cd /home/won/projects/dreamseed_monorepo/admin_front
./deploy.sh
```

That's it! The script will:
1. Pull latest code from git
2. Install dependencies
3. Build Next.js for production
4. Restart the server on port 3100
5. Test and reload NGINX
6. Run health check

## 📋 What the Script Does

```bash
./deploy.sh
```

Executes:
- ✅ `git pull --ff-only` - Get latest code
- ✅ `npm install` - Install/update dependencies
- ✅ `npm run build` - Production build
- ✅ `pkill -f "next-server"` - Stop old process
- ✅ `PORT=3100 npm run start &` - Start new server
- ✅ `sudo nginx -t && sudo systemctl reload nginx` - Reload NGINX
- ✅ `curl https://admin.dreamseedai.com/questions` - Health check

## 🔧 Manual Deployment (if needed)

### 1. Build
```bash
cd /home/won/projects/dreamseed_monorepo/admin_front
npm install
npm run build
```

### 2. Restart Server
```bash
# Stop existing
pkill -f "next-server"

# Start new
PORT=3100 npm run start > /tmp/admin_front_prod.log 2>&1 &
```

### 3. Reload NGINX
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 🔍 Verify Deployment

```bash
# Check server is running
ss -tlnp | grep :3100

# Check HTTPS works
curl -I https://admin.dreamseedai.com/questions

# Check API works
curl -s https://admin.dreamseedai.com/api/admin/questions/13164 | jq .id
```

## 📊 Monitoring

### Check Logs
```bash
# Next.js logs
tail -f /tmp/admin_front_prod.log

# NGINX error logs
sudo tail -f /var/log/nginx/error.log
```

### Check Process
```bash
# Find Next.js process
ps aux | grep "next-server"

# Check port
lsof -i :3100
```

## 🛠️ Troubleshooting

### Server won't start
```bash
# Check logs
tail -50 /tmp/admin_front_prod.log

# Check port is free
lsof -i :3100

# Try manual restart
pkill -f "next-server"
PORT=3100 npm run start
```

### Build fails
```bash
# Clean build
rm -rf .next
npm run build
```

### NGINX issues
```bash
# Test config
sudo nginx -t

# Check admin config
sudo cat /etc/nginx/sites-available/admin.dreamseedai.com

# Reload
sudo systemctl reload nginx
```

## 🔄 Rollback

If deployment fails, rollback to previous version:

```bash
cd /home/won/projects/dreamseed_monorepo/admin_front

# Revert git
git reset --hard HEAD~1

# Rebuild
npm run build

# Restart
pkill -f "next-server"
PORT=3100 npm run start > /tmp/admin_front_prod.log 2>&1 &
```

## 📝 Environment Variables

Current production setup:

```bash
# .env.production
NEXT_PUBLIC_API_BASE_URL=http://admin.dreamseedai.com
NEXT_PUBLIC_API_PREFIX=/api/admin
NODE_ENV=production
PORT=3100
```

## 🎯 Production URLs

- **Frontend**: https://admin.dreamseedai.com
- **Questions List**: https://admin.dreamseedai.com/questions
- **Edit Page**: https://admin.dreamseedai.com/questions/[id]/edit
- **API**: https://admin.dreamseedai.com/api/admin/questions

## 🔐 Security Notes

- ✅ HTTPS enabled (Let's Encrypt)
- ✅ HTTP → HTTPS redirect
- ✅ Certificate auto-renewal
- ✅ Separate subdomain (admin.dreamseedai.com)
- ⚠️ Add authentication before public release!

---

**Last Updated**: 2025-11-18  
**Script Location**: `/home/won/projects/dreamseed_monorepo/infra/deploy/deploy_admin_front.sh`  
**Symlink**: `./deploy.sh` (in admin_front directory)
