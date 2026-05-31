"""
한국투자증권 API - 인증 모듈
OAuth2 토큰 발급 및 관리
"""
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Optional
from config.settings import api_config


class KISAuth:
    """
    한국투자증권 API OAuth2 인증 클래스
    
    토큰을 자동으로 발급하고 만료 시 재발급합니다.
    """

    TOKEN_URL = "/oauth2/tokenP"

    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    # ──────────────────────────────────────────
    # 토큰 발급
    # ──────────────────────────────────────────

    def issue_token(self) -> str:
        """
        Access Token 발급
        
        Returns:
            str: 발급된 Access Token
        
        Raises:
            RuntimeError: 토큰 발급 실패 시
        """
        url = api_config.BASE_URL + self.TOKEN_URL
        payload = {
            "grant_type": "client_credentials",
            "appkey": api_config.APP_KEY,
            "appsecret": api_config.APP_SECRET,
        }
        headers = {"content-type": "application/json"}

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        data = response.json()

        if "access_token" not in data:
            raise RuntimeError(f"토큰 발급 실패: {data}")

        self._access_token = data["access_token"]
        # 토큰 만료 시간 (보통 24시간, 여유 두고 23시간으로 설정)
        self._token_expires_at = datetime.now() + timedelta(hours=23)

        print(f"[Auth] 토큰 발급 성공 | 만료: {self._token_expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        return self._access_token

    # ──────────────────────────────────────────
    # 토큰 조회 (자동 갱신 포함)
    # ──────────────────────────────────────────

    @property
    def access_token(self) -> str:
        """
        유효한 Access Token 반환
        만료 임박 시 자동 재발급
        """
        if self._is_token_expired():
            self.issue_token()
        return self._access_token

    def _is_token_expired(self) -> bool:
        """토큰 만료 여부 확인"""
        if self._access_token is None or self._token_expires_at is None:
            return True
        return datetime.now() >= self._token_expires_at

    # ──────────────────────────────────────────
    # 공통 헤더 생성
    # ──────────────────────────────────────────

    def get_headers(self, tr_id: str, extra: Optional[dict] = None) -> dict:
        """
        API 요청 공통 헤더 생성
        
        Args:
            tr_id: 거래 ID (예: FHKST01010100)
            extra: 추가 헤더 딕셔너리
        
        Returns:
            dict: 완성된 헤더
        """
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": api_config.APP_KEY,
            "appsecret": api_config.APP_SECRET,
            "tr_id": tr_id,
        }
        if extra:
            headers.update(extra)
        return headers


# 싱글턴 인스턴스
kis_auth = KISAuth()
