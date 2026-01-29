#!/usr/bin/env python3
"""
AI 모델 테스트 스크립트
GPU와 모델이 올바르게 작동하는지 확인
"""
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from app.utils.gpu_utils import check_gpu_available, get_gpu_memory_info


def test_gpu():
    """GPU 상태 테스트"""
    print("=" * 60)
    print("1. GPU 상태 확인")
    print("=" * 60)

    if not torch.cuda.is_available():
        print("❌ GPU를 사용할 수 없습니다!")
        print("   CUDA가 설치되어 있는지 확인하세요.")
        return False

    print(f"✅ GPU 사용 가능: {torch.cuda.get_device_name(0)}")

    memory_info = get_gpu_memory_info()
    if memory_info:
        print(f"   - Total VRAM: {memory_info['total']}")
        print(f"   - Allocated: {memory_info['allocated']}")
        print(f"   - Free: {memory_info['free']}")

    return True


def test_code_reviewer():
    """코드 리뷰 모델 테스트"""
    print("\n" + "=" * 60)
    print("2. Code Reviewer 모델 테스트")
    print("=" * 60)

    try:
        from app.ai.huggingface_client import get_hf_client

        client = get_hf_client()
        reviewer = client.get_code_reviewer()

        # 테스트 코드
        test_code = '''
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
'''

        print("테스트 코드:")
        print(test_code)
        print("\n분석 결과:")

        result = reviewer.get_quality_score(test_code)
        print(f"  - Quality Score: {result['quality_score']:.1f}")
        print(f"  - Review: {result['review'][:200]}...")

        print("\n✅ Code Reviewer 테스트 성공")
        return True

    except Exception as e:
        print(f"❌ Code Reviewer 테스트 실패: {e}")
        return False


def test_vulnerability_detector():
    """취약점 탐지 모델 테스트"""
    print("\n" + "=" * 60)
    print("3. Vulnerability Detector 모델 테스트")
    print("=" * 60)

    try:
        from app.ai.huggingface_client import get_hf_client

        client = get_hf_client()
        detector = client.get_vulnerability_detector()

        # 안전한 코드
        safe_code = '''
def greet(name):
    return f"Hello, {name}!"
'''

        # 잠재적 취약점 코드 (SQL 인젝션 가능성)
        vulnerable_code = '''
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return execute_query(query)
'''

        print("안전한 코드 테스트:")
        safe_result = detector.detect(safe_code)
        print(f"  - Vulnerable: {safe_result['vulnerable']}")
        print(f"  - Safety Score: {safe_result['score']:.1f}")

        print("\n취약한 코드 테스트:")
        vuln_result = detector.detect(vulnerable_code)
        print(f"  - Vulnerable: {vuln_result['vulnerable']}")
        print(f"  - Safety Score: {vuln_result['score']:.1f}")

        print("\n✅ Vulnerability Detector 테스트 성공")
        return True

    except Exception as e:
        print(f"❌ Vulnerability Detector 테스트 실패: {e}")
        return False


def test_persona_llm():
    """페르소나 LLM 테스트"""
    print("\n" + "=" * 60)
    print("4. Persona LLM (SOLAR-10.7B) 모델 테스트")
    print("=" * 60)
    print("⚠️  이 모델은 크기가 커서 로딩에 시간이 걸릴 수 있습니다...")

    try:
        from app.ai.huggingface_client import get_hf_client
        from app.ai.prompts.chef_ahn import CHEF_AHN_SYSTEM_PROMPT, build_review_prompt

        client = get_hf_client()
        llm = client.get_persona_llm()

        # 테스트 데이터
        scores = {
            "overall": 72.5,
            "security": 80.0,
            "quality": 70.0,
            "best_practices": 65.0,
            "complexity": 75.0,
            "documentation": 60.0,
        }
        issues = ["함수가 너무 길어요", "변수명이 명확하지 않아요"]

        user_prompt = build_review_prompt(level=3, scores=scores, issues=issues)

        print("리뷰 생성 중...")
        review = llm.generate_review(
            system_prompt=CHEF_AHN_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_new_tokens=300,
            temperature=0.8,
        )

        print("\n생성된 리뷰:")
        print("-" * 40)
        print(review)
        print("-" * 40)

        print("\n✅ Persona LLM 테스트 성공")
        return True

    except Exception as e:
        print(f"❌ Persona LLM 테스트 실패: {e}")
        return False


def test_preprocessor():
    """코드 전처리기 테스트"""
    print("\n" + "=" * 60)
    print("5. Code Preprocessor 테스트")
    print("=" * 60)

    try:
        from app.ai.processors.code_preprocessor import get_preprocessor

        preprocessor = get_preprocessor()

        # 현재 프로젝트를 테스트 대상으로 사용
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        print(f"스캔 대상: {project_root}")
        code_files = preprocessor.scan_repository(project_root)

        print(f"\n발견된 파일: {len(code_files)}개")

        if code_files:
            stats = preprocessor.get_language_stats(code_files)
            print(f"언어별 통계: {stats}")

            total_lines = preprocessor.get_total_lines(code_files)
            print(f"총 라인 수: {total_lines}")

            # 첫 번째 파일 청킹 테스트
            chunks = preprocessor.chunk_code(code_files[0])
            print(f"\n첫 번째 파일 ({code_files[0].relative_path}) 청크 수: {len(chunks)}")

        print("\n✅ Preprocessor 테스트 성공")
        return True

    except Exception as e:
        print(f"❌ Preprocessor 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("흑백개발자 AI 모델 테스트")
    print("=" * 60)

    results = {}

    # GPU 테스트
    results["GPU"] = test_gpu()

    if not results["GPU"]:
        print("\n❌ GPU를 사용할 수 없어 나머지 테스트를 건너뜁니다.")
        return

    # 전처리기 테스트 (GPU 불필요)
    results["Preprocessor"] = test_preprocessor()

    # 모델 테스트 메뉴
    print("\n" + "=" * 60)
    print("모델 테스트 옵션")
    print("=" * 60)
    print("1. Code Reviewer만 테스트")
    print("2. Vulnerability Detector만 테스트")
    print("3. Persona LLM만 테스트 (시간 오래 걸림)")
    print("4. 모든 모델 테스트")
    print("5. 건너뛰기")

    choice = input("\n선택 (1-5): ").strip()

    if choice == "1":
        results["CodeReviewer"] = test_code_reviewer()
    elif choice == "2":
        results["VulnerabilityDetector"] = test_vulnerability_detector()
    elif choice == "3":
        results["PersonaLLM"] = test_persona_llm()
    elif choice == "4":
        results["CodeReviewer"] = test_code_reviewer()
        results["VulnerabilityDetector"] = test_vulnerability_detector()
        results["PersonaLLM"] = test_persona_llm()

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    for name, passed in results.items():
        status = "✅ 성공" if passed else "❌ 실패"
        print(f"  {name}: {status}")

    # GPU 메모리 최종 상태
    memory_info = get_gpu_memory_info()
    if memory_info:
        print(f"\n최종 GPU 메모리 사용량: {memory_info['allocated']}")


if __name__ == "__main__":
    main()
