#!/usr/bin/env python3
"""
Generate detailed issue bodies per service from template blocks.
Usage:
  python scripts/generate_issue_body_from_template.py project_management/github_issues.csv > project_management/github_issues_with_bodies.csv
"""
import csv
import sys
from textwrap import dedent

SERVICE_SNIPPETS = {
    "r-glmm-plumber": dedent(
        """
        Service: r-glmm-plumber
        K8s: ops/k8s/r-plumber (overlays/internal for internal-only)
        CI: build-r-plumber matrix entry, ServiceMonitor scraping /healthz
        Tests: tests/r-plumber.http (health/fit/predict/forecast)

        Acceptance Criteria (service-specific)
        - [ ] /glmm/fit, /glmm/predict, /forecast/summary 200 응답 및 스키마 준수
        - [ ] 경고/오류 safe_glmer 캡처 및 로그(run_id) 기록
        - [ ] Ingress 미노출(내부 전용), NetworkPolicy 제한
        """
    ).strip(),
    "r-irt-plumber": dedent(
        """
        Service: r-irt-plumber
        K8s: ops/k8s/r-irt-plumber
        CI: build-r-plumber matrix entry to include r-irt
        Tests: tests/r-irt.http (calibrate/score)

        Acceptance Criteria (service-specific)
        - [ ] /irt/calibrate에서 item params/abilities/metrics 반환, /irt/score 정상
        - [ ] DB 업서트 파이프라인과 스키마(mirt_item_params, mirt_ability) 정합
        - [ ] Cron nightly 성공률/알람 구성
        """
    ).strip(),
    "r-brms-plumber": dedent(
        """
        Service: r-brms-plumber
        Notes: requires rstan/cmdstan toolchain; cache builds
        K8s: ops/k8s/r-brms-plumber
        CI: build with longer timeout; cache toolchain

        Acceptance Criteria (service-specific)
        - [ ] /growth/fit, /growth/predict, /growth/posterior-summary 구현
        - [ ] forecast API에서 brms 모드→Normal 폴백 검증
        - [ ] 빌드 캐시/도커 이미지 최적화 완료
        """
    ).strip(),
    "quarto-reports": dedent(
        """
        Reports: Quarto templates (reports/quarto/*.qmd)
        Runner: tools/quarto-runner image (TinyTeX)
        API: /reports/generate, artifacts in report_artifact
        Tests: build sample PDF/HTML in CI and attach as artifact

        Acceptance Criteria (report-specific)
        - [ ] 주간 리포트에 능력 추세/목표확률/추천 Top-N 포함
        - [ ] 다국어/브랜딩 설정 _quarto.yml 에서 관리
        - [ ] 렌더 실패 시 재시도/로그(run_id) 확인
        """
    ).strip(),
}

# Fallback keyword mapping: if explicit service key not found in title, try these keywords
KEYWORD_TO_SERVICE = {
    "irt": "r-irt-plumber",
    "brms": "r-brms-plumber",
    "bayesian": "r-brms-plumber",
    "quarto": "quarto-reports",
    "report": "quarto-reports",
    "glmm": "r-glmm-plumber",
}

CHECKLIST_BASE = dedent(
    """
    Acceptance Criteria
    - [ ] Functional endpoints or jobs deliver expected outputs
    - [ ] Errors handled and logged with run_id
    - [ ] Metrics and health endpoints wired to ServiceMonitor
    - [ ] Secrets and config injected via ExternalSecret/ConfigMap where applicable

    Tests
    - [ ] Unit and integration tests added
    - [ ] E2E smoke in CI or instructions provided
    - [ ] Load/perf tests where applicable

    Deployment
    - [ ] Kustomize base + overlays updated
    - [ ] CI workflow updated to build/push images
    - [ ] ArgoCD sync verified

    Rollout
    - [ ] Feature flag or staged rollout plan documented
    - [ ] Dashboards/alerts in place and validated
    """
).strip()


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_issue_body_from_template.py <csv_in>", file=sys.stderr)
        sys.exit(1)

    inp = sys.argv[1]
    with open(inp, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        # Keep original fields, replace body if it exists, or add it
        fieldnames = list(reader.fieldnames or [])
        if 'body' not in fieldnames:
            fieldnames.append('body')
        
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for row in reader:
            title = row.get("title", "")
            # detect service block
            body_parts = [f"Auto-generated issue for roadmap item {row.get('id','')}\n"]
            matched = False
            for key, snippet in SERVICE_SNIPPETS.items():
                if key.replace('-', ' ') in title.lower() or key in title.lower():
                    body_parts.append(snippet)
                    matched = True
            if not matched:
                # try keyword-based detection (first match wins)
                t = title.lower()
                for kw, svc in KEYWORD_TO_SERVICE.items():
                    if kw in t and svc in SERVICE_SNIPPETS:
                        body_parts.append(SERVICE_SNIPPETS[svc])
                        break
            body_parts.append(CHECKLIST_BASE)
            row["body"] = "\n\n".join(body_parts)
            writer.writerow(row)

if __name__ == "__main__":
    main()
