# Nginx Security & Rate Limiting

This folder contains Nginx snippets:
- `security_headers.conf` — strict security headers (HSTS, CSP, etc.)
- `rate_limit.conf` — zones and examples for request/connection limiting

## Usage (bare Nginx)

In `nginx.conf` (http context):
```
include /path/to/rate_limit.conf;
```

In `server` block handling HTTPS:
```
ssl_certificate ...;
ssl_certificate_key ...;

include /path/to/security_headers.conf;

location /api/ {
  limit_req zone=req_per_ip burst=50 nodelay;
  limit_conn conn_per_ip 20;
  proxy_pass http://backend;
}
```

Tune `rate`, `burst`, and connection caps to your traffic profile.
