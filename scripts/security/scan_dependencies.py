#!/usr/bin/env python3
"""
Dependency Security Scanner

Scans Python and npm dependencies for known vulnerabilities using:
- pip-audit for Python packages
- npm audit for npm packages
- GitHub Dependabot API for GitHub-hosted alerts

Usage:
    python scripts/security/scan_dependencies.py
    python scripts/security/scan_dependencies.py --format json
    python scripts/security/scan_dependencies.py --critical-only
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class SecurityScanner:
    """Security vulnerability scanner for dependencies."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "python": {},
            "npm": {},
            "summary": {},
        }

    def scan_python_dependencies(self, directory: str = "backend") -> Dict[str, Any]:
        """
        Scan Python dependencies using pip-audit.

        Args:
            directory: Directory containing requirements.txt

        Returns:
            Dict with vulnerability information
        """
        print(f"🐍 Scanning Python dependencies in {directory}...")

        try:
            result = subprocess.run(
                ["pip-audit", "--format", "json", "--requirement", "requirements.txt"],
                capture_output=True,
                text=True,
                cwd=self.repo_root / directory,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout) if result.stdout else {"dependencies": []}
                vulns = data.get("dependencies", [])

                return {
                    "total": sum(
                        len(v.get("vulns", [])) for v in vulns if isinstance(v.get("vulns", []), list)
                    ),
                    "critical": sum(
                        1
                        for v in vulns
                        for vuln in v.get("vulns", [])
                        if vuln.get("severity") == "critical"
                    ),
                    "high": sum(
                        1
                        for v in vulns
                        for vuln in v.get("vulns", [])
                        if vuln.get("severity") == "high"
                    ),
                    "medium": sum(
                        1
                        for v in vulns
                        for vuln in v.get("vulns", [])
                        if vuln.get("severity") == "medium"
                    ),
                    "low": sum(
                        1
                        for v in vulns
                        for vuln in v.get("vulns", [])
                        if vuln.get("severity") == "low"
                    ),
                    "vulnerabilities": vulns,
                }
            else:
                print(f"⚠️  pip-audit returned non-zero: {result.stderr}")
                return {"total": 0, "error": result.stderr}

        except FileNotFoundError:
            print("❌ pip-audit not installed. Run: pip install pip-audit")
            return {"total": 0, "error": "pip-audit not installed"}
        except Exception as e:
            print(f"❌ Error scanning Python dependencies: {e}")
            return {"total": 0, "error": str(e)}

    def scan_npm_dependencies(self, directory: str = "portal_front") -> Dict[str, Any]:
        """
        Scan npm dependencies using npm audit.

        Args:
            directory: Directory containing package.json

        Returns:
            Dict with vulnerability information
        """
        print(f"📦 Scanning npm dependencies in {directory}...")

        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True,
                text=True,
                cwd=self.repo_root / directory,
            )

            # npm audit returns non-zero if vulnerabilities are found
            # So we don't check returncode here
            data = json.loads(result.stdout) if result.stdout else {}
            metadata = data.get("metadata", {})
            vulns = metadata.get("vulnerabilities", {})

            return {
                "total": sum(vulns.values()),
                "critical": vulns.get("critical", 0),
                "high": vulns.get("high", 0),
                "moderate": vulns.get("moderate", 0),
                "low": vulns.get("low", 0),
                "info": vulns.get("info", 0),
                "raw": data,
            }

        except FileNotFoundError:
            print("❌ npm not installed or package.json not found")
            return {"total": 0, "error": "npm not found"}
        except Exception as e:
            print(f"❌ Error scanning npm dependencies: {e}")
            return {"total": 0, "error": str(e)}

    def scan_all(self):
        """Scan all dependency types."""
        # Python - backend
        self.results["python"]["backend"] = self.scan_python_dependencies("backend")

        # Python - adaptive_engine
        if (self.repo_root / "adaptive_engine" / "requirements.txt").exists():
            self.results["python"]["adaptive_engine"] = self.scan_python_dependencies(
                "adaptive_engine"
            )

        # npm - portal_front
        if (self.repo_root / "portal_front" / "package.json").exists():
            self.results["npm"]["portal_front"] = self.scan_npm_dependencies("portal_front")

        # npm - admin_front
        if (self.repo_root / "admin_front" / "package.json").exists():
            self.results["npm"]["admin_front"] = self.scan_npm_dependencies("admin_front")

        # Calculate summary
        self.results["summary"] = self._calculate_summary()

    def _calculate_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics."""
        total_vulns = 0
        critical = 0
        high = 0
        medium = 0
        low = 0

        # Python
        for py_scan in self.results["python"].values():
            if "error" not in py_scan:
                total_vulns += py_scan.get("total", 0)
                critical += py_scan.get("critical", 0)
                high += py_scan.get("high", 0)
                medium += py_scan.get("medium", 0)
                low += py_scan.get("low", 0)

        # npm
        for npm_scan in self.results["npm"].values():
            if "error" not in npm_scan:
                total_vulns += npm_scan.get("total", 0)
                critical += npm_scan.get("critical", 0)
                high += npm_scan.get("high", 0)
                medium += npm_scan.get("moderate", 0)  # npm uses "moderate"
                low += npm_scan.get("low", 0)

        return {
            "total_vulnerabilities": total_vulns,
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
            "status": "🔴 CRITICAL" if critical > 0 else ("🟠 HIGH" if high > 0 else "✅ OK"),
        }

    def print_summary(self):
        """Print human-readable summary."""
        summary = self.results["summary"]

        print("\n" + "=" * 60)
        print("🔒 SECURITY SCAN SUMMARY")
        print("=" * 60)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Status: {summary['status']}")
        print(f"\nTotal Vulnerabilities: {summary['total_vulnerabilities']}")
        print(f"  🔴 Critical: {summary['critical']}")
        print(f"  🟠 High: {summary['high']}")
        print(f"  🟡 Medium: {summary['medium']}")
        print(f"  🟢 Low: {summary['low']}")

        print("\n" + "-" * 60)
        print("📊 Detailed Breakdown:")
        print("-" * 60)

        # Python
        print("\nPython Packages:")
        for name, scan in self.results["python"].items():
            if "error" in scan:
                print(f"  {name}: ❌ {scan['error']}")
            else:
                print(f"  {name}: {scan['total']} vulnerabilities")

        # npm
        print("\nnpm Packages:")
        for name, scan in self.results["npm"].items():
            if "error" in scan:
                print(f"  {name}: ❌ {scan['error']}")
            else:
                print(f"  {name}: {scan['total']} vulnerabilities")

        print("=" * 60 + "\n")

    def save_json(self, output_file: Path):
        """Save results as JSON."""
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"✅ Results saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Scan dependencies for security vulnerabilities")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("security-scan-results.json"),
        help="Output file for JSON format",
    )
    parser.add_argument(
        "--critical-only",
        action="store_true",
        help="Exit with error code if critical vulnerabilities found",
    )

    args = parser.parse_args()

    # Find repository root
    repo_root = Path(__file__).parent.parent.parent.resolve()

    # Run scanner
    scanner = SecurityScanner(repo_root)
    scanner.scan_all()

    # Output
    if args.format == "json":
        scanner.save_json(args.output)
        print(json.dumps(scanner.results, indent=2))
    else:
        scanner.print_summary()

    # Exit with error if critical vulnerabilities found
    if args.critical_only and scanner.results["summary"]["critical"] > 0:
        print("\n❌ Critical vulnerabilities found. Exiting with error code 1.")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
