[Unit]
Description=DreamSeed Uvicorn Service
After=network.target

[Service]
EnvironmentFile=/etc/dreamseed.env
WorkingDirectory=${WORKDIR}
ExecStart=/usr/bin/env bash -lc "uvicorn $APP_MODULE --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'"
Restart=always
RestartSec=5
TimeoutStopSec=15
User=${USER}
Group=${GROUP}
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
