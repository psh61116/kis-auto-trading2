"""
시간 관련 유틸리티
장 운영 시간 체크 등
"""
from datetime import datetime, time
import pytz

KST = pytz.timezone("Asia/Seoul")

MARKET_OPEN  = time(9, 0)
MARKET_CLOSE = time(15, 30)

WEEKDAY_MAP = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}


def now_kst() -> datetime:
    """현재 한국 시간 반환"""
    return datetime.now(KST)


def is_market_open() -> bool:
    """
    현재 장이 열려있는지 확인
    
    Returns:
        bool: 장 운영 중이면 True
    """
    now = now_kst()
    # 주말 제외
    if now.weekday() >= 5:
        return False
    current_time = now.time()
    return MARKET_OPEN <= current_time <= MARKET_CLOSE


def seconds_until_market_open() -> float:
    """장 시작까지 남은 초 반환"""
    now = now_kst()
    if now.weekday() >= 5:
        # 주말이면 다음 월요일
        days_ahead = 7 - now.weekday()
        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
        target = target + __import__("datetime").timedelta(days=days_ahead)
    else:
        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now.time() >= MARKET_OPEN:
            return 0  # 이미 장 시작
    return max(0, (target - now).total_seconds())
