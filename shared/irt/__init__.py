"""
IRT (Item Response Theory) 패키지

이 패키지는 IRT 모델 캘리브레이션, 분석, 리포팅 기능을 제공합니다.

Note: 핵심 IRT 수학 함수들은 shared.irt 모듈(irt.py)에 정의되어 있습니다.
      순환 import를 피하기 위해 이 __init__.py는 비어있습니다.
      IRT 수학 함수를 사용하려면 다음과 같이 import하세요:

      import shared.irt as irt_funcs
      irt_funcs.eap_theta(...)
"""

__all__ = []
