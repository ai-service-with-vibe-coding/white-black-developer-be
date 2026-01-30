# 스트리밍 API 가이드

코드 분석 결과를 실시간으로 받아보는 방법을 설명합니다.

## API 엔드포인트

```
POST /api/v1/analysis/analyze/stream
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

## SSE 이벤트 타입

| 이벤트 | 설명 | 데이터 |
|--------|------|--------|
| `analysis` | 코드 분석 결과 (즉시) | 점수, 리뷰, 이슈 등 |
| `persona_token` | 페르소나 리뷰 토큰 | `{"token": "코드"}` |
| `persona_done` | 페르소나 리뷰 완료 | `{"full_review": "전체 리뷰"}` |
| `error` | 에러 발생 | `{"error": "에러 메시지"}` |
| `done` | 모든 처리 완료 | `{"status": "completed"}` |

## 타임라인

```
[요청] ──→ [analysis 이벤트] ──→ [persona_token] ──→ [persona_token] ──→ ... ──→ [persona_done] ──→ [done]
           (즉시, ~2초)         (실시간 스트리밍, 토큰 단위)                    (완료)
```

---

## 프론트엔드 구현 예시

### JavaScript (Vanilla)

```javascript
async function analyzeCodeStream(code, onAnalysis, onToken, onComplete) {
  const response = await fetch('/api/v1/analysis/analyze/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      code: code,
      language: 'auto',
      include_persona_review: true,
    }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop(); // 마지막 불완전한 라인 보관

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        const eventType = line.slice(7);
        continue;
      }
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));

        // 이벤트 타입에 따라 처리
        if (data.level !== undefined) {
          // analysis 이벤트
          onAnalysis(data);
        } else if (data.token !== undefined) {
          // persona_token 이벤트
          onToken(data.token);
        } else if (data.full_review !== undefined) {
          // persona_done 이벤트
          console.log('Persona review completed');
        } else if (data.status === 'completed') {
          // done 이벤트
          onComplete();
        } else if (data.error) {
          // error 이벤트
          console.error('Error:', data.error);
        }
      }
    }
  }
}

// 사용 예시
const code = `def hello():
    print("Hello, World!")`;

let personaReview = '';

analyzeCodeStream(
  code,
  // 분석 결과 수신 (즉시)
  (analysis) => {
    console.log('분석 완료!', analysis);
    document.getElementById('score').textContent = `점수: ${analysis.overall_score}`;
    document.getElementById('level').textContent = `레벨: ${analysis.level}`;
    document.getElementById('code-review').textContent = analysis.code_review;
  },
  // 페르소나 토큰 수신 (실시간)
  (token) => {
    personaReview += token;
    document.getElementById('persona-review').textContent = personaReview;
  },
  // 완료
  () => {
    console.log('모든 처리 완료!');
  }
);
```

### React

```jsx
import { useState, useCallback } from 'react';

function useStreamAnalysis() {
  const [analysis, setAnalysis] = useState(null);
  const [personaReview, setPersonaReview] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);

  const analyze = useCallback(async (code) => {
    setIsLoading(true);
    setPersonaReview('');
    setAnalysis(null);

    try {
      const response = await fetch('/api/v1/analysis/analyze/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code,
          language: 'auto',
          include_persona_review: true,
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));

            if (data.level !== undefined) {
              // 분석 결과
              setAnalysis(data);
              setIsLoading(false);
              setIsStreaming(true);
            } else if (data.token !== undefined) {
              // 페르소나 토큰
              setPersonaReview((prev) => prev + data.token);
            } else if (data.status === 'completed') {
              // 완료
              setIsStreaming(false);
            }
          }
        }
      }
    } catch (error) {
      console.error('Analysis failed:', error);
      setIsLoading(false);
      setIsStreaming(false);
    }
  }, []);

  return { analysis, personaReview, isLoading, isStreaming, analyze };
}

// 컴포넌트에서 사용
function CodeAnalyzer() {
  const { analysis, personaReview, isLoading, isStreaming, analyze } = useStreamAnalysis();
  const [code, setCode] = useState('');

  return (
    <div>
      <textarea
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="코드를 입력하세요"
      />
      <button onClick={() => analyze(code)} disabled={isLoading}>
        {isLoading ? '분석 중...' : '분석하기'}
      </button>

      {analysis && (
        <div>
          <h2>분석 결과</h2>
          <p>레벨: {analysis.level} ({analysis.level_title})</p>
          <p>점수: {analysis.overall_score}</p>
          <p>코드 리뷰: {analysis.code_review}</p>
        </div>
      )}

      {(isStreaming || personaReview) && (
        <div>
          <h2>쉐프의 심사평 {isStreaming && '✍️'}</h2>
          <p style={{ whiteSpace: 'pre-wrap' }}>{personaReview}</p>
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
    <textarea v-model="code" placeholder="코드를 입력하세요"></textarea>
    <button @click="analyze" :disabled="isLoading">
      {{ isLoading ? '분석 중...' : '분석하기' }}
    </button>

    <div v-if="analysis">
      <h2>분석 결과</h2>
      <p>레벨: {{ analysis.level }} ({{ analysis.level_title }})</p>
      <p>점수: {{ analysis.overall_score }}</p>
      <p>코드 리뷰: {{ analysis.code_review }}</p>
    </div>

    <div v-if="isStreaming || personaReview">
      <h2>쉐프의 심사평 <span v-if="isStreaming">✍️</span></h2>
      <p style="white-space: pre-wrap">{{ personaReview }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const code = ref('');
const analysis = ref(null);
const personaReview = ref('');
const isLoading = ref(false);
const isStreaming = ref(false);

async function analyze() {
  isLoading.value = true;
  personaReview.value = '';
  analysis.value = null;

  try {
    const response = await fetch('/api/v1/analysis/analyze/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: code.value,
        language: 'auto',
        include_persona_review: true,
      }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));

          if (data.level !== undefined) {
            analysis.value = data;
            isLoading.value = false;
            isStreaming.value = true;
          } else if (data.token !== undefined) {
            personaReview.value += data.token;
          } else if (data.status === 'completed') {
            isStreaming.value = false;
          }
        }
      }
    }
  } catch (error) {
    console.error('Analysis failed:', error);
    isLoading.value = false;
    isStreaming.value = false;
  }
}
</script>
```

---

## curl 테스트

```bash
curl -X POST http://localhost:8000/api/v1/analysis/analyze/stream \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello():\n    print(\"Hello\")", "language": "auto", "include_persona_review": true}'
```

## 주의사항

1. **CORS**: 프론트엔드와 백엔드 도메인이 다르면 CORS 설정 필요
2. **프록시**: Nginx 등 프록시 사용 시 버퍼링 비활성화 필요
   ```nginx
   proxy_buffering off;
   proxy_cache off;
   ```
3. **타임아웃**: 페르소나 생성에 시간이 걸리므로 클라이언트 타임아웃 설정 주의
