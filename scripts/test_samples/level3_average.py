# 레벨 3 테스트 코드 - 평균적인 코드 (60-75점 목표)
# 특징: 함수 여러개, 적절한 중첩, 일부 문서화, 기본 에러 처리

"""
간단한 데이터 처리 모듈 level4로 나옴
"""

import json
from typing import List, Dict


def load_data(filepath: str) -> Dict:
    """파일에서 데이터를 로드합니다."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def process_items(items: List[int]) -> List[int]:
    """아이템 리스트를 처리합니다."""
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
        else:
            result.append(0)
    return result


def calculate_average(numbers: List[int]) -> float:
    """평균을 계산합니다."""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def filter_positive(numbers: List[int]) -> List[int]:
    """양수만 필터링합니다."""
    return [n for n in numbers if n > 0]


class DataProcessor:
    def __init__(self):
        self.data = []

    def add_item(self, item):
        self.data.append(item)

    def get_all(self):
        return self.data

    def clear(self):
        self.data = []


def main():
    processor = DataProcessor()
    processor.add_item(1)
    processor.add_item(2)
    processor.add_item(3)

    items = processor.get_all()
    processed = process_items(items)
    avg = calculate_average(processed)

    print(f"Processed: {processed}")
    print(f"Average: {avg}")


if __name__ == "__main__":
    main()
