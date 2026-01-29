# PRD: 흑백개발자 (White-Black Developer)

## 1. 프로젝트 개요

### 1.1 프로젝트 명
**흑백개발자** - AI 기반 개발자 실력 평가 플랫폼

### 1.2 프로젝트 컨셉
"흑백요리사"의 안성재 쉐프와 같은 살벌하고 직설적인 코드 리뷰를 통해 개발자의 실력을 냉정하게 평가하는 플랫폼

### 1.3 목표
- GitHub 연동을 통한 자동 코드 분석
- Hugging Face AI 모델을 활용한 객관적 코드 리뷰
- 재미있고 독특한 피드백으로 학습 동기 부여

## 2. 핵심 기능 요구사항

### 2.1 GitHub 연동
- **기능**: 사용자 GitHub 계정 OAuth 연동
- **세부 사항**:
  - GitHub OAuth 2.0 인증
  - 사용자 repository 목록 조회
  - 특정 repository 선택 및 코드 다운로드
  - Private repository 접근 권한 처리

### 2.2 코드 분석 및 리뷰
- **기능**: Hugging Face 모델을 활용한 다각도 코드 분석
- **분석 항목**:
  1. 코드 품질 (Code Quality)
  2. 보안 취약점 (Security Vulnerabilities)
  3. 코드 복잡도 (Code Complexity)
  4. 베스트 프랙티스 준수 (Best Practices)
  5. 코드 일관성 (Code Consistency)
  6. 문서화 수준 (Documentation)

### 2.3 레벨 평가 시스템
- **레벨 체계**: 1~5단계
  - **레벨 5**: 마스터 개발자 - 완벽에 가까운 코드
  - **레벨 4**: 시니어 개발자 - 우수한 코드 품질
  - **레벨 3**: 미드레벨 개발자 - 평균 이상
  - **레벨 2**: 주니어 개발자 - 개선 필요
  - **레벨 1**: 초보 개발자 - 많은 개선 필요

- **평가 기준**:
  - 보안 취약점: 30% 가중치
  - 코드 품질: 25% 가중치
  - 베스트 프랙티스: 20% 가중치
  - 코드 복잡도: 15% 가중치
  - 문서화: 10% 가중치

### 2.4 AI 리뷰 생성 (안성재 쉐프 페르소나)
- **기능**: 평가 결과를 살벌하고 재미있는 리뷰로 변환
- **특징**:
  - 직설적이고 날카로운 피드백
  - 유머러스하면서도 핵심을 찌르는 표현
  - 개선점에 대한 구체적 조언
  - 한국어 자연어 처리

### 2.5 리포트 제공
- **기능**: 사용자에게 종합 평가 리포트 제공
- **포함 내용**:
  - 최종 레벨
  - 안성재 쉐프 스타일 리뷰
  - 상세 분석 결과 (항목별 점수)
  - 주요 문제점 및 개선 방향
  - 우수한 코드 예시 (있는 경우)

## 3. Hugging Face 모델 선정

### 3.1 코드 리뷰 전용 모델
#### microsoft/codereviewer
- **용도**: 메인 코드 리뷰
- **특징**: 코드 변경사항 및 리뷰 데이터로 사전 학습
- **기능**: 전반적인 코드 품질 평가, 개선 제안

#### LLaMA-Reviewer
- **용도**: 보조 리뷰 및 상세 분석
- **특징**: 파라미터 효율적 fine-tuning으로 리소스 최적화
- **기능**: 코드 리뷰 자동화, 상세 피드백 생성

### 3.2 코드 분석 모델

#### microsoft/codebert-base
- **용도**: 다중 언어 코드 분석
- **지원 언어**: Python, Java, JavaScript, PHP, Ruby, Go
- **기능**:
  - 코드-자연어 이해
  - 코드 검색
  - 코드 문서화 평가

#### mahdin70/codebert-devign-code-vulnerability-detector
- **용도**: 보안 취약점 탐지
- **기능**:
  - 정적 코드 분석
  - 보안 감사
  - 자동 취약점 탐지

#### mrm8488/codebert-base-finetuned-detect-insecure-code
- **용도**: 보안 위험 코드 식별
- **기능**:
  - 리소스 누수 탐지
  - Use-after-free 취약점 탐지
  - DoS 공격 가능성 분석
  - 이진 분류 (안전/위험)

### 3.3 코드 생성 및 이해 모델

#### StarCoder2-15B
- **용도**: 코드 품질 및 베스트 프랙티스 평가
- **특징**:
  - 15B 파라미터
  - 600+ 프로그래밍 언어 지원
  - 4조 토큰으로 학습
- **기능**:
  - 코드 완성도 평가
  - 패턴 인식
  - 베스트 프랙티스 비교

#### CodeLlama-34B
- **용도**: 복잡한 코드 분석 및 개선 제안
- **특징**:
  - 34B 파라미터 (고성능)
  - Python 전문가 버전 사용 가능
  - Instruction fine-tuned 버전
- **기능**:
  - 코드 리팩토링 제안
  - 복잡도 분석
  - 아키텍처 평가

### 3.4 페르소나 생성 모델 (한국어 LLM)
#### SOLAR-10.7B-Instruct (Upstage) - 추천
- **용도**: 안성재 쉐프 스타일 리뷰 생성
- **크기**: 10.7B 파라미터
- **특징**: 한국어 성능 우수, 지시 따르기 능력 뛰어남
- **VRAM**: 12GB+ 권장 (4-bit 양자화 시 6GB)

#### 대안 모델
- **EEVE-Korean-Instruct-10.8B**: 야놀자 제작, 최신 한국어 모델
- **Llama-2-ko-7b**: 경량, 8GB VRAM으로 동작
- **KULLM-12.8B**: NLPAI Lab, 한국어 특화
- **Qwen2.5-7B-Instruct**: 다국어 지원, 성능 우수

**기능**:
- 분석 결과를 재미있는 리뷰로 변환
- 한국어 자연스러운 표현
- 페르소나 일관성 유지
- 완전 로컬 실행 (API 비용 없음)

## 4. 기술 스택

### 4.1 백엔드
- **프레임워크**: FastAPI
- **언어**: Python 3.11+
- **데이터베이스**: PostgreSQL + SQLAlchemy ORM
- **캐시/큐**: Redis (세션, API 응답 캐싱, Celery 큐)
- **비동기 처리**: Celery (백그라운드 작업)

### 4.2 AI/ML (GPU 기반 로컬 추론)
- **Hugging Face Transformers**: 모델 직접 로드 및 추론
- **PyTorch**: 딥러닝 프레임워크 (CUDA 지원)
- **bitsandbytes**: 모델 양자화 (메모리 최적화)
- **accelerate**: 멀티 GPU 및 최적화
- **GPU**: NVIDIA GPU (CUDA 11.8+, VRAM 12GB+ 권장)

### 4.3 인증 및 연동
- **OAuth 2.0**: GitHub 인증 (Authlib)
- **GitHub API**: PyGithub 또는 httpx
- **JWT**: python-jose (세션 관리)

### 4.4 인프라
- **컨테이너**: Docker + Docker Compose (GPU 지원)
- **GPU 컨테이너**: NVIDIA Container Toolkit
- **클라우드**: AWS (GPU 인스턴스: g4dn, g5 등)

## 5. 시스템 아키텍처

### 5.1 전체 플로우
```
사용자 → GitHub OAuth → Repository 선택 → 코드 다운로드 →
AI 분석 파이프라인 → 레벨 평가 → 페르소나 리뷰 생성 → 리포트 제공
```

### 5.2 AI 분석 파이프라인
```
1. 코드 전처리 및 파싱
2. 병렬 분석:
   - CodeReviewer: 전반적 리뷰
   - CodeBERT: 언어별 분석
   - Vulnerability Detector: 보안 분석
   - StarCoder2: 베스트 프랙티스 평가
   - CodeLlama: 복잡도 분석
3. 결과 집계 및 정규화
4. 레벨 계산
5. 페르소나 리뷰 생성
```

### 5.3 주요 컴포넌트
- **API Gateway**: 요청 라우팅 및 인증
- **GitHub Service**: GitHub API 연동
- **Code Analysis Service**: 코드 다운로드 및 전처리
- **AI Inference Service**: Hugging Face 모델 추론
- **Scoring Service**: 레벨 계산 및 평가
- **Persona Service**: 리뷰 텍스트 생성
- **Report Service**: 최종 리포트 생성

## 6. API 엔드포인트 (예시)

### 6.1 인증
- `POST /auth/github` - GitHub OAuth 시작
- `GET /auth/github/callback` - OAuth 콜백
- `POST /auth/logout` - 로그아웃

### 6.2 Repository
- `GET /repositories` - 사용자 repository 목록
- `GET /repositories/:id` - Repository 상세 정보

### 6.3 분석
- `POST /analyze` - 코드 분석 시작
- `GET /analyze/:jobId` - 분석 진행 상황
- `GET /analyze/:jobId/result` - 분석 결과

### 6.4 리포트
- `GET /reports/:id` - 리포트 조회
- `GET /reports/history` - 분석 이력

## 7. 데이터베이스 스키마 (개요)

### 7.1 Users
- id, github_id, username, email, avatar_url, access_token, created_at

### 7.2 Repositories
- id, user_id, github_repo_id, name, url, language, created_at

### 7.3 Analyses
- id, user_id, repository_id, status, started_at, completed_at

### 7.4 AnalysisResults
- id, analysis_id, level, overall_score, security_score, quality_score, complexity_score, documentation_score, review_text, details (JSON)

## 8. 비기능 요구사항

### 8.1 성능
- API 응답 시간: 95%ile < 200ms (분석 요청 제외)
- 코드 분석 시간: 중간 크기 프로젝트 < 5분
- 동시 사용자: 최소 100명 지원

### 8.2 보안
- GitHub access token 암호화 저장
- HTTPS 필수
- Rate limiting 적용
- SQL Injection, XSS 방어

### 8.3 확장성
- 마이크로서비스 아키텍처로 독립적 확장
- AI 추론 서비스 수평 확장 가능
- 데이터베이스 복제 및 샤딩 대비

## 9. 개발 단계

### Phase 1:
- GitHub OAuth 연동
- 기본 코드 다운로드
- 1-2개 모델로 간단한 분석
- 레벨 평가 (기본 알고리즘)
- 단순한 리뷰 생성

### Phase 2:
- 다중 모델 통합
- 상세 분석 파이프라인
- 안성재 쉐프 페르소나 고도화
- 리포트 UI/UX 개선

### Phase 3:
- 성능 최적화
- 캐싱 전략
- 모니터링 및 로깅
- A/B 테스트

## 10. 주요 과제 및 고려사항

### 10.1 기술적 과제
- **모델 추론 비용**: Hugging Face Inference API Transformers 사용
- **대용량 코드베이스**: 큰 repository 처리 최적화
- **다중 언어 지원**: 다양한 프로그래밍 언어 파싱
- **페르소나 일관성**: 안성재 쉐프 스타일 품질 유지

### 10.2 비즈니스 고려사항
- **무료/유료 tier**: 분석 횟수 제한
- **프라이버시**: Private repository 코드 보호
- **데이터 보존**: 분석 결과 보관 정책

## 11. 참고 자료

### Hugging Face 모델
- [microsoft/codereviewer](https://huggingface.co/microsoft/codereviewer)
- [LLaMA-Reviewer Paper](https://huggingface.co/papers/2308.11148)
- [microsoft/codebert-base](https://huggingface.co/microsoft/codebert-base)
- [mahdin70/codebert-devign-code-vulnerability-detector](https://huggingface.co/mahdin70/codebert-devign-code-vulnerability-detector)
- [mrm8488/codebert-base-finetuned-detect-insecure-code](https://huggingface.co/mrm8488/codebert-base-finetuned-detect-insecure-code)
- [StarCoder2](https://huggingface.co/docs/transformers/en/model_doc/starcoder2)
- [Code Llama](https://huggingface.co/blog/codellama)

### GitHub API
- [GitHub REST API](https://docs.github.com/en/rest)
- [GitHub OAuth](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps)
