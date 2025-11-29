"""회귀 테스트 - SVG 해시 & MathSpeak 검증"""
import subprocess
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
GOLDEN = ROOT / "goldenset" / "goldenset.sample.jsonl"
NODE = ROOT / "node"

def test_snapshots_hash_and_speech():
    """Node.js 스냅샷 체크 실행"""
    result = subprocess.run(
        ["npm", "run", "snapshot:check", "--silent"],
        cwd=NODE,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        assert False, "Snapshot check failed"
    
    assert result.returncode == 0, "Snapshot check passed"
