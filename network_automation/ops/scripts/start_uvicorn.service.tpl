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

# --- Hardening ---
NoNewPrivileges=yes
ProtectSystem=full
ProtectHome=true
PrivateTmp=true
ProtectControlGroups=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectClock=yes
LockPersonality=yes
CapabilityBoundingSet=~CAP_SYS_ADMIN CAP_NET_ADMIN CAP_SYS_MODULE CAP_SYS_PTRACE CAP_SETUID CAP_SETGID
RestrictSUIDSGID=yes
RestrictRealtime=yes
MemoryDenyWriteExecute=yes
SystemCallArchitectures=native
SystemCallFilter=@system-service @basic-io @network-io ~@mount ~@privileged

[Install]
WantedBy=multi-user.target