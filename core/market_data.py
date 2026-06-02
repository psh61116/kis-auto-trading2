"""
한국투자증권 API - 시세 조회 모듈
주식 현재가, 일봉 데이터 조회 (yfinance 사용)
"""
import time
import yfinance as yf
from datetime import datetime
from typing import Optional


# 종목코드 → 야후 티커 변환
def to_yahoo_ticker(symbol: str) -> str:
    return f"{symbol}.KS"


class MarketData:

    def get_current_price(self, symbol: str) -> dict:
        ticker = yf.Ticker(to_yahoo_ticker(symbol))
        info = ticker.fast_info
        price = int(info.last_price)
        prev_close = int(info.previous_close)
        change = price - prev_close
        change_rate = round((change / prev_close) * 100, 2)
        return {
            "symbol": symbol,
            "name": symbol,
            "price": price,
            "change": change,
            "change_rate": change_rate,
            "volume": int(info.three_month_average_volume or 0),
            "high": int(info.day_high),
            "low": int(info.day_low),
            "open": int(info.open),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def get_daily_ohlcv(self, symbol: str, start_date: str, end_date: str) -> list:
        ticker = yf.Ticker(to_yahoo_ticker(symbol))
        start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
        end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
        df = ticker.history(start=start, end=end)
        result = []
        for date, row in df.iterrows():
            result.append({
                "date": date.strftime("%Y%m%d"),
                "open": int(row["Open"]),
                "high": int(row["High"]),
                "low": int(row["Low"]),
                "close": int(row["Close"]),
                "volume": int(row["Volume"]),
            })
        return result

    def stream_price(self, symbol: str, interval: float = 1.0, max_count: int = None):
        count = 0
        try:
            while True:
                data = self.get_current_price(symbol)
                yield data
                count += 1
                if max_count and count >= max_count:
                    break
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[MarketData] 스트리밍 중단됨")


market_data = MarketData()
