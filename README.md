KIS Auto Trading Bot
한국투자증권(KIS) Open API와 yfinance를 활용한(시세데이터를 불러오는데 어려움이 있어서 yfinance를 활용하여 시세를 불러오도록 수정하였습니다..)이동평균선(MA) 크로스 전략 자동매매 프로그램입니다.
프로젝트 구조
kis-auto-trading2/

config/ — API 키 및 매매 설정
core/ — 주문 실행, API 연동 핵심 로직
strategy/ — 이동평균선 크로스 전략 구현
utils/ — 보조 유틸리티
examples/ — 사용 예시
tests/ — 테스트 코드
main.py — 실행 진입점

매매 전략
이동평균선(MA) 크로스 전략

단기 이동평균선이 장기 이동평균선을 상향 돌파 시 매수, 하향 돌파 시 매도.

시세 데이터는 yfinance를 통해 수신.
설치 및 실행

pip install -r requirements.txt
.env.example을 .env로 복사 후 KIS API 키 입력
python main.py 실행

 
