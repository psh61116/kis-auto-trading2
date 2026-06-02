"""
이동평균 교차 전략 (Golden Cross / Dead Cross)
- 단기 MA가 장기 MA를 상향 돌파 → 매수 (Golden Cross)
- 단기 MA가 장기 MA를 하향 돌파 → 매도 (Dead Cross)
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from core.market_data import market_data
from core.order import order_manager
from config.settings import api_config, trading_config
from utils.logger import get_logger

logger = get_logger("MA_Strategy")


class MovingAverageCrossStrategy:
    """
    이동평균 교차 전략
    
    Parameters:
        symbol: 종목코드
        short_ma: 단기 이동평균 기간 (기본 5일)
        long_ma: 장기 이동평균 기간 (기본 20일)
        quantity: 1회 매매 수량
        stop_loss_rate: 손절 기준 (기본 -5%)
        take_profit_rate: 익절 기준 (기본 +10%)
    """

    def __init__(
        self,
        symbol: str,
        short_ma: int = None,
        long_ma: int = None,
        quantity: int = 1,
        stop_loss_rate: float = None,
        take_profit_rate: float = None,
    ):
        self.symbol = symbol
        self.short_ma = short_ma or trading_config.SHORT_MA
        self.long_ma = long_ma or trading_config.LONG_MA
        self.quantity = quantity
        self.stop_loss_rate = stop_loss_rate or trading_config.STOP_LOSS_RATE
        self.take_profit_rate = take_profit_rate or trading_config.TAKE_PROFIT_RATE

        # 상태 관리
        self.position: Optional[dict] = None   # 현재 보유 포지션
        self.last_signal: Optional[str] = None # 마지막 신호 ("buy" / "sell" / None)

    # ──────────────────────────────────────────
    # 이동평균 계산
    # ──────────────────────────────────────────

    def _fetch_ohlcv(self) -> pd.DataFrame:
        """일봉 데이터 로드 및 DataFrame 변환"""
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=self.long_ma * 3)).strftime("%Y%m%d")

        rows = market_data.get_daily_ohlcv(self.symbol, start_date, end_date)
        df = pd.DataFrame(rows)
        df["close"] = df["close"].astype(float)
        df = df.sort_values("date").reset_index(drop=True)
        return df

    def _compute_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """MA 계산 및 신호 생성"""
        df[f"ma{self.short_ma}"] = df["close"].rolling(self.short_ma).mean()
        df[f"ma{self.long_ma}"] = df["close"].rolling(self.long_ma).mean()

        df["signal"] = None
        for i in range(1, len(df)):
            prev_short = df[f"ma{self.short_ma}"].iloc[i - 1]
            prev_long  = df[f"ma{self.long_ma}"].iloc[i - 1]
            curr_short = df[f"ma{self.short_ma}"].iloc[i]
            curr_long  = df[f"ma{self.long_ma}"].iloc[i]

            if pd.isna(prev_short) or pd.isna(prev_long):
                continue

            # Golden Cross
            if prev_short <= prev_long and curr_short > curr_long:
                df.at[i, "signal"] = "buy"
            # Dead Cross
            elif prev_short >= prev_long and curr_short < curr_long:
                df.at[i, "signal"] = "sell"

        return df

    # ──────────────────────────────────────────
    # 손익 기반 청산 체크
    # ──────────────────────────────────────────

    def _check_exit(self, current_price: int) -> Optional[str]:
        """손절/익절 조건 체크"""
        if self.position is None:
            return None

        entry_price = self.position["entry_price"]
        pnl_rate = (current_price - entry_price) / entry_price

        if pnl_rate <= self.stop_loss_rate:
            logger.warning(
                f"[{self.symbol}] 🔴 손절 | 수익률: {pnl_rate:.2%} | "
                f"매수가: {entry_price:,} → 현재가: {current_price:,}"
            )
            return "stop_loss"

        if pnl_rate >= self.take_profit_rate:
            logger.info(
                f"[{self.symbol}] 🟢 익절 | 수익률: {pnl_rate:.2%} | "
                f"매수가: {entry_price:,} → 현재가: {current_price:,}"
            )
            return "take_profit"

        return None

    # ──────────────────────────────────────────
    # 신호 실행
    # ──────────────────────────────────────────

    def run_once(self) -> Optional[str]:
        """
        전략을 1회 실행합니다.
        
        Returns:
            str | None: 실행된 액션 ("buy" / "sell" / "stop_loss" / "take_profit" / None)
        """
        # 현재가 조회
        logger.info(f"[{self.symbol}] 현재가 조회 중...")
        current = market_data.get_current_price(self.symbol)
        current_price = current["price"]

        # 손절/익절 체크
        exit_reason = self._check_exit(current_price)
        if exit_reason:
            order_manager.sell(self.symbol, self.quantity)
            self.position = None
            self.last_signal = "sell"
            return exit_reason

        # MA 신호 체크
        logger.info(f"[{self.symbol}] 일봉 조회 중...")
        df = self._fetch_ohlcv()
        df = self._compute_signals(df)

        latest_signal = df["signal"].iloc[-1]

        if latest_signal == "buy" and self.position is None:
            order_manager.buy(self.symbol, self.quantity)
            self.position = {
                "entry_price": current_price,
                "entry_time": datetime.now().isoformat(),
                "quantity": self.quantity,
            }
            self.last_signal = "buy"
            logger.info(
                f"[{self.symbol}] ✅ 매수 실행 | 가격: {current_price:,} | "
                f"MA{self.short_ma}/{self.long_ma} 골든크로스"
            )
            return "buy"

        elif latest_signal == "sell" and self.position is not None:
            order_manager.sell(self.symbol, self.quantity)
            self.position = None
            self.last_signal = "sell"
            logger.info(
                f"[{self.symbol}] ✅ 매도 실행 | 가격: {current_price:,} | "
                f"MA{self.short_ma}/{self.long_ma} 데드크로스"
            )
            return "sell"

        logger.debug(
            f"[{self.symbol}] 대기 | 현재가: {current_price:,} | "
            f"신호: {latest_signal or '없음'} | 포지션: {'보유' if self.position else '없음'}"
        )
        return None
