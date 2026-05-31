"""
한국투자증권 API - 주문 모듈
시장가/지정가 매수·매도, 잔고 조회
"""
import requests
import json
from typing import Optional
from datetime import datetime
from core.auth import kis_auth
from config.settings import api_config


class OrderManager:
    """
    주식 주문 관리 클래스
    
    매수/매도 주문 실행 및 잔고/체결 조회를 담당합니다.
    모의투자(IS_PAPER=True)와 실전투자를 자동으로 구분합니다.
    """

    # 거래 ID 매핑 (실전 vs 모의)
    TR_IDS = {
        "buy": {
            "real": "TTTC0802U",
            "paper": "VTTC0802U",
        },
        "sell": {
            "real": "TTTC0801U",
            "paper": "VTTC0801U",
        },
        "balance": {
            "real": "TTTC8434R",
            "paper": "VTTC8434R",
        },
        "order_list": {
            "real": "TTTC8001R",
            "paper": "VTTC8001R",
        },
    }

    def _get_tr_id(self, action: str) -> str:
        mode = "paper" if api_config.IS_PAPER else "real"
        return self.TR_IDS[action][mode]

    # ──────────────────────────────────────────
    # 매수 주문
    # ──────────────────────────────────────────

    def buy(
        self,
        symbol: str,
        quantity: int,
        price: int = 0,
        order_type: str = "market",
    ) -> dict:
        """
        매수 주문
        
        Args:
            symbol: 종목코드 (예: "005930")
            quantity: 수량
            price: 가격 (지정가일 때 사용, 시장가면 0)
            order_type: "market" (시장가) | "limit" (지정가)
        
        Returns:
            dict: 주문 결과
        """
        return self._send_order(
            action="buy",
            symbol=symbol,
            quantity=quantity,
            price=price,
            order_type=order_type,
        )

    # ──────────────────────────────────────────
    # 매도 주문
    # ──────────────────────────────────────────

    def sell(
        self,
        symbol: str,
        quantity: int,
        price: int = 0,
        order_type: str = "market",
    ) -> dict:
        """
        매도 주문
        
        Args:
            symbol: 종목코드
            quantity: 수량
            price: 가격 (지정가일 때 사용)
            order_type: "market" | "limit"
        
        Returns:
            dict: 주문 결과
        """
        return self._send_order(
            action="sell",
            symbol=symbol,
            quantity=quantity,
            price=price,
            order_type=order_type,
        )

    # ──────────────────────────────────────────
    # 공통 주문 전송
    # ──────────────────────────────────────────

    def _send_order(
        self,
        action: str,
        symbol: str,
        quantity: int,
        price: int,
        order_type: str,
    ) -> dict:
        """내부 주문 전송 메서드"""
        url = api_config.BASE_URL + "/uapi/domestic-stock/v1/trading/order-cash"

        # 주문구분 코드: 00=지정가, 01=시장가
        ord_dvsn = "01" if order_type == "market" else "00"

        payload = {
            "CANO": api_config.ACCOUNT_PREFIX,
            "ACNT_PRDT_CD": api_config.ACCOUNT_SUFFIX,
            "PDNO": symbol,
            "ORD_DVSN": ord_dvsn,
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price) if order_type == "limit" else "0",
        }

        tr_id = self._get_tr_id(action)
        headers = kis_auth.get_headers(tr_id=tr_id)

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        data = response.json()

        if data.get("rt_cd") != "0":
            raise RuntimeError(
                f"주문 실패 [{action.upper()} {symbol}]: {data.get('msg1')}"
            )

        output = data.get("output", {})
        result = {
            "action": action,
            "symbol": symbol,
            "quantity": quantity,
            "order_type": order_type,
            "price": price,
            "order_no": output.get("ODNO", ""),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_paper": api_config.IS_PAPER,
        }
        print(
            f"[Order] {'📈 매수' if action == 'buy' else '📉 매도'} "
            f"{symbol} {quantity}주 | {order_type} | 주문번호: {result['order_no']}"
        )
        return result

    # ──────────────────────────────────────────
    # 잔고 조회
    # ──────────────────────────────────────────

    def get_balance(self) -> dict:
        """
        계좌 잔고 조회
        
        Returns:
            dict: {
                "cash": int,            # 예수금
                "holdings": list,       # 보유 종목 리스트
                "total_eval": int,      # 총평가금액
                "total_profit_rate": float
            }
        """
        url = api_config.BASE_URL + "/uapi/domestic-stock/v1/trading/inquire-balance"
        params = {
            "CANO": api_config.ACCOUNT_PREFIX,
            "ACNT_PRDT_CD": api_config.ACCOUNT_SUFFIX,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "N",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }
        tr_id = self._get_tr_id("balance")
        headers = kis_auth.get_headers(tr_id=tr_id)

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()

        if data.get("rt_cd") != "0":
            raise RuntimeError(f"잔고 조회 실패: {data.get('msg1')}")

        output2 = data.get("output2", [{}])[0]
        holdings = []
        for item in data.get("output1", []):
            if int(item.get("hldg_qty", 0)) > 0:
                holdings.append({
                    "symbol": item.get("pdno", ""),
                    "name": item.get("prdt_name", ""),
                    "quantity": int(item.get("hldg_qty", 0)),
                    "avg_price": int(item.get("pchs_avg_pric", 0)),
                    "current_price": int(item.get("prpr", 0)),
                    "profit_loss": int(item.get("evlu_pfls_amt", 0)),
                    "profit_rate": float(item.get("evlu_pfls_rt", 0)),
                })

        return {
            "cash": int(output2.get("dnca_tot_amt", 0)),
            "holdings": holdings,
            "total_eval": int(output2.get("tot_evlu_amt", 0)),
            "total_profit_loss": int(output2.get("evlu_pfls_smtl_amt", 0)),
            "total_profit_rate": float(output2.get("asst_icdc_erng_rt", 0)),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


# 싱글턴 인스턴스
order_manager = OrderManager()
