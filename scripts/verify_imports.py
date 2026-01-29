#!/usr/bin/env python3
"""
Import 검증 스크립트
모든 모듈이 정상적으로 import 되는지 확인
"""
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def verify_imports():
    """모든 import 검증"""
    print("=" * 60)
    print("Import 검증")
    print("=" * 60)

    errors = []

    # 1. Config
    print("\n1. Config...")
    try:
        from app.config import settings
        print(f"   ✅ settings loaded (APP_NAME: {settings.APP_NAME})")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(("config", str(e)))

    # 2. Utils
    print("\n2. Utils...")
    try:
        from app.utils.logger import get_logger
        from app.utils.gpu_utils import check_gpu_available, get_gpu_memory_info
        print("   ✅ logger, gpu_utils")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(("utils", str(e)))

    # 3. AI Models
    print("\n3. AI Models...")
    try:
        from app.ai.models import (
            CodeReviewerModel,
            VulnerabilityDetector,
            PersonaLLM,
        )
        print("   ✅ CodeReviewerModel, VulnerabilityDetector, PersonaLLM")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(("ai.models", str(e)))

    # 4. AI Processors
    print("\n4. AI Processors...")
    try:
        from app.ai.processors import (
            CodePreprocessor,
            CodeFile,
            CodeChunk,
            get_preprocessor,
            AnalysisOrchestrator,
            AnalysisStage,
            get_orchestrator,
        )
        print("   ✅ CodePreprocessor, AnalysisOrchestrator")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(("ai.processors", str(e)))

    # 5. AI Client
    print("\n5. AI Client...")
    try:
        from app.ai import HuggingFaceClient, get_hf_client
        print("   ✅ HuggingFaceClient, get_hf_client")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(("ai", str(e)))

    # 6. AI Prompts
    print("\n6. AI Prompts...")
    try:
        from app.ai.prompts.chef_ahn import CHEF_AHN_SYSTEM_PROMPT, build_review_prompt
        print("   ✅ CHEF_AHN_SYSTEM_PROMPT, build_review_prompt")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(("ai.prompts", str(e)))

    # 7. Services
    print("\n7. Services...")
    try:
        from app.services import (
            ScoringService,
            get_scoring_service,
            PersonaService,
            get_persona_service,
            AnalysisService,
            get_analysis_service,
        )
        print("   ✅ ScoringService, PersonaService, AnalysisService")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(("services", str(e)))

    # 8. Database Models
    print("\n8. Database Models...")
    try:
        from app.db.models import User, Repository, Analysis, AnalysisResult
        print("   ✅ User, Repository, Analysis, AnalysisResult")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(("db.models", str(e)))

    # 결과 요약
    print("\n" + "=" * 60)
    print("결과 요약")
    print("=" * 60)

    if errors:
        print(f"\n❌ {len(errors)}개 모듈에서 오류 발생:")
        for module, error in errors:
            print(f"   - {module}: {error}")
        return False
    else:
        print("\n✅ 모든 모듈이 정상적으로 import 되었습니다!")
        return True


def main():
    success = verify_imports()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
