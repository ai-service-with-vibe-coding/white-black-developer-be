# 레벨 4 테스트 코드 - 좋은 코드 (75-90점 목표)
# 특징: 잘 구조화된 클래스, 좋은 문서화, 에러 처리, 타입 힌트

"""
사용자 관리 모듈

이 모듈은 사용자 데이터를 관리하기 위한 클래스와 함수를 제공합니다.
SOLID 원칙을 준수하여 설계되었습니다.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

# 로거 설정
logger = logging.getLogger(__name__)


@dataclass
class User:
    """사용자 데이터 클래스"""
    id: int
    name: str
    email: str
    is_active: bool = True


class UserRepositoryInterface(ABC):
    """사용자 저장소 인터페이스 (DIP 준수)"""

    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]:
        """ID로 사용자 조회"""
        pass

    @abstractmethod
    def find_all(self) -> List[User]:
        """모든 사용자 조회"""
        pass

    @abstractmethod
    def save(self, user: User) -> User:
        """사용자 저장"""
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """사용자 삭제"""
        pass


class InMemoryUserRepository(UserRepositoryInterface):
    """인메모리 사용자 저장소 구현"""

    def __init__(self):
        self._users: Dict[int, User] = {}
        self._next_id: int = 1

    def find_by_id(self, user_id: int) -> Optional[User]:
        """ID로 사용자 조회"""
        return self._users.get(user_id)

    def find_all(self) -> List[User]:
        """모든 사용자 조회"""
        return list(self._users.values())

    def save(self, user: User) -> User:
        """사용자 저장"""
        if user.id == 0:
            user.id = self._next_id
            self._next_id += 1
        self._users[user.id] = user
        logger.info(f"User saved: {user.id}")
        return user

    def delete(self, user_id: int) -> bool:
        """사용자 삭제"""
        if user_id in self._users:
            del self._users[user_id]
            logger.info(f"User deleted: {user_id}")
            return True
        return False


class UserService:
    """사용자 서비스 클래스 (SRP 준수)"""

    def __init__(self, repository: UserRepositoryInterface):
        self._repository = repository

    def create_user(self, name: str, email: str) -> User:
        """새 사용자 생성"""
        try:
            user = User(id=0, name=name, email=email)
            return self._repository.save(user)
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise

    def get_user(self, user_id: int) -> Optional[User]:
        """사용자 조회"""
        try:
            return self._repository.find_by_id(user_id)
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            raise

    def get_all_users(self) -> List[User]:
        """모든 사용자 조회"""
        try:
            return self._repository.find_all()
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            raise

    def deactivate_user(self, user_id: int) -> bool:
        """사용자 비활성화"""
        try:
            user = self._repository.find_by_id(user_id)
            if user:
                user.is_active = False
                self._repository.save(user)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to deactivate user: {e}")
            raise


def main():
    """메인 함수"""
    # 의존성 주입
    repository = InMemoryUserRepository()
    service = UserService(repository)

    # 사용자 생성
    user1 = service.create_user("홍길동", "hong@example.com")
    user2 = service.create_user("김철수", "kim@example.com")

    # 사용자 조회
    all_users = service.get_all_users()
    print(f"Total users: {len(all_users)}")

    # 사용자 비활성화
    service.deactivate_user(user1.id)


if __name__ == "__main__":
    main()
