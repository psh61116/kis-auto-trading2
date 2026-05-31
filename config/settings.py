"""
한국투자증권 API 자동매매 시스템 - 설정 파일
"""
import os
from dataclasses import dataclass

# ───────────────────────────────────────────────
# 환경변수에서 키 로딩 (.env 파일 또는 시스템 환경변수)
# ───────────────────────────────────────────────

@dataclass
class APIConfig:
    """한국투자증권 API 설정"""
    APP_KEY: str = os.getenv("KIS_APP_KEY", "")
    APP_SECRET: str = os.getenv("KIS_APP_SECRET", "")
    ACCOUNT_NO: str = os.getenv("KIS_ACCOUNT_NO", "")       # 예: "12345678-01"
    IS_PAPER: bool = os.getenv("KIS_IS_PAPER", "true").lower() == "true"  # 모의투자 여부

    # API 엔드포인트
    BASE_URL_REAL: str = "https://openapi.koreainvestment.com:9443"
    BASE_URL_PAPER: str = "https://openapivts.koreainvestment.com:29443"

    @property
    def BASE_URL(self) -> str:
        return self.BASE_URL_PAPER if self.IS_PAPER else self.BASE_URL_REAL

    @property
    def ACCOUNT_PREFIX(self) -> str:
        """계좌번호 앞 8자리"""
        return self.ACCOUNT_NO.split("-")[0] if "-" in self.ACCOUNT_NO else self.ACCOUNT_NO[:8]

    @property
    def ACCOUNT_SUFFIX(self) -> str:
        """계좌번호 뒤 2자리"""
        return self.ACCOUNT_NO.split("-")[1] if "-" in self.ACCOUNT_NO else self.ACCOUNT_NO[8:]


@dataclass
class TradingConfig:
    """매매 전략 설정"""
    # 매매 대상 종목 (종목코드 리스트)
    SYMBOLS: list = None

    # 매매 관련
    MAX_BUY_AMOUNT: int = 1_000_000       # 1회 최대 매수금액 (원)
    STOP_LOSS_RATE: float = -0.05         # 손절 기준 (-5%)
    TAKE_PROFIT_RATE: float = 0.10        # 익절 기준 (+10%)

    # 이동평균 전략 파라미터
    SHORT_MA: int = 5                     # 단기 이동평균 (일)
    LONG_MA: int = 20                     # 장기 이동평균 (일)

    # 실행 관련
    POLLING_INTERVAL: float = 1.0         # 가격 조회 주기 (초)
    MARKET_OPEN: str = "09:00"
    MARKET_CLOSE: str = "15:30"

    def __post_init__(self):
        if self.SYMBOLS is None:
            self.SYMBOLS = ["005930", "000660"]  # 삼성전자, SK하이닉스 (기본값)


# 전역 설정 인스턴스
api_config = APIConfig()
trading_config = TradingConfig()
