"""
로깅 유틸리티
파일 + 콘솔 동시 출력
"""
import logging
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)


def get_logger(name: str = "kis-trader", level: int = logging.DEBUG) -> logging.Logger:
    """
    로거 생성 및 반환
    
    Args:
        name: 로거 이름
        level: 로그 레벨
    
    Returns:
        logging.Logger
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # 이미 설정된 로거 재사용

    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(name)s] %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 파일 핸들러 (날짜별)
    log_filename = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
