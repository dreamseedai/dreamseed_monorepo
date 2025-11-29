#!/bin/bash
# Quick deployment commands - Admin Frontend

echo "🚀 Admin Frontend Quick Deploy"
echo ""

# Navigate to project
cd /home/won/projects/dreamseed_monorepo/admin_front

# Build
echo "📦 Building..."
npm install && npm run build

echo ""
echo "✅ Build complete!"
echo ""
echo "Next steps:"
echo ""
echo "1️⃣  Install/update systemd service:"
echo "    sudo cp /home/won/projects/dreamseed_monorepo/infra/systemd/admin-front.service /etc/systemd/system/"
echo "    sudo systemctl daemon-reload"
echo "    sudo systemctl restart admin-front"
echo ""
echo "2️⃣  Check status:"
echo "    sudo systemctl status admin-front"
echo ""
echo "3️⃣  View logs:"
echo "    sudo journalctl -u admin-front -f"
echo ""
echo "4️⃣  Test locally:"
echo "    curl http://localhost:3031/"
echo ""
echo "5️⃣  Test in production:"
echo "    curl https://dreamseedai.com/admin/"
echo ""
