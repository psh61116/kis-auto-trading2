"""
한국투자증권 자동매매 시스템 - 메인 실행 파일

실행 방법:
    python main.py

환경변수 (.env 또는 시스템):
    KIS_APP_KEY      - 한국투자증권 App Key
    KIS_APP_SECRET   - 한국투자증권 App Secret
    KIS_ACCOUNT_NO   - 계좌번호 (예: 12345678-01)
    KIS_IS_PAPER     - 모의투자 여부 (true/false, 기본 true)
"""
import time
import signal
import sys
from dotenv import load_dotenv

load_dotenv()

from config.settings import api_config, trading_config
from core.auth import kis_auth
from core.market_data import market_data
from core.order import order_manager
from strategy.ma_cross import MovingAverageCrossStrategy
from strategy.rsi import RSIStrategy
from utils.logger import get_logger
from utils.time_utils import is_market_open, seconds_until_market_open

logger = get_logger("Main")


# ──────────────────────────────────────────────────
# Graceful Shutdown 처리
# ──────────────────────────────────────────────────

_running = True

def _signal_handler(sig, frame):
    global _running
    logger.info("종료 신호 수신 (Ctrl+C). 안전하게 종료합니다...")
    _running = False

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ──────────────────────────────────────────────────
# 메인 실행
# ──────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("🚀 한국투자증권 자동매매 시스템 시작")
    logger.info(f"   모드: {'📝 모의투자' if api_config.IS_PAPER else '💰 실전투자'}")
    logger.info(f"   계좌: {api_config.ACCOUNT_NO}")
    logger.info(f"   종목: {trading_config.SYMBOLS}")
    logger.info("=" * 60)

    # 토큰 발급
    try:
        kis_auth.issue_token()
    except Exception as e:
        logger.error(f"토큰 발급 실패: {e}")
        logger.error("App Key / App Secret / 계좌번호를 확인하세요.")
        sys.exit(1)

    # 잔고 확인
    try:
        balance = order_manager.get_balance()
        logger.info(f"💰 예수금: {balance['cash']:,}원 | 총평가: {balance['total_eval']:,}원")
        for h in balance["holdings"]:
            logger.info(
                f"   [{h['symbol']}] {h['name']} | {h['quantity']}주 | "
                f"평균가: {h['avg_price']:,} | 수익률: {h['profit_rate']:.2f}%"
            )
    except Exception as e:
        logger.warning(f"잔고 조회 실패: {e}")

    # 전략 초기화
    strategies = []
    for symbol in trading_config.SYMBOLS:
        strategies.append(
            MovingAverageCrossStrategy(
                symbol=symbol,
                short_ma=trading_config.SHORT_MA,
                long_ma=trading_config.LONG_MA,
                quantity=1,
                stop_loss_rate=trading_config.STOP_LOSS_RATE,
                take_profit_rate=trading_config.TAKE_PROFIT_RATE,
            )
        )

    logger.info(f"전략 초기화 완료: MA({trading_config.SHORT_MA}/{trading_config.LONG_MA}) × {len(strategies)}개 종목")

    # ──────────────────────────────────────────
    # 메인 루프
    # ──────────────────────────────────────────
    while _running:
        try:
            if not is_market_open():
                wait_sec = seconds_until_market_open()
                if wait_sec > 0:
                    logger.info(f"⏳ 장 마감 시간. {wait_sec/3600:.1f}시간 후 재개됩니다.")
                    # 1분 단위로 체크
                    for _ in range(min(60, int(wait_sec))):
                        if not _running:
                            break
                        time.sleep(1)
                continue

            # 각 종목 전략 실행
            for strategy in strategies:
                if not _running:
                    break
                try:
                    action = strategy.run_once()
                    if action:
                        logger.info(f"[{strategy.symbol}] 액션: {action}")
                except Exception as e:
                    logger.error(f"[{strategy.symbol}] 전략 실행 오류: {e}", exc_info=True)

            time.sleep(trading_config.POLLING_INTERVAL)

        except Exception as e:
            logger.error(f"메인 루프 오류: {e}", exc_info=True)
            time.sleep(5)

    logger.info("✅ 자동매매 시스템 정상 종료")


if __name__ == "__main__":
    main()
