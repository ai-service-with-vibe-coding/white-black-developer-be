"""
코드 전처리기
GitHub 저장소 코드를 AI 모델에 적합한 형태로 전처리
"""
import os
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 분석 대상 확장자
SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
}

# 제외할 디렉토리
EXCLUDED_DIRS = {
    "node_modules",
    "__pycache__",
    ".git",
    ".svn",
    "venv",
    "env",
    ".venv",
    "dist",
    "build",
    "target",
    ".idea",
    ".vscode",
    "vendor",
    ".cache",
    "coverage",
    ".nyc_output",
}

# 제외할 파일 패턴
EXCLUDED_PATTERNS = [
    r".*\.min\.js$",
    r".*\.min\.css$",
    r".*\.bundle\.js$",
    r".*\.map$",
    r".*\.lock$",
    r"package-lock\.json$",
    r"yarn\.lock$",
    r"poetry\.lock$",
]


@dataclass
class CodeFile:
    """코드 파일 정보"""
    path: str
    relative_path: str
    language: str
    content: str
    line_count: int
    size_bytes: int


@dataclass
class CodeChunk:
    """코드 청크 (모델 입력용)"""
    file_path: str
    language: str
    content: str
    start_line: int
    end_line: int
    chunk_index: int


class CodePreprocessor:
    """코드 전처리기"""

    def __init__(
        self,
        max_file_size: int = 100_000,  # 100KB
        max_chunk_lines: int = 200,
        chunk_overlap_lines: int = 20,
    ):
        self.max_file_size = max_file_size
        self.max_chunk_lines = max_chunk_lines
        self.chunk_overlap_lines = chunk_overlap_lines
        self._excluded_patterns = [re.compile(p) for p in EXCLUDED_PATTERNS]

    def scan_repository(self, repo_path: str) -> List[CodeFile]:
        """
        저장소 스캔하여 분석 대상 파일 목록 반환

        Args:
            repo_path: 저장소 루트 경로

        Returns:
            CodeFile 리스트
        """
        code_files = []
        repo_path = Path(repo_path)

        if not repo_path.exists():
            logger.error(f"Repository path not found: {repo_path}")
            return []

        logger.info(f"Scanning repository: {repo_path}")

        for root, dirs, files in os.walk(repo_path):
            # 제외 디렉토리 필터링
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(repo_path)

                # 확장자 확인
                ext = file_path.suffix.lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue

                # 제외 패턴 확인
                if self._is_excluded(str(relative_path)):
                    continue

                # 파일 크기 확인
                try:
                    size = file_path.stat().st_size
                    if size > self.max_file_size:
                        logger.debug(f"Skipping large file: {relative_path} ({size} bytes)")
                        continue

                    # 파일 읽기
                    content = self._read_file(file_path)
                    if content is None:
                        continue

                    line_count = content.count("\n") + 1

                    code_files.append(CodeFile(
                        path=str(file_path),
                        relative_path=str(relative_path),
                        language=SUPPORTED_EXTENSIONS[ext],
                        content=content,
                        line_count=line_count,
                        size_bytes=size,
                    ))

                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {e}")
                    continue

        logger.info(f"Found {len(code_files)} code files to analyze")
        return code_files

    def _is_excluded(self, file_path: str) -> bool:
        """제외 패턴 확인"""
        for pattern in self._excluded_patterns:
            if pattern.match(file_path):
                return True
        return False

    def _read_file(self, file_path: Path) -> Optional[str]:
        """파일 읽기 (인코딩 자동 감지)"""
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp949"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")
                return None

        logger.warning(f"Could not decode file: {file_path}")
        return None

    def chunk_code(self, code_file: CodeFile) -> List[CodeChunk]:
        """
        코드를 청크로 분할

        Args:
            code_file: CodeFile 인스턴스

        Returns:
            CodeChunk 리스트
        """
        lines = code_file.content.split("\n")
        chunks = []

        if len(lines) <= self.max_chunk_lines:
            # 청크 분할 불필요
            chunks.append(CodeChunk(
                file_path=code_file.relative_path,
                language=code_file.language,
                content=code_file.content,
                start_line=1,
                end_line=len(lines),
                chunk_index=0,
            ))
        else:
            # 청크로 분할
            chunk_index = 0
            start = 0

            while start < len(lines):
                end = min(start + self.max_chunk_lines, len(lines))
                chunk_lines = lines[start:end]

                chunks.append(CodeChunk(
                    file_path=code_file.relative_path,
                    language=code_file.language,
                    content="\n".join(chunk_lines),
                    start_line=start + 1,
                    end_line=end,
                    chunk_index=chunk_index,
                ))

                chunk_index += 1
                start = end - self.chunk_overlap_lines

        return chunks

    def prepare_for_analysis(
        self, repo_path: str
    ) -> Tuple[List[CodeFile], List[CodeChunk]]:
        """
        분석을 위한 전처리 수행

        Args:
            repo_path: 저장소 경로

        Returns:
            (CodeFile 리스트, CodeChunk 리스트)
        """
        code_files = self.scan_repository(repo_path)

        all_chunks = []
        for code_file in code_files:
            chunks = self.chunk_code(code_file)
            all_chunks.extend(chunks)

        logger.info(f"Prepared {len(all_chunks)} chunks from {len(code_files)} files")

        return code_files, all_chunks

    def get_language_stats(self, code_files: List[CodeFile]) -> Dict[str, int]:
        """언어별 파일 수 통계"""
        stats = {}
        for cf in code_files:
            stats[cf.language] = stats.get(cf.language, 0) + 1
        return stats

    def get_total_lines(self, code_files: List[CodeFile]) -> int:
        """총 코드 라인 수"""
        return sum(cf.line_count for cf in code_files)

    def extract_functions(self, code: str, language: str) -> List[Dict]:
        """
        코드에서 함수/메서드 추출 (간단한 휴리스틱)

        Args:
            code: 소스 코드
            language: 프로그래밍 언어

        Returns:
            함수 정보 리스트
        """
        functions = []

        # 언어별 함수 패턴
        patterns = {
            "python": r"^(?:async\s+)?def\s+(\w+)\s*\(",
            "javascript": r"(?:async\s+)?function\s+(\w+)\s*\(|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(?.*?\)?\s*=>",
            "typescript": r"(?:async\s+)?function\s+(\w+)\s*\(|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(?.*?\)?\s*=>",
            "java": r"(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\(",
            "go": r"func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(",
        }

        pattern = patterns.get(language)
        if not pattern:
            return functions

        lines = code.split("\n")
        for i, line in enumerate(lines):
            match = re.search(pattern, line)
            if match:
                func_name = match.group(1) or (match.group(2) if match.lastindex > 1 else None)
                if func_name:
                    functions.append({
                        "name": func_name,
                        "line": i + 1,
                        "signature": line.strip()[:100],
                    })

        return functions


# 전역 인스턴스
_preprocessor: Optional[CodePreprocessor] = None


def get_preprocessor() -> CodePreprocessor:
    """전처리기 싱글톤"""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = CodePreprocessor()
    return _preprocessor
