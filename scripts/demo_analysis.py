#!/usr/bin/env python3
"""
전체 분석 파이프라인 데모
현재 프로젝트를 분석하여 결과 확인
"""
import sys
import os
import asyncio
import json

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.processors.analysis_orchestrator import AnalysisStage


async def progress_callback(stage: AnalysisStage, progress: int):
    """진행 상황 출력"""
    stage_names = {
        AnalysisStage.PREPROCESSING: "전처리",
        AnalysisStage.CODE_REVIEW: "코드 리뷰",
        AnalysisStage.VULNERABILITY_SCAN: "취약점 스캔",
        AnalysisStage.SCORING: "점수 계산",
        AnalysisStage.REVIEW_GENERATION: "리뷰 생성",
        AnalysisStage.COMPLETED: "완료",
        AnalysisStage.FAILED: "실패",
    }
    print(f"  [{stage_names.get(stage, stage)}] {progress}%")


async def run_demo():
    """데모 실행"""
    print("=" * 60)
    print("흑백개발자 - 전체 분석 파이프라인 데모")
    print("=" * 60)

    # GPU 확인
    import torch
    if not torch.cuda.is_available():
        print("❌ GPU를 사용할 수 없습니다!")
        return

    print(f"✅ GPU: {torch.cuda.get_device_name(0)}")

    # 분석 대상 선택
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print(f"\n분석 대상: {project_root}")
    print("\n옵션:")
    print("1. 빠른 분석 (페르소나 리뷰 없이)")
    print("2. 전체 분석 (페르소나 리뷰 포함 - 시간 오래 걸림)")

    choice = input("\n선택 (1-2): ").strip()

    from app.services.analysis_service import get_analysis_service

    service = get_analysis_service()

    print("\n" + "=" * 60)
    print("분석 시작...")
    print("=" * 60)

    if choice == "1":
        # 빠른 분석
        result = await service.quick_analyze(
            repo_path=project_root,
            repo_name="white-black-developer-be",
        )
        print("\n" + "=" * 60)
        print("빠른 분석 결과")
        print("=" * 60)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        # 전체 분석
        result = await service.analyze_repository(
            repo_path=project_root,
            repo_name="white-black-developer-be",
            progress_callback=progress_callback,
            generate_persona_review=True,
        )

        print("\n" + "=" * 60)
        print("전체 분석 결과")
        print("=" * 60)

        print(f"\n📊 레벨: {result.level} ({result.level_title})")
        print(f"📈 종합 점수: {result.overall_score:.1f}/100")
        print(f"🎯 판정: {result.verdict}")

        print("\n점수 상세:")
        for category, score in result.scores.items():
            print(f"  - {category}: {score:.1f}")

        print(f"\n📁 분석 파일: {result.total_files}개")
        print(f"📝 총 라인: {result.total_lines}줄")
        print(f"💻 언어: {result.language_stats}")

        if result.critical_issues:
            print(f"\n🚨 심각한 이슈 ({len(result.critical_issues)}개):")
            for issue in result.critical_issues[:5]:
                print(f"  - {issue}")

        if result.warnings:
            print(f"\n⚠️  경고 ({len(result.warnings)}개):")
            for warning in result.warnings[:5]:
                print(f"  - {warning}")

        print("\n" + "=" * 60)
        print("안성재 쉐프의 리뷰")
        print("=" * 60)
        print(result.persona_review)

    # GPU 메모리 사용량
    from app.utils.gpu_utils import get_gpu_memory_info
    memory_info = get_gpu_memory_info()
    if memory_info:
        print(f"\n최종 GPU 메모리: {memory_info['allocated']} / {memory_info['total']}")


def main():
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
