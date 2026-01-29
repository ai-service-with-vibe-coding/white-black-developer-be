# 흑백개발자 백엔드 프로젝트 구조 계획 (FastAPI)

## 1. 프로젝트 구조

```
white-black-developer-be/
├── app/
│   ├── main.py                  # FastAPI 애플리케이션 진입점
│   ├── config.py                # 설정 관리 (Pydantic Settings)
│   ├── dependencies.py          # 의존성 주입
│   │
│   ├── api/                     # API 라우터
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── github.py
│   │   │   ├── analysis.py
│   │   │   └── reports.py
│   │
│   ├── core/                    # 핵심 기능
│   │   ├── __init__.py
│   │   ├── security.py          # JWT, 암호화
│   │   ├── github_oauth.py      # GitHub OAuth 처리
│   │   └── rate_limiter.py      # Rate limiting
│   │
│   ├── db/                      # 데이터베이스
│   │   ├── __init__.py
│   │   ├── base.py              # SQLAlchemy Base
│   │   ├── session.py           # DB 세션 관리
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── user.py
│   │       ├── repository.py
│   │       ├── analysis.py
│   │       └── analysis_result.py
│   │
│   ├── schemas/                 # Pydantic 스키마
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── repository.py
│   │   ├── analysis.py
│   │   └── report.py
│   │
│   ├── services/                # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── github_service.py
│   │   ├── analysis_service.py
│   │   ├── scoring_service.py
│   │   ├── persona_service.py
│   │   └── report_service.py
│   │
│   ├── ai/                      # AI 모델 연동
│   │   ├── __init__.py
│   │   ├── huggingface_client.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── code_reviewer.py
│   │   │   ├── codebert.py
│   │   │   ├── vulnerability_detector.py
│   │   │   ├── starcoder.py
│   │   │   └── codellama.py
│   │   ├── processors/
│   │   │   ├── __init__.py
│   │   │   ├── code_preprocessor.py
│   │   │   └── analysis_orchestrator.py
│   │   └── prompts/
│   │       ├── __init__.py
│   │       └── chef_ahn.py
│   │
│   ├── tasks/                   # Celery 백그라운드 작업
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   └── analysis_tasks.py
│   │
│   ├── middleware/              # 미들웨어
│   │   ├── __init__.py
│   │   ├── auth_middleware.py
│   │   └── logging_middleware.py
│   │
│   └── utils/                   # 유틸리티
│       ├── __init__.py
│       ├── logger.py
│       ├── encryption.py
│       └── code_parser.py
│
├── alembic/                     # 데이터베이스 마이그레이션
│   ├── env.py
│   ├── versions/
│   └── alembic.ini
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/
│   ├── init_db.py
│   └── seed_data.py
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml             # Poetry 의존성 관리
├── requirements.txt           # 또는 pip requirements
├── PRD.md
├── PROJECT_PLAN.md
├── CLAUDE.md
└── README.md
```

## 2. 핵심 기술 스택 상세

### 2.1 FastAPI
**선택 이유:**
- 빠른 성능 (Starlette 기반)
- 자동 API 문서 생성 (Swagger UI, ReDoc)
- Pydantic을 통한 데이터 검증
- 비동기 지원 (async/await)
- Python 네이티브로 Hugging Face 통합 용이

### 2.2 데이터베이스
**PostgreSQL + SQLAlchemy 2.0**

**모델 예시:**
```python
# app/db/models/user.py
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    github_id = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=False)
    email = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    access_token = Column(Text, nullable=False)  # 암호화 저장
    refresh_token = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    analyses = relationship("Analysis", back_populates="user")


# app/db/models/analysis.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum

class AnalysisStatus(enum.Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    ANALYZING = "analyzing"
    GENERATING_REVIEW = "generating_review"
    COMPLETED = "completed"
    FAILED = "failed"

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="analyses")
    repository = relationship("Repository")
    result = relationship("AnalysisResult", back_populates="analysis", uselist=False)


# app/db/models/analysis_result.py
from sqlalchemy import Column, String, Integer, Float, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id"), unique=True, nullable=False)
    level = Column(Integer, nullable=False)
    overall_score = Column(Float, nullable=False)
    security_score = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=False)
    complexity_score = Column(Float, nullable=False)
    documentation_score = Column(Float, nullable=False)
    review_text = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis = relationship("Analysis", back_populates="result")
```

### 2.3 Celery + Redis
**비동기 백그라운드 작업 처리**

```python
# app/tasks/celery_app.py
from celery import Celery
from app.config import settings

celery_app = Celery(
    "whiteblack",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


# app/tasks/analysis_tasks.py
from celery import Task
from app.tasks.celery_app import celery_app
from app.services.analysis_service import AnalysisService
from app.db.session import SessionLocal

@celery_app.task(bind=True, name="analyze_repository")
def analyze_repository_task(self: Task, analysis_id: str, repository_url: str):
    """코드 분석 백그라운드 작업"""
    db = SessionLocal()

    try:
        service = AnalysisService(db)

        # 1. 코드 다운로드
        self.update_state(state="DOWNLOADING", meta={"progress": 10})
        code_path = service.download_code(repository_url)

        # 2. 코드 전처리
        self.update_state(state="PREPROCESSING", meta={"progress": 20})
        preprocessed_code = service.preprocess_code(code_path)

        # 3. AI 분석
        self.update_state(state="ANALYZING", meta={"progress": 30})
        analysis_results = service.analyze_code(preprocessed_code)

        # 4. 레벨 계산
        self.update_state(state="SCORING", meta={"progress": 70})
        level, scores = service.calculate_level(analysis_results)

        # 5. 리뷰 생성
        self.update_state(state="GENERATING_REVIEW", meta={"progress": 85})
        review = service.generate_review(level, scores, analysis_results)

        # 6. 결과 저장
        self.update_state(state="SAVING", meta={"progress": 95})
        service.save_results(analysis_id, level, scores, review)

        return {
            "analysis_id": analysis_id,
            "status": "completed",
            "level": level,
        }

    except Exception as e:
        self.update_state(state="FAILED", meta={"error": str(e)})
        service.mark_failed(analysis_id, str(e))
        raise
    finally:
        db.close()
```

### 2.4 Pydantic 스키마
```python
# app/schemas/analysis.py
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    ANALYZING = "analyzing"
    GENERATING_REVIEW = "generating_review"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisCreate(BaseModel):
    repository_id: str

class AnalysisResponse(BaseModel):
    id: str
    user_id: str
    repository_id: str
    status: AnalysisStatus
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AnalysisResultResponse(BaseModel):
    id: str
    level: int = Field(..., ge=1, le=5)
    overall_score: float = Field(..., ge=0, le=100)
    security_score: float
    quality_score: float
    complexity_score: float
    documentation_score: float
    review_text: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
```

## 3. AI 모델 연동 전략

### 3.1 Hugging Face Transformers (직접 로드)
**장점:**
- Python 네이티브 통합
- 완전한 제어
- 낮은 레이턴시 (로컬 추론)
- API 호출 비용 없음

**단점:**
- GPU 인프라 필요
- 메모리 요구사항 높음

```python
# app/ai/models/code_reviewer.py
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch

class CodeReviewerModel:
    def __init__(self, model_name: str = "microsoft/codereviewer"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device)

    def analyze(self, code: str, max_length: int = 512) -> str:
        """코드 리뷰 수행"""
        inputs = self.tokenizer(
            code,
            max_length=max_length,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=512,
                num_beams=5,
                early_stopping=True
            )

        review = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return review


# app/ai/huggingface_client.py
from app.ai.models.code_reviewer import CodeReviewerModel
from app.ai.models.vulnerability_detector import VulnerabilityDetector
from functools import lru_cache

class HuggingFaceClient:
    """모델 로드 및 캐싱 관리"""

    def __init__(self):
        self._models = {}

    @lru_cache(maxsize=1)
    def get_code_reviewer(self) -> CodeReviewerModel:
        if "code_reviewer" not in self._models:
            self._models["code_reviewer"] = CodeReviewerModel()
        return self._models["code_reviewer"]

    @lru_cache(maxsize=1)
    def get_vulnerability_detector(self) -> VulnerabilityDetector:
        if "vulnerability_detector" not in self._models:
            self._models["vulnerability_detector"] = VulnerabilityDetector()
        return self._models["vulnerability_detector"]

# Singleton 패턴
hf_client = HuggingFaceClient()
```

### 3.2 Hugging Face Inference API (선택사항)
```python
# app/ai/huggingface_api.py
from huggingface_hub import InferenceClient
from app.config import settings

class HuggingFaceAPI:
    def __init__(self):
        self.client = InferenceClient(token=settings.HUGGINGFACE_API_KEY)

    async def analyze_code(self, code: str, model: str) -> str:
        response = await self.client.text_generation(
            prompt=code,
            model=model,
            max_new_tokens=512,
            temperature=0.7,
        )
        return response
```

## 4. 분석 파이프라인 상세

### 4.1 코드 전처리
```python
# app/ai/processors/code_preprocessor.py
import os
from pathlib import Path
from typing import List, Dict
import gitignore_parser

class CodePreprocessor:
    EXCLUDED_DIRS = {
        "node_modules", ".git", "__pycache__", "venv",
        "env", ".env", "dist", "build", ".next"
    }

    EXCLUDED_EXTENSIONS = {
        ".pyc", ".pyo", ".so", ".dylib", ".exe",
        ".jpg", ".png", ".gif", ".mp4", ".pdf"
    }

    MAX_FILE_SIZE = 1_000_000  # 1MB

    def preprocess(self, repo_path: str) -> List[Dict[str, str]]:
        """Repository 코드 전처리"""
        files = []

        # .gitignore 파싱
        gitignore_path = Path(repo_path) / ".gitignore"
        if gitignore_path.exists():
            matches = gitignore_parser.parse_gitignore(gitignore_path)
        else:
            matches = lambda x: False

        # 파일 수집
        for root, dirs, filenames in os.walk(repo_path):
            # 제외 디렉토리 필터링
            dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS]

            for filename in filenames:
                filepath = Path(root) / filename

                # 제외 조건 체크
                if self._should_exclude(filepath, matches):
                    continue

                # 파일 읽기
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()

                    files.append({
                        "path": str(filepath.relative_to(repo_path)),
                        "content": content,
                        "language": self._detect_language(filepath),
                    })
                except Exception as e:
                    continue

        return files

    def _should_exclude(self, filepath: Path, gitignore_matches) -> bool:
        """파일 제외 여부 판단"""
        # 확장자 체크
        if filepath.suffix in self.EXCLUDED_EXTENSIONS:
            return True

        # 파일 크기 체크
        if filepath.stat().st_size > self.MAX_FILE_SIZE:
            return True

        # .gitignore 체크
        if gitignore_matches(str(filepath)):
            return True

        return False

    def _detect_language(self, filepath: Path) -> str:
        """프로그래밍 언어 감지"""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
        }
        return extension_map.get(filepath.suffix, "unknown")

    def chunk_code(self, files: List[Dict], max_tokens: int = 2048) -> List[List[Dict]]:
        """모델 입력 크기에 맞게 청크 분할"""
        chunks = []
        current_chunk = []
        current_size = 0

        for file in files:
            # 간단한 토큰 추정 (문자 수 / 4)
            estimated_tokens = len(file["content"]) // 4

            if current_size + estimated_tokens > max_tokens:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = [file]
                current_size = estimated_tokens
            else:
                current_chunk.append(file)
                current_size += estimated_tokens

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
```

### 4.2 분석 오케스트레이터
```python
# app/ai/processors/analysis_orchestrator.py
from typing import Dict, Any
import asyncio
from app.ai.huggingface_client import hf_client

class AnalysisOrchestrator:
    """여러 모델을 병렬로 실행"""

    async def analyze_all(self, code_chunks: List[List[Dict]]) -> Dict[str, Any]:
        """모든 분석 병렬 실행"""

        # 병렬 실행
        results = await asyncio.gather(
            self._analyze_code_review(code_chunks),
            self._analyze_security(code_chunks),
            self._analyze_quality(code_chunks),
            self._analyze_complexity(code_chunks),
            return_exceptions=True
        )

        return {
            "code_review": results[0],
            "security": results[1],
            "quality": results[2],
            "complexity": results[3],
        }

    async def _analyze_code_review(self, chunks):
        model = hf_client.get_code_reviewer()
        reviews = []
        for chunk in chunks:
            code = "\n".join([f["content"] for f in chunk])
            review = model.analyze(code)
            reviews.append(review)
        return reviews

    async def _analyze_security(self, chunks):
        detector = hf_client.get_vulnerability_detector()
        vulnerabilities = []
        for chunk in chunks:
            code = "\n".join([f["content"] for f in chunk])
            result = detector.detect(code)
            vulnerabilities.extend(result)
        return vulnerabilities

    # ... 다른 분석 메서드
```

### 4.3 레벨 계산
```python
# app/services/scoring_service.py
from typing import Dict, Tuple

class ScoringService:
    WEIGHTS = {
        "security": 0.30,
        "quality": 0.25,
        "best_practices": 0.20,
        "complexity": 0.15,
        "documentation": 0.10,
    }

    def calculate_level(self, scores: Dict[str, float]) -> Tuple[int, Dict[str, float]]:
        """레벨 계산"""
        # 가중 평균 계산
        weighted_score = sum(
            scores[key] * self.WEIGHTS[key]
            for key in self.WEIGHTS.keys()
        )

        # 레벨 변환
        if weighted_score >= 90:
            level = 5
        elif weighted_score >= 75:
            level = 4
        elif weighted_score >= 60:
            level = 3
        elif weighted_score >= 40:
            level = 2
        else:
            level = 1

        return level, {
            "overall": weighted_score,
            **scores
        }
```

### 4.4 안성재 쉐프 페르소나 리뷰
```python
# app/ai/prompts/chef_ahn.py
CHEF_AHN_SYSTEM_PROMPT = """
당신은 냉정하고 직설적인 안성재 쉐프입니다.
- 문제점은 정확하고 날카롭게 지적합니다
- 레벨이 낮으면 더 엄격하게
- 레벨이 높으면 인정하되 개선점도 제시
- 아래 말투를 참고하여 한국어 존댓말을 사용

말투 예시:
- "맛을 보고 이걸 판단하고 이거는 제가 정확하지 않나 싶어요"
- "코드의 완성도가 조금 모자라더라구요"
- "제가 제일 중요하게 생각하는 것은 코드의 모듈화 정도인 것 같아요. 그 모듈화가 굉장히 타이트해요"
- "이 코드는 잘 못 작성됬거덩요."
- "코딩의 세계는 무궁무진해요. 생각을 여세요."
- "코드의 모듈화, SOLID. 굉장히 좋았던거 같아요"
- "와 이거 존나 잘 짰다 이러는데.. 메서드 하나가 계속 남아서"
- "아직은 좀 force하고 있다는 느낌이 있고"
- "확 들어 맞지 않는 하나는 아무 의미 없는 필드를 넣었어요."
- "제 생각에는 제일 자신있는 코드를 저에게 보여줬다고 생각해요. 작성한 사람이 제일 잘 알고 있으니까."
- "지금 이 코드들은 따로 놀고 있어요. 탈락입니다"
- "코드의 완성도가 조금 모자라더라구요."
- "코드가 이븐하게 쪼개지지 않았어요"
- "코드를 되게 잘 짜시는 분 가테요. 다음 거를 보고 싶고, 여기다 다른 거를 어떻게 추가할 수 있을까? 라는 기대감을 같고, 굉장히 컴플릿 한거죠"
- "아키텍처라는게 이제 좀 어려운거거덩요"
- "확실한 전달력이 없으면 전 애매하다고 보거덩요"
- "근데 이 코드가 지금 저한텐 킥이거덩요"
- "너무 좋습니다. 축하드립니다. 통과하셨습니다"
- "이 코드는 잘 못 작성됐거덩요. 로직이 이븐하게 동작하지 않았어요"
- "제 생각에는 본인이 알고 있는 지식은 조금 모자른 것 같아요"
- "보류하겠습니다"
- "탈락입니다"
- "생존하셨습니다"
"""

def build_review_prompt(level: int, scores: Dict[str, float], issues: List[str]) -> str:
    return f"""
개발자의 코드를 다음과 같이 평가했습니다:

레벨: {level}/5
종합 점수: {scores['overall']:.1f}/100
보안 점수: {scores['security']:.1f}/100
코드 품질: {scores['quality']:.1f}/100
복잡도: {scores['complexity']:.1f}/100
문서화: {scores['documentation']:.1f}/100

주요 문제점:
{chr(10).join(f'- {issue}' for issue in issues)}

안성재 쉐프의 말투로 이 개발자에게 직설적이고
날카롭지만 재미있는 리뷰를 작성해주세요.
개선점을 구체적으로 지적하고,
{'격려도 잊지 마세요.' if level >= 4 else '엄격하게 평가해주세요.'}

리뷰는 300-500자 정도로 작성해주세요.
"""


# app/services/persona_service.py
from app.ai.huggingface_client import hf_client
from app.ai.prompts.chef_ahn import CHEF_AHN_SYSTEM_PROMPT, build_review_prompt
from typing import Dict, List

class PersonaService:
    """로컬 LLM으로 페르소나 리뷰 생성"""

    def __init__(self):
        # OpenAI 대신 로컬 한국어 LLM 사용
        self.llm = hf_client.get_persona_llm()

    def generate_review(
        self,
        level: int,
        scores: Dict[str, float],
        issues: List[str]
    ) -> str:
        """안성재 쉐프 스타일 리뷰 생성 (GPU로 실행)"""
        prompt = build_review_prompt(level, scores, issues)

        review = self.llm.generate_review(
            system_prompt=CHEF_AHN_SYSTEM_PROMPT,
            user_prompt=prompt,
            max_new_tokens=1000,
            temperature=0.8
        )

        return review
```

## 5. API 엔드포인트 상세 설계

### 5.1 FastAPI 라우터
```python
# app/api/v1/analysis.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.analysis import AnalysisCreate, AnalysisResponse, AnalysisResultResponse
from app.services.analysis_service import AnalysisService
from app.core.security import get_current_user
from app.db.models.user import User
from app.tasks.analysis_tasks import analyze_repository_task

router = APIRouter()

@router.post("/", response_model=AnalysisResponse)
async def create_analysis(
    data: AnalysisCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """코드 분석 시작"""
    service = AnalysisService(db)

    # 분석 작업 생성
    analysis = service.create_analysis(
        user_id=current_user.id,
        repository_id=data.repository_id,
    )

    # Celery 백그라운드 작업 시작
    repository = service.get_repository(data.repository_id)
    task = analyze_repository_task.delay(analysis.id, repository.url)

    return analysis


@router.get("/{analysis_id}/status")
async def get_analysis_status(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """분석 진행 상황 조회"""
    service = AnalysisService(db)
    analysis = service.get_analysis(analysis_id)

    if not analysis or analysis.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Celery 작업 상태 조회
    from app.tasks.celery_app import celery_app
    task = celery_app.AsyncResult(analysis_id)

    return {
        "status": analysis.status.value,
        "progress": task.info.get("progress", 0) if task.info else 0,
        "started_at": analysis.started_at,
    }


@router.get("/{analysis_id}/result", response_model=AnalysisResultResponse)
async def get_analysis_result(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """분석 결과 조회"""
    service = AnalysisService(db)
    result = service.get_result(analysis_id)

    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    return result


# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from app.core.github_oauth import GitHubOAuth
from app.core.security import create_access_token
from app.schemas.user import Token

router = APIRouter()
github_oauth = GitHubOAuth()

@router.get("/github")
async def github_login():
    """GitHub OAuth 로그인 시작"""
    authorization_url = github_oauth.get_authorization_url()
    return RedirectResponse(authorization_url)


@router.get("/github/callback")
async def github_callback(code: str, db: Session = Depends(get_db)):
    """GitHub OAuth 콜백"""
    # 토큰 교환
    access_token = await github_oauth.exchange_code_for_token(code)

    # 사용자 정보 가져오기
    user_info = await github_oauth.get_user_info(access_token)

    # 사용자 저장 또는 업데이트
    from app.services.user_service import UserService
    user_service = UserService(db)
    user = user_service.create_or_update_user(user_info, access_token)

    # JWT 발급
    jwt_token = create_access_token(data={"sub": user.id})

    return Token(access_token=jwt_token, token_type="bearer")
```

### 5.2 메인 애플리케이션
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, github, analysis, reports
from app.core.rate_limiter import RateLimiterMiddleware
from app.middleware.logging_middleware import LoggingMiddleware

app = FastAPI(
    title="흑백개발자 API",
    description="AI 기반 개발자 실력 평가 플랫폼",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 커스텀 미들웨어
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(LoggingMiddleware)

# 라우터 등록
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(github.router, prefix="/api/v1/github", tags=["github"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])

@app.get("/")
async def root():
    return {"message": "흑백개발자 API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

## 6. 환경 설정

### 6.1 Pydantic Settings
```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "White-Black Developer"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # GitHub OAuth
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_CALLBACK_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 168  # 7 days

    # AI 모델 설정 (로컬 실행)
    CODE_REVIEWER_MODEL: str = "microsoft/codereviewer"
    VULNERABILITY_DETECTOR_MODEL: str = "mahdin70/codebert-devign-code-vulnerability-detector"
    PERSONA_MODEL: str = "beomi/OPEN-SOLAR-KO-10.7B"

    # 모델 캐시 디렉토리
    HF_HOME: str = "./model_cache"
    TRANSFORMERS_CACHE: str = "./model_cache"

    # GPU 설정
    CUDA_VISIBLE_DEVICES: str = "0"  # 사용할 GPU ID

    # Encryption
    ENCRYPTION_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
```

### 6.2 환경 변수 예시
```bash
# .env.example
# App
DEBUG=true

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/whiteblack

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# GitHub OAuth
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
GITHUB_CALLBACK_URL=http://localhost:8000/api/v1/auth/github/callback

# JWT
JWT_SECRET_KEY=your-secret-key-here

# AI 모델 설정 (로컬 실행)
CODE_REVIEWER_MODEL=microsoft/codereviewer
VULNERABILITY_DETECTOR_MODEL=mahdin70/codebert-devign-code-vulnerability-detector
PERSONA_MODEL=beomi/OPEN-SOLAR-KO-10.7B

# 모델 캐시 디렉토리
HF_HOME=./model_cache
TRANSFORMERS_CACHE=./model_cache

# GPU 설정
CUDA_VISIBLE_DEVICES=0

# Encryption
ENCRYPTION_KEY=your-encryption-key-32-bytes
```

## 7. 의존성 관리

### 7.1 pyproject.toml (Poetry)
```toml
[tool.poetry]
name = "white-black-developer-be"
version = "0.1.0"
description = "AI 기반 개발자 실력 평가 플랫폼"
authors = ["Your Name <you@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
sqlalchemy = "^2.0.25"
alembic = "^1.13.1"
psycopg2-binary = "^2.9.9"
redis = "^5.0.1"
celery = "^5.3.6"
pydantic = {extras = ["email"], version = "^2.5.3"}
pydantic-settings = "^2.1.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
python-multipart = "^0.0.6"
authlib = "^1.3.0"
httpx = "^0.26.0"
# AI/ML (GPU 기반)
transformers = "^4.37.0"
torch = "^2.1.2"  # CUDA 11.8 버전
huggingface-hub = "^0.20.2"
bitsandbytes = "^0.41.0"  # 모델 양자화
accelerate = "^0.25.0"  # 멀티 GPU 및 최적화
sentencepiece = "^0.1.99"  # 일부 모델 토크나이저
# Git
gitpython = "^3.1.41"
gitignore-parser = "^0.1.11"

[tool.poetry.dev-dependencies]
pytest = "^7.4.4"
pytest-asyncio = "^0.23.3"
pytest-cov = "^4.1.0"
black = "^23.12.1"
flake8 = "^7.0.0"
mypy = "^1.8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### 7.2 requirements.txt (대안)
```
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0

# Database
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9

# Cache & Queue
redis==5.0.1
celery==5.3.6

# Validation & Settings
pydantic[email]==2.5.3
pydantic-settings==2.1.0

# Auth & Security
python-jose[cryptography]==3.3.0
authlib==1.3.0
cryptography==41.0.7

# HTTP Client
httpx==0.26.0

# AI/ML (GPU 기반)
transformers==4.37.0
torch==2.1.2+cu118  # CUDA 11.8
huggingface-hub==0.20.2
bitsandbytes==0.41.0
accelerate==0.25.0
sentencepiece==0.1.99

# Git
gitpython==3.1.41
gitignore-parser==0.1.11
```

**PyTorch CUDA 설치 주의사항:**
```bash
# CUDA 11.8 버전 (권장)
pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cu118

# 또는 CUDA 12.1
pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cu121
```

## 8. Docker 설정 (GPU 지원)

### 8.1 Dockerfile (GPU 버전)
```dockerfile
# NVIDIA CUDA 베이스 이미지 사용
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Python 3.11 설치
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    gcc \
    g++ \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python 3.11을 기본으로 설정
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

WORKDIR /app

# pip 업그레이드
RUN pip install --upgrade pip

# PyTorch CUDA 버전 먼저 설치
RUN pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cu118

# 나머지 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY ./app ./app
COPY alembic.ini ./

# 모델 캐시 디렉토리 생성
RUN mkdir -p /app/model_cache

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/model_cache
ENV TRANSFORMERS_CACHE=/app/model_cache

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8.1.1 Dockerfile (개발용 - 경량)
```dockerfile
# GPU 없이 개발할 때 (CPU 모드)
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

# CPU 버전 PyTorch
RUN pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY alembic.ini ./

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 8.2 docker-compose.yml (GPU 지원)
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/whiteblack
      - REDIS_HOST=redis
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
      - HF_HOME=/app/model_cache
      - TRANSFORMERS_CACHE=/app/model_cache
      - CUDA_VISIBLE_DEVICES=0
    depends_on:
      - db
      - redis
    volumes:
      - ./app:/app/app
      - model_cache:/app/model_cache  # 모델 캐시 영속화
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1  # GPU 1개 할당
              capabilities: [gpu]
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/whiteblack
      - REDIS_HOST=redis
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
      - HF_HOME=/app/model_cache
      - TRANSFORMERS_CACHE=/app/model_cache
      - CUDA_VISIBLE_DEVICES=0
    depends_on:
      - db
      - redis
    volumes:
      - ./app:/app/app
      - model_cache:/app/model_cache
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1  # Celery worker도 GPU 필요
              capabilities: [gpu]

  celery_beat:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A app.tasks.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/whiteblack
      - REDIS_HOST=redis
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - redis
    volumes:
      - ./app:/app/app

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: whiteblack
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  model_cache:  # 모델 캐시용 volume
```

**Docker Compose 실행:**
```bash
# GPU 지원 확인
docker run --rm --gpus all nvidia/cuda:11.8.0-base nvidia-smi

# 컨테이너 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f api
docker-compose logs -f celery_worker
```

**시스템 요구사항:**
- Docker 20.10+
- NVIDIA Container Toolkit 설치
- NVIDIA Driver 470.x 이상

## 9. 개발 순서 (MVP)

### Week 1-2: 기초 인프라
- [ ] FastAPI 프로젝트 초기화
- [ ] SQLAlchemy 모델 및 Alembic 마이그레이션
- [ ] GitHub OAuth 연동
- [ ] JWT 인증 구현
- [ ] 기본 API 구조

### Week 3-4: GitHub 연동 및 코드 분석
- [ ] GitHub API 클라이언트 (PyGithub)
- [ ] Repository 조회 API
- [ ] 코드 다운로드 서비스 (GitPython)
- [ ] 코드 전처리 파이프라인
- [ ] Celery 워커 설정

### Week 5-6: AI 모델 통합
- [ ] Hugging Face Transformers 통합
- [ ] CodeReviewer 모델 로드
- [ ] Vulnerability Detector 통합
- [ ] 분석 오케스트레이터
- [ ] 레벨 계산 알고리즘

### Week 7-8: 리뷰 생성 및 리포트
- [ ] 페르소나 리뷰 생성 (OpenAI API)
- [ ] 프롬프트 엔지니어링
- [ ] 리포트 API
- [ ] 에러 처리 및 로깅

## 10. 개발 명령어

```bash
# Poetry 사용
poetry install                    # 의존성 설치
poetry shell                      # 가상환경 활성화
poetry add <package>              # 패키지 추가

# 또는 pip/venv
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 데이터베이스
alembic revision --autogenerate -m "message"  # 마이그레이션 생성
alembic upgrade head              # 마이그레이션 적용
alembic downgrade -1              # 마이그레이션 롤백

# 개발 서버
uvicorn app.main:app --reload     # 개발 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000  # 프로덕션

# Celery
celery -A app.tasks.celery_app worker --loglevel=info  # 워커 실행
celery -A app.tasks.celery_app beat --loglevel=info    # 스케줄러 실행
celery -A app.tasks.celery_app flower                  # 모니터링 UI

# 테스트
pytest                            # 전체 테스트
pytest tests/unit                 # 단위 테스트
pytest --cov=app --cov-report=html  # 커버리지

# 코드 품질
black app/                        # 코드 포맷팅
flake8 app/                       # 린팅
mypy app/                         # 타입 체크

# Docker
docker-compose up                 # 전체 실행
docker-compose up -d              # 백그라운드 실행
docker-compose down               # 종료
docker-compose logs -f api        # 로그 확인
```

## 11. 테스트 전략

### 11.1 단위 테스트
```python
# tests/unit/test_scoring.py
import pytest
from app.services.scoring_service import ScoringService

def test_calculate_level():
    service = ScoringService()

    scores = {
        "security": 85.0,
        "quality": 80.0,
        "best_practices": 75.0,
        "complexity": 70.0,
        "documentation": 60.0,
    }

    level, result = service.calculate_level(scores)

    assert level == 4
    assert 75 <= result["overall"] < 90
```

### 11.2 통합 테스트
```python
# tests/integration/test_analysis_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_analysis(auth_headers):
    response = client.post(
        "/api/v1/analysis/",
        json={"repository_id": "test-repo-id"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"
```

## 12. 보안 고려사항

### 12.1 GitHub Token 암호화
```python
# app/utils/encryption.py
from cryptography.fernet import Fernet
from app.config import settings

cipher = Fernet(settings.ENCRYPTION_KEY.encode())

def encrypt_token(token: str) -> str:
    return cipher.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    return cipher.decrypt(encrypted_token.encode()).decode()
```

### 12.2 Rate Limiting
```python
# app/core/rate_limiter.py
from fastapi import Request, HTTPException
from redis import Redis
from app.config import settings

redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

async def check_rate_limit(request: Request, max_requests: int = 100, window: int = 3600):
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"

    current = redis_client.get(key)
    if current and int(current) >= max_requests:
        raise HTTPException(status_code=429, detail="Too many requests")

    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    pipe.execute()
```

## 13. 모니터링 및 로깅

### 13.1 로깅 설정
```python
# app/utils/logger.py
import logging
from app.config import settings

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("whiteblack")
```

## 14. 참고 문서

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
