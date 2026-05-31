"""
RSI(상대강도지수) 전략
- RSI < 30 (과매도) → 매수
- RSI > 70 (과매수) → 매도
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from core.market_data import market_data
from core.order import order_manager
from config.settings import trading_config
from utils.logger import get_logger

logger = get_logger("RSI_Strategy")


class RSIStrategy:
    """
    RSI 기반 역추세 전략
    
    Parameters:
        symbol: 종목코드
        rsi_period: RSI 계산 기간 (기본 14일)
        oversold: 과매도 기준값 (기본 30)
        overbought: 과매수 기준값 (기본 70)
        quantity: 1회 매매 수량
    """

    def __init__(
        self,
        symbol: str,
        rsi_period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
        quantity: int = 1,
    ):
        self.symbol = symbol
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.quantity = quantity
        self.position: Optional[dict] = None

    # ──────────────────────────────────────────
    # RSI 계산
    # ──────────────────────────────────────────

    @staticmethod
    def _compute_rsi(series: pd.Series, period: int) -> pd.Series:
        """
        RSI 계산
        
        Args:
            series: 종가 시리즈
            period: 기간
        
        Returns:
            pd.Series: RSI 값 (0~100)
        """
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _fetch_df(self) -> pd.DataFrame:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=self.rsi_period * 4)).strftime("%Y%m%d")
        rows = market_data.get_daily_ohlcv(self.symbol, start_date, end_date)
        df = pd.DataFrame(rows)
        df["close"] = df["close"].astype(float)
        df = df.sort_values("date").reset_index(drop=True)
        df["rsi"] = self._compute_rsi(df["close"], self.rsi_period)
        return df

    # ──────────────────────────────────────────
    # 신호 실행
    # ──────────────────────────────────────────

    def run_once(self) -> Optional[str]:
        """
        RSI 전략 1회 실행
        
        Returns:
            str | None: 실행 결과
        """
        df = self._fetch_df()
        current_rsi = df["rsi"].iloc[-1]
        current_price = int(df["close"].iloc[-1])

        logger.debug(f"[{self.symbol}] RSI: {current_rsi:.2f} | 가격: {current_price:,}")

        if current_rsi < self.oversold and self.position is None:
            order_manager.buy(self.symbol, self.quantity)
            self.position = {
                "entry_price": current_price,
                "entry_time": datetime.now().isoformat(),
                "quantity": self.quantity,
            }
            logger.info(
                f"[{self.symbol}] ✅ 매수 (과매도) | RSI: {current_rsi:.2f} | 가격: {current_price:,}"
            )
            return "buy"

        elif current_rsi > self.overbought and self.position is not None:
            order_manager.sell(self.symbol, self.quantity)
            self.position = None
            logger.info(
                f"[{self.symbol}] ✅ 매도 (과매수) | RSI: {current_rsi:.2f} | 가격: {current_price:,}"
            )
            return "sell"

        return None
