# Vault Agent 설정 - Alert Threader 환경변수 렌더링
# 사용법: vault agent -config=/etc/vault-agent.d/alert-threader.hcl

exit_after_auth = false
pid_file = "/run/vault-agent-alert-threader.pid"

# =============================
# Vault 연결 설정
# =============================
vault {
  address = "https://vault.mycorp.local:8200"
  # TLS 설정 (필요시)
  # tls_skip_verify = true
  # ca_cert = "/etc/ssl/certs/vault-ca.pem"
}

# =============================
# 자동 인증 설정
# =============================
auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path = "/etc/vault-agent.d/role_id"
      secret_id_file_path = "/etc/vault-agent.d/secret_id"
    }
  }

  # 토큰 저장소
  sink "file" {
    config = {
      path = "/run/vault/.token"
    }
  }
}

# =============================
# 템플릿 렌더링 설정
# =============================
template {
  source      = "/etc/vault-agent.d/alert-threader.tpl"
  destination = "/run/alert-threader.env"
  perms       = 0640
  user        = "root"
  group       = "root"
  
  # 템플릿 변경 감지 시 자동 재렌더링
  create_dest_dirs = true
  
  # 렌더링 후 명령 실행 (선택사항)
  # command = "systemctl reload alert-threader-python"
}

# =============================
# 로깅 설정
# =============================
log_level = "INFO"
log_format = "json"
log_file = "/var/log/vault-agent-alert-threader.log"
