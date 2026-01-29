#!/usr/bin/env python3
"""
API 테스트 스크립트
서버가 실행 중일 때 API를 테스트합니다.

사용법:
1. 서버 실행: uvicorn app.main:app --reload
2. 테스트 실행: python scripts/test_api.py
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_root():
    """루트 엔드포인트 테스트"""
    print("=" * 60)
    print("1. 루트 엔드포인트 테스트")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_health():
    """헬스 체크 테스트"""
    print("\n" + "=" * 60)
    print("2. 헬스 체크 테스트")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/v1/analysis/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_quick_analysis():
    """빠른 분석 테스트 (페르소나 리뷰 없음)"""
    print("\n" + "=" * 60)
    print("3. 빠른 분석 테스트")
    print("=" * 60)

    test_code = '''
def calculate_sum(numbers):
    """숫자 리스트의 합계를 계산합니다."""
    total = 0
    for num in numbers:
        total += num
    return total


def main():
    numbers = [1, 2, 3, 4, 5]
    result = calculate_sum(numbers)
    print(f"Sum: {result}")


if __name__ == "__main__":
    main()
'''

    payload = {
        "code": test_code,
        "language": "python",
        "include_persona_review": False
    }

    print("요청 코드:")
    print(test_code[:200] + "...")

    response = requests.post(
        f"{BASE_URL}/api/v1/analysis/quick",
        json=payload
    )

    print(f"\nStatus: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n레벨: {result['level']} ({result['level_title']})")
        print(f"판정: {result['verdict']}")
        print(f"종합 점수: {result['overall_score']}")
        print(f"\n점수 상세:")
        for key, value in result['scores'].items():
            print(f"  - {key}: {value}")
        print(f"\n코드 리뷰: {result['code_review'][:200]}...")
        return True
    else:
        print(f"Error: {response.text}")
        return False


def test_full_analysis():
    """전체 분석 테스트 (페르소나 리뷰 포함)"""
    print("\n" + "=" * 60)
    print("4. 전체 분석 테스트 (페르소나 리뷰 포함)")
    print("=" * 60)

    # 취약점이 있는 코드 예시
    test_code = '''
def get_user_data(user_id):
    # SQL 인젝션 취약점 예시
    query = "SELECT * FROM users WHERE id = " + user_id
    result = execute_query(query)
    return result


def save_file(filename, content):
    # 경로 조작 취약점
    with open("/uploads/" + filename, "w") as f:
        f.write(content)
'''

    payload = {
        "code": test_code,
        "language": "auto",
        "include_persona_review": True
    }

    print("요청 코드 (취약점 포함):")
    print(test_code)

    print("\n분석 중... (페르소나 LLM 로딩으로 시간이 걸릴 수 있습니다)")

    response = requests.post(
        f"{BASE_URL}/api/v1/analysis/analyze",
        json=payload,
        timeout=300  # 5분 타임아웃
    )

    print(f"\nStatus: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n레벨: {result['level']} ({result['level_title']})")
        print(f"판정: {result['verdict']}")
        print(f"종합 점수: {result['overall_score']}")
        print(f"취약점 감지: {result['is_vulnerable']}")

        print(f"\n점수 상세:")
        for key, value in result['scores'].items():
            print(f"  - {key}: {value}")

        if result['issues']:
            print(f"\n발견된 이슈:")
            for issue in result['issues']:
                print(f"  - {issue}")

        print(f"\n안성재 쉐프의 리뷰:")
        print("-" * 40)
        print(result.get('persona_review', 'N/A'))
        print("-" * 40)

        return True
    else:
        print(f"Error: {response.text}")
        return False


def main():
    print("=" * 60)
    print("흑백개발자 API 테스트")
    print("=" * 60)
    print(f"서버 주소: {BASE_URL}")

    # 서버 연결 확인
    try:
        requests.get(f"{BASE_URL}/", timeout=5)
    except requests.exceptions.ConnectionError:
        print("\n❌ 서버에 연결할 수 없습니다!")
        print("   먼저 서버를 실행하세요: uvicorn app.main:app --reload")
        return

    results = {}

    results["root"] = test_root()
    results["health"] = test_health()

    print("\n" + "=" * 60)
    print("분석 테스트 옵션")
    print("=" * 60)
    print("1. 빠른 분석만 (페르소나 리뷰 없음)")
    print("2. 전체 분석 (페르소나 리뷰 포함 - 시간 오래 걸림)")
    print("3. 둘 다 테스트")
    print("4. 건너뛰기")

    choice = input("\n선택 (1-4): ").strip()

    if choice in ["1", "3"]:
        results["quick_analysis"] = test_quick_analysis()

    if choice in ["2", "3"]:
        results["full_analysis"] = test_full_analysis()

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    for name, passed in results.items():
        status = "✅ 성공" if passed else "❌ 실패"
        print(f"  {name}: {status}")


if __name__ == "__main__":
    main()
