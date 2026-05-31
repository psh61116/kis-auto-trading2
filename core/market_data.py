"""
한국투자증권 API - 시세 조회 모듈
주식 현재가, 일봉 데이터 조회
"""
import requests
import json
import time
from typing import Optional
from datetime import datetime
from core.auth import kis_auth
from config.settings import api_config


class MarketData:
    """
    주식 시세 조회 클래스
    
    현재가, 호가, 일봉(OHLCV) 데이터를 조회합니다.
    """

    # ──────────────────────────────────────────
    # 현재가 조회
    # ──────────────────────────────────────────

    def get_current_price(self, symbol: str) -> dict:
        """
        주식 현재가 조회
        
        Args:
            symbol: 종목코드 (예: "005930")
        
        Returns:
            dict: {
                "symbol": str,
                "name": str,
                "price": int,           # 현재가
                "change": int,          # 전일 대비
                "change_rate": float,   # 등락률 (%)
                "volume": int,          # 거래량
                "timestamp": str
            }
        """
        url = (
            api_config.BASE_URL
            + "/uapi/domestic-stock/v1/quotations/inquire-price"
            + f"?fid_cond_mrkt_div_code=J&fid_input_iscd={symbol}"
        )
        headers = kis_auth.get_headers(tr_id="FHKST01010100")

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()

        if data.get("rt_cd") != "0":
            raise RuntimeError(f"현재가 조회 실패 [{symbol}]: {data.get('msg1')}")

        output = data["output"]
        return {
            "symbol": symbol,
            "name": output.get("hts_kor_isnm", ""),
            "price": int(output.get("stck_prpr", 0)),
            "change": int(output.get("prdy_vrss", 0)),
            "change_rate": float(output.get("prdy_ctrt", 0)),
            "volume": int(output.get("acml_vol", 0)),
            "high": int(output.get("stck_hgpr", 0)),
            "low": int(output.get("stck_lwpr", 0)),
            "open": int(output.get("stck_oprc", 0)),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ──────────────────────────────────────────
    # 일봉 데이터 조회
    # ──────────────────────────────────────────

    def get_daily_ohlcv(self, symbol: str, start_date: str, end_date: str) -> list:
        """
        주식 일봉(OHLCV) 데이터 조회
        
        Args:
            symbol: 종목코드 (예: "005930")
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
        
        Returns:
            list of dict: [{
                "date": str,
                "open": int,
                "high": int,
                "low": int,
                "close": int,
                "volume": int
            }, ...]
        """
        url = (
            api_config.BASE_URL
            + "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        )
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": symbol,
            "fid_input_date_1": start_date,
            "fid_input_date_2": end_date,
            "fid_period_div_code": "D",   # D: 일, W: 주, M: 월
            "fid_org_adj_prc": "0",
        }
        headers = kis_auth.get_headers(tr_id="FHKST03010100")

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()

        if data.get("rt_cd") != "0":
            raise RuntimeError(f"일봉 조회 실패 [{symbol}]: {data.get('msg1')}")

        result = []
        for row in data.get("output2", []):
            result.append({
                "date": row.get("stck_bsop_date", ""),
                "open": int(row.get("stck_oprc", 0)),
                "high": int(row.get("stck_hgpr", 0)),
                "low": int(row.get("stck_lwpr", 0)),
                "close": int(row.get("stck_clpr", 0)),
                "volume": int(row.get("acml_vol", 0)),
            })

        return result

    # ──────────────────────────────────────────
    # 실시간 가격 스트리밍 (폴링 방식)
    # ──────────────────────────────────────────

    def stream_price(self, symbol: str, interval: float = 1.0, max_count: int = None):
        """
        실시간 가격 폴링 제너레이터
        
        Args:
            symbol: 종목코드
            interval: 조회 주기 (초)
            max_count: 최대 조회 횟수 (None이면 무한)
        
        Yields:
            dict: 현재가 데이터
        
        Example:
            for data in market.stream_price("005930", interval=1.0):
                print(data["price"])
        """
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


# 싱글턴 인스턴스
market_data = MarketData()
