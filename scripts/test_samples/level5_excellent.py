# 레벨 5 테스트 코드 - 우수한 코드 (90점 이상 목표)
# 특징: 짧고 간결, 높은 문서화 비율, 적절한 에러 처리

"""
주문 처리 모듈

이 모듈은 주문 관련 기능을 제공합니다.
- 주문 생성
- 주문 조회
- 주문 취소
"""

from dataclasses import dataclass
from typing import List, Optional
import logging

# 로거 설정
logger = logging.getLogger(__name__)


@dataclass
class Order:
    """주문 엔티티"""
    # 주문 ID
    id: str
    # 사용자 ID
    user_id: str
    # 금액
    amount: int = 0


class OrderRepository:
    """주문 저장소"""

    def __init__(self):
        """초기화"""
        # 저장소
        self._orders = {}

    def save(self, order: Order) -> Order:
        """주문 저장"""
        # 저장
        self._orders[order.id] = order
        return order

    def find(self, order_id: str) -> Optional[Order]:
        """주문 조회"""
        # 조회
        return self._orders.get(order_id)

    def delete(self, order_id: str) -> bool:
        """주문 삭제"""
        # 삭제
        if order_id in self._orders:
            del self._orders[order_id]
            return True
        return False


class OrderService:
    """주문 서비스"""

    def __init__(self, repo: OrderRepository):
        """초기화"""
        # 저장소 주입
        self._repo = repo
        # ID 카운터
        self._counter = 0

    def create(self, user_id: str, amount: int) -> Order:
        """주문 생성"""
        try:
            # ID 생성
            self._counter += 1
            order_id = f"ORD-{self._counter}"
            # 주문 생성
            order = Order(order_id, user_id, amount)
            # 저장
            return self._repo.save(order)
        except Exception as e:
            # 에러 로깅
            logger.error(f"생성 실패: {e}")
            raise

    def get(self, order_id: str) -> Optional[Order]:
        """주문 조회"""
        try:
            # 조회
            return self._repo.find(order_id)
        except Exception as e:
            # 에러 로깅
            logger.error(f"조회 실패: {e}")
            raise

    def cancel(self, order_id: str) -> bool:
        """주문 취소"""
        try:
            # 삭제
            return self._repo.delete(order_id)
        except Exception as e:
            # 에러 로깅
            logger.error(f"취소 실패: {e}")
            raise


def main():
    """메인 함수"""
    # 초기화
    repo = OrderRepository()
    service = OrderService(repo)
    # 주문 생성
    order = service.create("user1", 10000)
    # 출력
    print(f"주문: {order}")


if __name__ == "__main__":
    main()
