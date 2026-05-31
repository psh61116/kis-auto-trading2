# 📈 KIS Auto Trading System
### 한국투자증권 API 기반 자동매매 시스템

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![KIS OpenAPI](https://img.shields.io/badge/KIS-OpenAPI-red.svg)](https://apiportal.koreainvestment.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📌 개요

한국투자증권(KIS) Open API를 활용하여 주식 자동매매를 실행하는 시스템입니다.  
수업에서 배운 Python 클래스 설계, 모듈화, API 통신 개념을 실제 금융 시스템에 적용했습니다.

**모의투자 / 실전투자 모두 지원하며, 기본값은 안전한 모의투자입니다.**

---

## 🗂️ 프로젝트 구조

```
kis-auto-trading/
│
├── main.py                    # 🚀 메인 실행 파일
│
├── config/
│   ├── __init__.py
│   └── settings.py            # API 키, 전략 파라미터 설정
│
├── core/                      # 핵심 API 통신 모듈
│   ├── __init__.py
│   ├── auth.py                # OAuth2 토큰 발급 및 갱신
│   ├── market_data.py         # 현재가, 일봉 조회, 실시간 스트리밍
│   └── order.py               # 매수/매도 주문, 잔고 조회
│
├── strategy/                  # 매매 전략
│   ├── __init__.py
│   ├── ma_cross.py            # 이동평균 교차 전략 (Golden/Dead Cross)
│   └── rsi.py                 # RSI 과매도/과매수 전략
│
├── utils/
│   ├── __init__.py
│   ├── logger.py              # 로깅 (파일 + 콘솔)
│   └── time_utils.py          # 장 운영시간 체크
│
├── examples/
│   └── quick_start.py         # API 연결 테스트 예제
│
├── tests/
│   └── test_strategy.py       # 유닛 테스트
│
├── logs/                      # 자동 생성 (날짜별 로그)
├── .env.example               # 환경변수 예시 파일
├── .gitignore
└── requirements.txt
```

---

## ⚙️ 설치 및 설정

### 1. 레포지토리 클론

```bash
git clone https://github.com/<YOUR_USERNAME>/kis-auto-trading.git
cd kis-auto-trading
```

### 2. 가상환경 생성 및 패키지 설치

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 한국투자증권 API 키 발급

1. [KIS Developers](https://apiportal.koreainvestment.com) 접속
2. 회원가입 → 앱 등록
3. **App Key** / **App Secret** 발급
4. 모의투자 신청 (처음엔 반드시 모의투자로 시작!)

### 4. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 실제 값 입력:

```env
KIS_APP_KEY=발급받은_앱키
KIS_APP_SECRET=발급받은_앱시크릿
KIS_ACCOUNT_NO=계좌번호-01
KIS_IS_PAPER=true          # 모의투자: true, 실전: false
```

> ⚠️ `.env` 파일은 절대 GitHub에 올리지 마세요! (`.gitignore`에 포함됨)

---

## 🚀 실행 방법

### API 연결 테스트

```bash
python examples/quick_start.py
```

출력 예시:
```
==================================================
📡 한국투자증권 API 연결 테스트
==================================================

[1] 토큰 발급 중...
✅ 토큰 발급 성공 (앞 20자): eyJ0eXAiOiJKV1Qi...

[2] 현재가 조회
----------------------------------------
[005930] 삼성전자    현재가:  75,400원  (+1,200 / +1.62%)  거래량: 15,234,000
[000660] SK하이닉스  현재가: 182,000원  (+3,500 / +1.96%)  거래량:  3,456,000

[3] 잔고 조회
----------------------------------------
예수금    :      50,000,000원
총평가금액:      50,000,000원
...
```

### 자동매매 실행

```bash
python main.py
```

---

## 📊 매매 전략 설명

### 1. 이동평균 교차 전략 (MA Cross)

```
단기 MA > 장기 MA 상향 돌파 → 📈 매수 (Golden Cross)
단기 MA < 장기 MA 하향 돌파 → 📉 매도 (Dead Cross)
```

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `short_ma` | 5 | 단기 이동평균 기간 (일) |
| `long_ma` | 20 | 장기 이동평균 기간 (일) |
| `stop_loss_rate` | -5% | 손절 기준 |
| `take_profit_rate` | +10% | 익절 기준 |

### 2. RSI 전략

```
RSI < 30 (과매도 구간) → 📈 매수
RSI > 70 (과매수 구간) → 📉 매도
```

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `rsi_period` | 14 | RSI 계산 기간 |
| `oversold` | 30 | 과매도 기준 |
| `overbought` | 70 | 과매수 기준 |

---

## 🔧 전략 커스터마이징

`config/settings.py`의 `TradingConfig`를 수정하거나,  
전략 클래스를 직접 파라미터와 함께 초기화하면 됩니다.

```python
from strategy.ma_cross import MovingAverageCrossStrategy
from strategy.rsi import RSIStrategy

# 커스텀 MA 전략
ma_strategy = MovingAverageCrossStrategy(
    symbol="005930",
    short_ma=3,
    long_ma=10,
    quantity=2,
    stop_loss_rate=-0.03,   # -3% 손절
    take_profit_rate=0.05,  # +5% 익절
)

# 커스텀 RSI 전략
rsi_strategy = RSIStrategy(
    symbol="000660",
    rsi_period=14,
    oversold=25,
    overbought=75,
    quantity=1,
)
```

---

## 🏗️ 아키텍처

```
[config]
  └─ settings.py        # API Key, 전략 파라미터 관리
       ↓
[core]
  ├─ auth.py            # 토큰 자동 발급/갱신 (OAuth2)
  ├─ market_data.py     # 현재가 / 일봉 / 실시간 스트리밍
  └─ order.py           # 매수/매도/잔고 API
       ↓
[strategy]
  ├─ ma_cross.py        # 이동평균 교차 전략
  └─ rsi.py             # RSI 전략
       ↓
[main.py]               # 장 운영시간 체크 → 전략 루프 실행
```

---

## 🧪 테스트 실행

```bash
python -m pytest tests/ -v
```

---

## ⚠️ 주의사항

- **처음에는 반드시 모의투자(`KIS_IS_PAPER=true`)로 충분히 검증 후 실전 전환**
- 자동매매는 예상치 못한 손실이 발생할 수 있습니다
- API 호출 빈도 제한(초당 20회)을 초과하지 않도록 `POLLING_INTERVAL` 조정
- 실전 전환 전 전략 백테스트를 강력히 권장합니다

---

## 📚 참고

- [KIS Developers 공식 문서](https://apiportal.koreainvestment.com/apiservice)
- [한국투자증권 OpenAPI GitHub](https://github.com/koreainvestment/open-trading-api)

---

## 📝 License

MIT License
