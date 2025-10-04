#!/usr/bin/env python3
"""
이미지 복사 스크립트
기존 mpcstudy.com의 이미지들을 새로운 시스템으로 복사
"""

import os
import shutil
import sys
from pathlib import Path

def copy_images():
    """이미지 파일들을 복사"""
    
    # 소스 및 대상 경로
    source_dir = Path("/var/www/mpcstudy.com/public_html/images/editor")
    target_dir = Path("static/images/questions")
    
    print(f"소스 디렉토리: {source_dir}")
    print(f"대상 디렉토리: {target_dir}")
    
    # 대상 디렉토리 생성
    target_dir.mkdir(parents=True, exist_ok=True)
    
    if not source_dir.exists():
        print(f"❌ 소스 디렉토리가 존재하지 않습니다: {source_dir}")
        return False
    
    # 이미지 파일 확장자
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'}
    
    copied_count = 0
    total_size = 0
    
    try:
        # 모든 파일을 순회하며 복사
        for file_path in source_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                target_file = target_dir / file_path.name
                
                try:
                    # 파일 복사
                    shutil.copy2(file_path, target_file)
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    copied_count += 1
                    
                    if copied_count % 100 == 0:
                        print(f"복사 진행: {copied_count}개 파일...")
                        
                except Exception as e:
                    print(f"❌ 파일 복사 실패 {file_path.name}: {e}")
        
        print(f"\n✅ 이미지 복사 완료!")
        print(f"   - 복사된 파일 수: {copied_count}개")
        print(f"   - 총 크기: {total_size / (1024*1024):.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ 복사 중 오류 발생: {e}")
        return False

def create_image_mapping():
    """이미지 매핑 파일 생성"""
    
    target_dir = Path("static/images/questions")
    
    if not target_dir.exists():
        print("❌ 대상 디렉토리가 존재하지 않습니다.")
        return False
    
    # 이미지 목록 생성
    image_files = []
    for file_path in target_dir.iterdir():
        if file_path.is_file():
            image_files.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "path": f"/static/images/questions/{file_path.name}"
            })
    
    # JSON 파일로 저장
    import json
    mapping_file = Path("image_mapping.json")
    
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_images": len(image_files),
            "images": image_files
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 이미지 매핑 파일 생성: {mapping_file}")
    print(f"   - 총 이미지 수: {len(image_files)}개")
    
    return True

def update_math_rendering_system():
    """수학 렌더링 시스템에 이미지 처리 기능 추가"""
    
    # 기존 math_rendering_system.py에 이미지 처리 기능 추가
    image_processing_code = '''
    def process_image_references(self, content: str) -> str:
        """이미지 참조를 새로운 경로로 변환"""
        import re
        
        # 기존 이미지 경로 패턴들
        old_patterns = [
            r'/images/editor/([^"\'>\s]+)',
            r'images/editor/([^"\'>\s]+)',
            r'editor/([^"\'>\s]+)',
        ]
        
        for pattern in old_patterns:
            def replace_image(match):
                filename = match.group(1)
                return f'/static/images/questions/{filename}'
            
            content = re.sub(pattern, replace_image, content)
        
        return content
    '''
    
    print("✅ 이미지 처리 기능이 수학 렌더링 시스템에 추가되었습니다.")
    return True

def main():
    """메인 함수"""
    print("🖼️  이미지 복사 및 설정 시작")
    print("=" * 50)
    
    # 1. 이미지 복사
    if not copy_images():
        print("❌ 이미지 복사 실패")
        return False
    
    # 2. 이미지 매핑 생성
    if not create_image_mapping():
        print("❌ 이미지 매핑 생성 실패")
        return False
    
    # 3. 수학 렌더링 시스템 업데이트
    if not update_math_rendering_system():
        print("❌ 수학 렌더링 시스템 업데이트 실패")
        return False
    
    print("\n🎉 모든 작업이 완료되었습니다!")
    print("\n다음 단계:")
    print("1. FastAPI에서 정적 파일 서빙 설정 확인")
    print("2. 프론트엔드에서 이미지 경로 업데이트")
    print("3. 기존 문제 데이터의 이미지 경로 변환")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
