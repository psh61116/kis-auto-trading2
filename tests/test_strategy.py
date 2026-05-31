"""
유닛 테스트 - 오프라인 (API 호출 없음)
전략 로직, 유틸리티 함수 테스트
"""
import unittest
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from strategy.rsi import RSIStrategy
from utils.time_utils import is_market_open, now_kst


class TestRSICompute(unittest.TestCase):
    """RSI 계산 로직 테스트"""

    def setUp(self):
        self.strategy = RSIStrategy(symbol="005930")

    def test_rsi_range(self):
        """RSI는 0~100 사이여야 함"""
        import numpy as np
        prices = pd.Series([100, 102, 101, 105, 103, 108, 107, 110,
                            108, 112, 111, 115, 113, 118, 116, 120])
        rsi = RSIStrategy._compute_rsi(prices, period=14)
        valid = rsi.dropna()
        self.assertTrue((valid >= 0).all() and (valid <= 100).all())

    def test_rsi_oversold(self):
        """RSI < 30 과매도 구간"""
        # 지속적으로 하락하는 가격 시리즈
        prices = pd.Series([100 - i * 2 for i in range(20)])
        rsi = RSIStrategy._compute_rsi(prices, period=14)
        last_rsi = rsi.dropna().iloc[-1]
        self.assertLess(last_rsi, 50)  # 하락세에서는 RSI < 50


class TestTimeUtils(unittest.TestCase):
    """시간 유틸리티 테스트"""

    def test_now_kst_is_aware(self):
        """한국 시간은 timezone-aware여야 함"""
        now = now_kst()
        self.assertIsNotNone(now.tzinfo)

    def test_market_open_returns_bool(self):
        """is_market_open은 bool 반환"""
        result = is_market_open()
        self.assertIsInstance(result, bool)


class TestMAStrategy(unittest.TestCase):
    """이동평균 전략 테스트"""

    def test_ma_calculation(self):
        """이동평균 계산 정확성"""
        prices = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        ma5 = prices.rolling(5).mean()
        self.assertAlmostEqual(ma5.iloc[-1], 8.0)
        self.assertAlmostEqual(ma5.iloc[-2], 7.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
