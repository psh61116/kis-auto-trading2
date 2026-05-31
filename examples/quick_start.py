"""
빠른 테스트용 예제 스크립트
API 연결 확인 및 현재가 조회

실행:
    python examples/quick_start.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from core.auth import kis_auth
from core.market_data import market_data
from core.order import order_manager

SYMBOLS = ["005930", "000660", "035720"]  # 삼성전자, SK하이닉스, 카카오


def main():
    print("=" * 50)
    print("📡 한국투자증권 API 연결 테스트")
    print("=" * 50)

    # 1. 토큰 발급
    print("\n[1] 토큰 발급 중...")
    try:
        token = kis_auth.issue_token()
        print(f"✅ 토큰 발급 성공 (앞 20자): {token[:20]}...")
    except Exception as e:
        print(f"❌ 토큰 발급 실패: {e}")
        print("   → .env 파일에 KIS_APP_KEY, KIS_APP_SECRET 확인")
        return

    # 2. 현재가 조회
    print("\n[2] 현재가 조회")
    print("-" * 40)
    for symbol in SYMBOLS:
        try:
            data = market_data.get_current_price(symbol)
            change_str = f"+{data['change']:,}" if data['change'] >= 0 else f"{data['change']:,}"
            rate_str   = f"+{data['change_rate']:.2f}%" if data['change_rate'] >= 0 else f"{data['change_rate']:.2f}%"
            print(
                f"[{symbol}] {data['name']:<10} "
                f"현재가: {data['price']:>8,}원  "
                f"({change_str} / {rate_str})  "
                f"거래량: {data['volume']:>10,}"
            )
        except Exception as e:
            print(f"[{symbol}] ❌ 조회 실패: {e}")

    # 3. 잔고 조회
    print("\n[3] 잔고 조회")
    print("-" * 40)
    try:
        balance = order_manager.get_balance()
        print(f"예수금    : {balance['cash']:>15,}원")
        print(f"총평가금액: {balance['total_eval']:>15,}원")
        print(f"평가손익  : {balance['total_profit_loss']:>+15,}원")
        print(f"수익률    : {balance['total_profit_rate']:>+14.2f}%")

        if balance["holdings"]:
            print("\n  보유 종목:")
            for h in balance["holdings"]:
                print(
                    f"  [{h['symbol']}] {h['name']:<10} "
                    f"{h['quantity']}주 | "
                    f"평균가 {h['avg_price']:,}원 | "
                    f"수익률 {h['profit_rate']:+.2f}%"
                )
        else:
            print("  보유 종목 없음")
    except Exception as e:
        print(f"❌ 잔고 조회 실패: {e}")

    # 4. 실시간 가격 스트리밍 (5회)
    print("\n[4] 실시간 가격 스트리밍 (삼성전자, 5초)")
    print("-" * 40)
    try:
        for data in market_data.stream_price("005930", interval=1.0, max_count=5):
            print(f"  {data['timestamp']} | {data['price']:,}원")
    except Exception as e:
        print(f"❌ 스트리밍 실패: {e}")

    print("\n✅ 테스트 완료!")


if __name__ == "__main__":
    main()
