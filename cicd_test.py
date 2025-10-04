#!/usr/bin/env python3
"""
DreamSeed CI/CD 파이프라인 테스트
"""
import subprocess
import os
import json
import time
from datetime import datetime

class CICDTester:
    """CI/CD 파이프라인 테스트 클래스"""
    
    def __init__(self):
        self.test_results = []
    
    def log_test(self, test_name, success, details=""):
        """테스트 결과 로깅"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
    
    def test_code_quality_tools(self):
        """코드 품질 도구 테스트"""
        print("\n🔍 코드 품질 도구 테스트")
        
        tools = [
            ("Black", "black --check ."),
            ("isort", "isort --check-only ."),
            ("Flake8", "flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics"),
            ("MyPy", "mypy api/ --ignore-missing-imports"),
            ("Bandit", "bandit -r . -f json -o bandit-report.json"),
            ("Safety", "safety check --json --output safety-report.json")
        ]
        
        for tool_name, command in tools:
            try:
                result = subprocess.run(command.split(), capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    self.log_test(f"{tool_name} 검사", True, "통과")
                else:
                    self.log_test(f"{tool_name} 검사", False, f"실패: {result.stderr[:100]}")
            except subprocess.TimeoutExpired:
                self.log_test(f"{tool_name} 검사", False, "타임아웃")
            except Exception as e:
                self.log_test(f"{tool_name} 검사", False, f"오류: {e}")
    
    def test_unit_tests(self):
        """단위 테스트 실행"""
        print("\n🧪 단위 테스트 실행")
        
        try:
            # pytest 설치 확인
            result = subprocess.run(["python", "-m", "pytest", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                self.log_test("pytest 설치", False, "pytest가 설치되지 않음")
                return False
            
            self.log_test("pytest 설치", True, "정상")
            
            # 단위 테스트 실행
            test_command = [
                "python", "-m", "pytest", 
                "tests/test_api.py", 
                "-v", 
                "--tb=short",
                "--timeout=30"
            ]
            
            result = subprocess.run(test_command, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.log_test("단위 테스트", True, "모든 테스트 통과")
                return True
            else:
                self.log_test("단위 테스트", False, f"일부 테스트 실패: {result.stdout[-200:]}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_test("단위 테스트", False, "테스트 타임아웃")
            return False
        except Exception as e:
            self.log_test("단위 테스트", False, f"오류: {e}")
            return False
    
    def test_docker_build(self):
        """Docker 빌드 테스트"""
        print("\n🐳 Docker 빌드 테스트")
        
        try:
            # Docker 설치 확인
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                self.log_test("Docker 설치", False, "Docker가 설치되지 않음")
                return False
            
            self.log_test("Docker 설치", True, "정상")
            
            # Docker 이미지 빌드
            build_command = [
                "docker", "build", 
                "-t", "dreamseed:test",
                "."
            ]
            
            result = subprocess.run(build_command, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log_test("Docker 빌드", True, "이미지 빌드 성공")
                
                # Docker 이미지 테스트
                test_command = [
                    "docker", "run", 
                    "--rm", 
                    "-d", 
                    "--name", "dreamseed-test",
                    "-p", "8003:8002",
                    "dreamseed:test"
                ]
                
                result = subprocess.run(test_command, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    # 컨테이너 헬스체크
                    time.sleep(10)
                    health_result = subprocess.run([
                        "curl", "-f", "http://localhost:8003/healthz"
                    ], capture_output=True, text=True, timeout=10)
                    
                    if health_result.returncode == 0:
                        self.log_test("Docker 컨테이너", True, "헬스체크 통과")
                        
                        # 컨테이너 정리
                        subprocess.run(["docker", "stop", "dreamseed-test"], 
                                     capture_output=True, timeout=10)
                        subprocess.run(["docker", "rm", "dreamseed-test"], 
                                     capture_output=True, timeout=10)
                        
                        return True
                    else:
                        self.log_test("Docker 컨테이너", False, "헬스체크 실패")
                        subprocess.run(["docker", "stop", "dreamseed-test"], 
                                     capture_output=True, timeout=10)
                        subprocess.run(["docker", "rm", "dreamseed-test"], 
                                     capture_output=True, timeout=10)
                        return False
                else:
                    self.log_test("Docker 컨테이너", False, "컨테이너 시작 실패")
                    return False
            else:
                self.log_test("Docker 빌드", False, f"빌드 실패: {result.stderr[-200:]}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_test("Docker 빌드", False, "빌드 타임아웃")
            return False
        except Exception as e:
            self.log_test("Docker 빌드", False, f"오류: {e}")
            return False
    
    def test_deployment_scripts(self):
        """배포 스크립트 테스트"""
        print("\n🚀 배포 스크립트 테스트")
        
        scripts = [
            "deploy_staging.sh",
            "deploy_production.sh", 
            "rollback.sh"
        ]
        
        for script in scripts:
            if os.path.exists(script):
                # 스크립트 실행 권한 확인
                if os.access(script, os.X_OK):
                    self.log_test(f"{script} 권한", True, "실행 가능")
                else:
                    self.log_test(f"{script} 권한", False, "실행 권한 없음")
                
                # 스크립트 문법 검사 (bash -n)
                try:
                    result = subprocess.run(["bash", "-n", script], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        self.log_test(f"{script} 문법", True, "문법 오류 없음")
                    else:
                        self.log_test(f"{script} 문법", False, f"문법 오류: {result.stderr}")
                except Exception as e:
                    self.log_test(f"{script} 문법", False, f"검사 오류: {e}")
            else:
                self.log_test(f"{script} 존재", False, "파일 없음")
    
    def test_github_workflows(self):
        """GitHub Actions 워크플로우 테스트"""
        print("\n⚙️ GitHub Actions 워크플로우 테스트")
        
        workflow_files = [
            ".github/workflows/ci.yml",
            ".github/workflows/cd.yml"
        ]
        
        for workflow_file in workflow_files:
            if os.path.exists(workflow_file):
                # YAML 문법 검사
                try:
                    result = subprocess.run([
                        "python", "-c", 
                        "import yaml; yaml.safe_load(open('" + workflow_file + "'))"
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        self.log_test(f"{workflow_file} YAML", True, "문법 정상")
                    else:
                        self.log_test(f"{workflow_file} YAML", False, f"문법 오류: {result.stderr}")
                except Exception as e:
                    self.log_test(f"{workflow_file} YAML", False, f"검사 오류: {e}")
            else:
                self.log_test(f"{workflow_file} 존재", False, "파일 없음")
    
    def test_configuration_files(self):
        """설정 파일 테스트"""
        print("\n⚙️ 설정 파일 테스트")
        
        config_files = [
            "pyproject.toml",
            ".pre-commit-config.yaml",
            "docker-compose.yml",
            "nginx.conf",
            "gunicorn.conf.py"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                # 파일 크기 확인 (너무 크지 않은지)
                file_size = os.path.getsize(config_file)
                if file_size < 1024 * 1024:  # 1MB 미만
                    self.log_test(f"{config_file} 크기", True, f"{file_size} bytes")
                else:
                    self.log_test(f"{config_file} 크기", False, f"너무 큼: {file_size} bytes")
                
                # 파일 읽기 가능 확인
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.log_test(f"{config_file} 읽기", True, "읽기 가능")
                except Exception as e:
                    self.log_test(f"{config_file} 읽기", False, f"읽기 오류: {e}")
            else:
                self.log_test(f"{config_file} 존재", False, "파일 없음")
    
    def test_dependencies(self):
        """의존성 테스트"""
        print("\n📦 의존성 테스트")
        
        try:
            # requirements.txt 확인
            if os.path.exists("requirements.txt"):
                with open("requirements.txt", 'r') as f:
                    requirements = f.read().strip().split('\n')
                
                self.log_test("requirements.txt", True, f"{len(requirements)}개 의존성")
                
                # 각 의존성 설치 테스트
                for req in requirements[:5]:  # 처음 5개만 테스트
                    if req.strip() and not req.startswith('#'):
                        try:
                            result = subprocess.run([
                                "python", "-c", f"import {req.split('==')[0].split('>=')[0].split('<=')[0].replace('-', '_')}"
                            ], capture_output=True, text=True, timeout=10)
                            
                            if result.returncode == 0:
                                self.log_test(f"의존성 {req.split('==')[0]}", True, "정상")
                            else:
                                self.log_test(f"의존성 {req.split('==')[0]}", False, "설치 안됨")
                        except Exception as e:
                            self.log_test(f"의존성 {req.split('==')[0]}", False, f"오류: {e}")
            else:
                self.log_test("requirements.txt", False, "파일 없음")
                
        except Exception as e:
            self.log_test("의존성 테스트", False, f"오류: {e}")
    
    def run_all_tests(self):
        """모든 CI/CD 테스트 실행"""
        print("🚀 DreamSeed CI/CD 파이프라인 테스트 시작")
        print("=" * 60)
        
        self.test_code_quality_tools()
        self.test_unit_tests()
        self.test_docker_build()
        self.test_deployment_scripts()
        self.test_github_workflows()
        self.test_configuration_files()
        self.test_dependencies()
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 CI/CD 파이프라인 테스트 결과 요약")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"총 테스트: {total}")
        print(f"통과: {passed}")
        print(f"실패: {total - passed}")
        print(f"성공률: {(passed/total)*100:.1f}%")
        
        # 실패한 테스트 목록
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("\n❌ 실패한 테스트:")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['details']}")
        
        # 결과를 JSON 파일로 저장
        with open('cicd_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 결과가 cicd_test_results.json에 저장되었습니다.")
        
        return passed == total

if __name__ == "__main__":
    tester = CICDTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 모든 CI/CD 테스트 통과!")
        exit(0)
    else:
        print("\n💥 일부 CI/CD 테스트 실패!")
        exit(1)

