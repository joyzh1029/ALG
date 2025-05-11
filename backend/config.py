from pathlib import Path

# 기본 설정
BASE_DIR = Path(__file__).resolve().parent

# YOLO 모델 설정
MODEL_PATH = str(BASE_DIR / "models" / "helmet_detection.pt")  # 다운로드 또는 학습이 필요한 헬멧 감지 모델
CONFIDENCE_THRESHOLD = 0.5  # 감지 신뢰도 임계값

# 클래스 설정
CLASSES = {
    0: "motorcycle",  # 오토바이
    1: "person",      # 사람
    2: "helmet",      # 헬멧
    3: "no_helmet"    # 헬멧 미착용
}

# API 설정
API_DESCRIPTION = """
오토바이 운전자의 헬멧 착용 여부를 판단하는 API
"""
API_TITLE = "Helmet Detection API"
API_VERSION = "1.0.0"

# WebSocket 설정
WS_PING_INTERVAL = 30  # WebSocket ping 간격(초)
