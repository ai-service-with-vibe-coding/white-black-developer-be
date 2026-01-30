"""
레벨별 샘플 코드 테스트 스크립트

각 레벨(1-5)의 샘플 코드를 분석하여 점수와 레벨을 확인합니다.
"""

import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.models.code_reviewer import CodeReviewerModel
from app.utils.logger import get_logger

logger = get_logger(__name__)


def analyze_sample(file_path: str, model: CodeReviewerModel) -> dict:
    """샘플 파일 분석"""
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    result = model.get_quality_score(code)
    return result


def calculate_expected_level(score: float) -> int:
    """점수로 예상 레벨 계산"""
    if score >= 90:
        return 5
    elif score >= 75:
        return 4
    elif score >= 60:
        return 3
    elif score >= 45:
        return 2
    else:
        return 1


def main():
    print("=" * 60)
    print("레벨별 샘플 코드 분석 테스트")
    print("=" * 60)

    # 샘플 파일 경로
    samples_dir = os.path.join(os.path.dirname(__file__), "test_samples")
    samples = [
        ("level1_terrible.py", 1),
        ("level2_poor.py", 2),
        ("level3_average.py", 3),
        ("level4_good.py", 4),
        ("level5_excellent.py", 5),
    ]

    # 모델 로드
    print("\n모델 로딩 중...")
    try:
        model = CodeReviewerModel()
        print("모델 로드 완료!\n")
    except Exception as e:
        print(f"모델 로드 실패: {e}")
        print("\n[참고] GPU 없이 간단한 메트릭 분석만 수행합니다.\n")
        model = None

    results = []

    for filename, expected_level in samples:
        filepath = os.path.join(samples_dir, filename)
        print(f"\n{'='*50}")
        print(f"분석 중: {filename} (목표 레벨: {expected_level})")
        print(f"{'='*50}")

        if model:
            try:
                result = analyze_sample(filepath, model)
                quality_score = result.get("quality_score", 0)
                metrics = result.get("metrics", {})
                summary = result.get("summary", "")
            except Exception as e:
                print(f"분석 오류: {e}")
                quality_score = 0
                metrics = {}
                summary = ""
        else:
            # 모델 없이 간단한 분석
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()

            lines = code.split('\n')
            code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]

            metrics = {
                "total_lines": len(lines),
                "code_lines": len(code_lines),
                "max_line_length": max((len(l) for l in lines), default=0),
                "function_count": code.count("def "),
                "class_count": code.count("class "),
            }

            # 간단한 점수 계산
            score = 70.0
            if metrics["max_line_length"] > 120:
                score -= 15
            if metrics["function_count"] == 0 and metrics["code_lines"] > 50:
                score -= 10
            if metrics["function_count"] >= 5:
                score += 10
            if metrics["class_count"] >= 2:
                score += 5

            quality_score = max(0, min(100, score))
            summary = "(모델 없음)"

        actual_level = calculate_expected_level(quality_score)

        print(f"\n[결과]")
        print(f"  품질 점수: {quality_score:.1f}")
        print(f"  예상 레벨: {actual_level}")
        print(f"  목표 레벨: {expected_level}")
        print(f"  일치 여부: {'✓' if actual_level == expected_level else '✗'}")

        print(f"\n[메트릭]")
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")

        if summary and summary != "(모델 없음)":
            print(f"\n[AI 요약]")
            print(f"  {summary[:100]}...")

        results.append({
            "file": filename,
            "expected": expected_level,
            "actual": actual_level,
            "score": quality_score,
            "match": actual_level == expected_level
        })

    # 요약
    print("\n" + "=" * 60)
    print("테스트 요약")
    print("=" * 60)
    print(f"\n{'파일':<25} {'목표':<6} {'실제':<6} {'점수':<8} {'결과':<6}")
    print("-" * 55)

    match_count = 0
    for r in results:
        status = "✓ 성공" if r["match"] else "✗ 실패"
        if r["match"]:
            match_count += 1
        print(f"{r['file']:<25} {r['expected']:<6} {r['actual']:<6} {r['score']:<8.1f} {status}")

    print("-" * 55)
    print(f"일치율: {match_count}/{len(results)} ({match_count/len(results)*100:.0f}%)")

    # 레벨별 점수 범위 안내
    print("\n[레벨 기준]")
    print("  레벨 5: 90점 이상")
    print("  레벨 4: 75-89점")
    print("  레벨 3: 60-74점")
    print("  레벨 2: 45-59점")
    print("  레벨 1: 45점 미만")


if __name__ == "__main__":
    main()
