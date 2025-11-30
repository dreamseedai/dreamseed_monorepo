#!/usr/bin/env python3
"""
Weekly Security Report Generator

Generates a comprehensive markdown report of security status including:
- Dependabot alerts
- Recent vulnerability scans
- Week-over-week trends
- Action items

Usage:
    python scripts/security/weekly_report.py
    python scripts/security/weekly_report.py --output docs/security/weekly-report-2025-11-29.md
"""

import argparse
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any


class WeeklyReportGenerator:
    """Generate weekly security reports."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.report_date = datetime.now()
        self.data = {}

    def fetch_dependabot_alerts(self) -> List[Dict[str, Any]]:
        """
        Fetch Dependabot alerts from GitHub API.

        Returns:
            List of alert dictionaries
        """
        try:
            result = subprocess.run(
                [
                    "gh",
                    "api",
                    "repos/dreamseedai/dreamseed_monorepo/dependabot/alerts",
                    "--jq",
                    ".[] | {number, state, severity: .security_advisory.severity, package: .dependency.package.name, ecosystem: .dependency.package.ecosystem}",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Parse JSON lines
                alerts = []
                for line in result.stdout.strip().split("\n"):
                    if line:
                        alerts.append(json.loads(line))
                return alerts
            else:
                print(f"⚠️  Failed to fetch Dependabot alerts: {result.stderr}")
                return []

        except Exception as e:
            print(f"❌ Error fetching Dependabot alerts: {e}")
            return []

    def generate_report(self) -> str:
        """Generate markdown report."""
        alerts = self.fetch_dependabot_alerts()

        # Count by severity and state
        open_alerts = [a for a in alerts if a["state"] == "open"]
        critical = sum(1 for a in open_alerts if a["severity"] == "critical")
        high = sum(1 for a in open_alerts if a["severity"] == "high")
        medium = sum(1 for a in open_alerts if a["severity"] == "medium")
        low = sum(1 for a in open_alerts if a["severity"] == "low")

        # Count by ecosystem
        python_alerts = sum(1 for a in open_alerts if a["ecosystem"] == "pip")
        npm_alerts = sum(1 for a in open_alerts if a["ecosystem"] == "npm")

        report = f"""# 🔒 Weekly Security Report - {self.report_date.strftime('%Y-%m-%d')}

**Report Period**: {(self.report_date - timedelta(days=7)).strftime('%Y-%m-%d')} to {self.report_date.strftime('%Y-%m-%d')}

---

## 📊 Summary

### Dependabot Alerts (Open)
- **Total**: {len(open_alerts)}
  - 🔴 **Critical**: {critical}
  - 🟠 **High**: {high}
  - 🟡 **Medium**: {medium}
  - 🟢 **Low**: {low}

### By Ecosystem
- 🐍 **Python (pip)**: {python_alerts} alerts
- 📦 **npm**: {npm_alerts} alerts

---

## 🎯 Action Items

### High Priority (This Week)
"""

        # List critical and high severity alerts
        critical_high = [a for a in open_alerts if a["severity"] in ["critical", "high"]]
        if critical_high:
            for i, alert in enumerate(critical_high[:5], 1):
                severity_emoji = "🔴" if alert["severity"] == "critical" else "🟠"
                report += f"{i}. {severity_emoji} Update `{alert['package']}` ({alert['ecosystem']}) - #{alert['number']}\n"
        else:
            report += "✅ No critical or high severity vulnerabilities!\n"

        report += f"""
### Medium Priority (Next 2 Weeks)
- Review and merge pending Dependabot PRs
- Update dependencies with medium severity issues
- Review security best practices

---

## 📈 Trends

### Week-over-Week
- Open alerts: {len(open_alerts)} (need historical data)
- Dependabot PRs merged: (need historical data)
- New vulnerabilities discovered: (need historical data)

### Monthly Overview
- Average time to patch: (need historical data)
- Security updates applied: (need historical data)

---

## 🔗 Quick Links

- [Dependabot Dashboard](https://github.com/dreamseedai/dreamseed_monorepo/security/dependabot)
- [Security Advisories](https://github.com/dreamseedai/dreamseed_monorepo/security/advisories)
- [Vulnerability Alerts](https://github.com/dreamseedai/dreamseed_monorepo/security/dependabot)

---

## 📝 Detailed Alerts

### Open Alerts by Severity

#### Critical (🔴)
"""

        critical_alerts = [a for a in open_alerts if a["severity"] == "critical"]
        if critical_alerts:
            for alert in critical_alerts:
                report += f"- **{alert['package']}** ({alert['ecosystem']}) - #{alert['number']}\n"
        else:
            report += "✅ None\n"

        report += "\n#### High (🟠)\n"
        high_alerts = [a for a in open_alerts if a["severity"] == "high"]
        if high_alerts:
            for alert in high_alerts:
                report += f"- **{alert['package']}** ({alert['ecosystem']}) - #{alert['number']}\n"
        else:
            report += "✅ None\n"

        report += "\n#### Medium (🟡)\n"
        medium_alerts = [a for a in open_alerts if a["severity"] == "medium"]
        if medium_alerts:
            for alert in medium_alerts[:10]:  # Limit to 10
                report += f"- **{alert['package']}** ({alert['ecosystem']}) - #{alert['number']}\n"
            if len(medium_alerts) > 10:
                report += f"- ... and {len(medium_alerts) - 10} more\n"
        else:
            report += "✅ None\n"

        report += f"""
---

## 💡 Recommendations

1. **Immediate Actions** (Critical/High severity)
   - Review and merge Dependabot PRs for critical/high severity issues
   - Test updates in staging before production
   - Monitor application logs after updates

2. **Weekly Maintenance**
   - Review this report every Monday
   - Triage new Dependabot alerts
   - Update dependencies proactively

3. **Process Improvements**
   - Enable auto-merge for low-risk updates (patch versions)
   - Set up Slack notifications for critical alerts
   - Schedule quarterly dependency refresh

---

**Generated**: {datetime.now().isoformat()}  
**Tool**: `scripts/security/weekly_report.py`
"""

        return report

    def save_report(self, output_file: Path):
        """Save report to file."""
        report = self.generate_report()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(report)
        print(f"✅ Weekly report saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate weekly security report")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/security") / f"weekly-report-{datetime.now().strftime('%Y-%m-%d')}.md",
        help="Output file path",
    )

    args = parser.parse_args()

    # Find repository root
    repo_root = Path(__file__).parent.parent.parent.resolve()

    # Generate report
    generator = WeeklyReportGenerator(repo_root)
    generator.save_report(args.output)

    # Also print to stdout
    print("\n" + generator.generate_report())


if __name__ == "__main__":
    main()
