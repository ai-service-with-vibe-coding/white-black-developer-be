# 코드 분석 API 가이드

코드를 분석하고 안성재 쉐프 스타일의 심사평을 받아보는 방법을 설명합니다.

## API 엔드포인트

```
POST /api/v1/analysis/analyze
Content-Type: application/json
```

## 요청 형식

```json
{
  "code": "def hello():\n    print('Hello, World!')",
  "language": "auto",
  "include_persona_review": true
}
```

### 요청 필드

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `code` | string | O | - | 분석할 코드 문자열 |
| `language` | string | X | `"auto"` | 프로그래밍 언어 (`auto`, `python`, `javascript`, `typescript`, `java`, `go`, `rust`, `cpp`, `c`) |
| `include_persona_review` | boolean | X | `true` | 안성재 쉐프 페르소나 리뷰 포함 여부 |

## 응답 형식

```json
{
  "level": 3,
  "level_title": "미들급 개발자",
  "verdict": "생존하셨습니다",
  "overall_score": 65.5,
  "scores": {
    "security": 80.0,
    "quality": 70.0,
    "best_practices": 55.0,
    "complexity": 65.0,
    "documentation": 40.0
  },
  "code_review": "코드 리뷰 내용...",
  "persona_review": "안성재 쉐프 스타일 심사평...",
  "is_vulnerable": false,
  "vulnerability_score": 80.0,
  "issues": ["개선이 필요합니다"],
  "suggestions": ["문서화를 추가하세요"],
  "language": "python",
  "line_count": 10
}
```

### 응답 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `level` | integer | 개발자 레벨 (1-5) |
| `level_title` | string | 레벨 명칭 |
| `verdict` | string | 최종 판정 |
| `overall_score` | float | 종합 점수 (0-100) |
| `scores` | object | 세부 점수 |
| `scores.security` | float | 보안 점수 |
| `scores.quality` | float | 코드 품질 점수 |
| `scores.best_practices` | float | 베스트 프랙티스 점수 |
| `scores.complexity` | float | 복잡도 점수 (낮은 복잡도 = 높은 점수) |
| `scores.documentation` | float | 문서화 점수 |
| `code_review` | string | AI 코드 리뷰 |
| `persona_review` | string | 안성재 쉐프 심사평 (요청 시) |
| `is_vulnerable` | boolean | 보안 취약점 존재 여부 |
| `vulnerability_score` | float | 취약점 점수 |
| `issues` | array | 발견된 이슈 목록 |
| `suggestions` | array | 개선 제안 목록 |
| `language` | string | 감지된 프로그래밍 언어 |
| `line_count` | integer | 코드 라인 수 |

### 레벨 체계

| 레벨 | 명칭 | 점수 범위 | 판정 |
|------|------|-----------|------|
| 1 | 입문자 | 0-35 | 탈락입니다 |
| 2 | 주니어 개발자 | 36-55 | 보류하겠습니다 |
| 3 | 미들급 개발자 | 56-70 | 생존하셨습니다 |
| 4 | 시니어 개발자 | 71-85 | 통과하셨습니다 |
| 5 | 엘리트 개발자 | 86-100 | 축하드립니다 |

---

## 프론트엔드 구현 예시

### JavaScript (Vanilla)

```javascript
async function analyzeCode(code, language = 'auto', includePersona = true) {
  const response = await fetch('/api/v1/analysis/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      code: code,
      language: language,
      include_persona_review: includePersona,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

// 사용 예시
const code = `def hello():
    print("Hello, World!")`;

analyzeCode(code)
  .then((result) => {
    console.log('레벨:', result.level, result.level_title);
    console.log('점수:', result.overall_score);
    console.log('판정:', result.verdict);
    console.log('심사평:', result.persona_review);
  })
  .catch((error) => {
    console.error('분석 실패:', error);
  });
```

### React

```jsx
import { useState } from 'react';

function useCodeAnalysis() {
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyze = async (code, language = 'auto', includePersona = true) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/analysis/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code,
          language,
          include_persona_review: includePersona,
        }),
      });

      if (!response.ok) {
        throw new Error('분석 요청 실패');
      }

      const data = await response.json();
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return { result, isLoading, error, analyze };
}

// 컴포넌트에서 사용
function CodeAnalyzer() {
  const { result, isLoading, error, analyze } = useCodeAnalysis();
  const [code, setCode] = useState('');

  const handleAnalyze = () => {
    analyze(code);
  };

  return (
    <div>
      <textarea
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="코드를 입력하세요"
        rows={10}
      />
      <button onClick={handleAnalyze} disabled={isLoading}>
        {isLoading ? '분석 중...' : '분석하기'}
      </button>

      {error && <p style={{ color: 'red' }}>오류: {error}</p>}

      {result && (
        <div>
          <h2>분석 결과</h2>
          <div className="level">
            <span>레벨 {result.level}</span>
            <span>{result.level_title}</span>
          </div>
          <div className="score">종합 점수: {result.overall_score}</div>

          <h3>세부 점수</h3>
          <ul>
            <li>보안: {result.scores.security}</li>
            <li>품질: {result.scores.quality}</li>
            <li>베스트 프랙티스: {result.scores.best_practices}</li>
            <li>복잡도: {result.scores.complexity}</li>
            <li>문서화: {result.scores.documentation}</li>
          </ul>

          <h3>코드 리뷰</h3>
          <p>{result.code_review}</p>

          {result.persona_review && (
            <>
              <h3>쉐프의 심사평</h3>
              <p style={{ whiteSpace: 'pre-wrap' }}>{result.persona_review}</p>
              <p><strong>{result.verdict}</strong></p>
            </>
          )}

          {result.issues.length > 0 && (
            <>
              <h3>발견된 이슈</h3>
              <ul>
                {result.issues.map((issue, i) => (
                  <li key={i}>{issue}</li>
                ))}
              </ul>
            </>
          )}

          {result.suggestions.length > 0 && (
            <>
              <h3>개선 제안</h3>
              <ul>
                {result.suggestions.map((suggestion, i) => (
                  <li key={i}>{suggestion}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default CodeAnalyzer;
```

### Vue 3

```vue
<template>
  <div>
    <textarea
      v-model="code"
      placeholder="코드를 입력하세요"
      rows="10"
    ></textarea>
    <button @click="analyze" :disabled="isLoading">
      {{ isLoading ? '분석 중...' : '분석하기' }}
    </button>

    <p v-if="error" style="color: red">오류: {{ error }}</p>

    <div v-if="result">
      <h2>분석 결과</h2>
      <div class="level">
        레벨 {{ result.level }} - {{ result.level_title }}
      </div>
      <div class="score">종합 점수: {{ result.overall_score }}</div>

      <h3>세부 점수</h3>
      <ul>
        <li>보안: {{ result.scores.security }}</li>
        <li>품질: {{ result.scores.quality }}</li>
        <li>베스트 프랙티스: {{ result.scores.best_practices }}</li>
        <li>복잡도: {{ result.scores.complexity }}</li>
        <li>문서화: {{ result.scores.documentation }}</li>
      </ul>

      <h3>코드 리뷰</h3>
      <p>{{ result.code_review }}</p>

      <div v-if="result.persona_review">
        <h3>쉐프의 심사평</h3>
        <p style="white-space: pre-wrap">{{ result.persona_review }}</p>
        <p><strong>{{ result.verdict }}</strong></p>
      </div>

      <div v-if="result.issues.length > 0">
        <h3>발견된 이슈</h3>
        <ul>
          <li v-for="(issue, i) in result.issues" :key="i">{{ issue }}</li>
        </ul>
      </div>

      <div v-if="result.suggestions.length > 0">
        <h3>개선 제안</h3>
        <ul>
          <li v-for="(suggestion, i) in result.suggestions" :key="i">
            {{ suggestion }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const code = ref('');
const result = ref(null);
const isLoading = ref(false);
const error = ref(null);

async function analyze() {
  isLoading.value = true;
  error.value = null;

  try {
    const response = await fetch('/api/v1/analysis/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: code.value,
        language: 'auto',
        include_persona_review: true,
      }),
    });

    if (!response.ok) {
      throw new Error('분석 요청 실패');
    }

    result.value = await response.json();
  } catch (err) {
    error.value = err.message;
  } finally {
    isLoading.value = false;
  }
}
</script>
```

---

## 빠른 분석 API

페르소나 리뷰 없이 빠르게 분석하려면 `/quick` 엔드포인트를 사용하세요.

```
POST /api/v1/analysis/quick
Content-Type: application/json
```

요청/응답 형식은 동일하며, `persona_review` 필드가 `null`로 반환됩니다.

---

## curl 테스트

### 기본 분석

```bash
curl -X POST http://localhost:8000/api/v1/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello():\n    print(\"Hello, World!\")",
    "language": "auto",
    "include_persona_review": true
  }'
```

### 빠른 분석 (페르소나 없음)

```bash
curl -X POST http://localhost:8000/api/v1/analysis/quick \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello():\n    print(\"Hello, World!\")",
    "language": "python"
  }'
```

---

## 에러 응답

### 500 Internal Server Error

```json
{
  "detail": "분석 중 오류가 발생했습니다: [에러 메시지]"
}
```

---

## 주의사항

1. **응답 시간**: 페르소나 리뷰 포함 시 GPU 추론으로 인해 10-30초 소요될 수 있습니다.
2. **코드 길이**: 너무 긴 코드는 토큰 제한으로 잘릴 수 있습니다. 핵심 코드만 전송하세요.
3. **언어 감지**: `language: "auto"` 사용 시 자동 감지되지만, 정확도를 위해 언어를 명시하는 것을 권장합니다.
4. **CORS**: 프론트엔드와 백엔드 도메인이 다르면 CORS 설정이 필요합니다.

## 실시간 스트리밍

페르소나 리뷰를 실시간으로 받아보려면 스트리밍 API를 사용하세요.
자세한 내용은 [STREAMING_API.md](./STREAMING_API.md)를 참고하세요.
