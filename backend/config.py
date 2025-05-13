from pathlib import Path

# 기본 설정
BASE_DIR = Path(__file__).resolve().parent

# 모델 설정
YOLO_WORLD_MODEL_PATH = str(BASE_DIR / "models" / "yolov8s-world.pt")  # YOLO-World 모델 경로
YOLOV11N_MODEL_PATH = str(BASE_DIR / "models" / "yolo11n.pt")  # YOLO11n 모델 경로
HELMET_MODEL_PATH = str(BASE_DIR / "models" / "helmet_model.pt")  # 헬멧 감지 모델 경로
CONFIDENCE_THRESHOLD = 0.5  # 감지 신뢰도 임계값

# 클래스 설정
CLASSES = {
    0: "motorcycle",  # 오토바이
    1: "person",      # 사람
    2: "helmet",      # 헬멧
    3: "no_helmet"    # 헬멧 미착용
}

# 표현식 설정
RIDER_MOTORCYCLE_PAIRING_THRESHOLD = 0.6  # 라이더와 오토바이 페어링 임계값
HELMET_RESULT_AGGREGATION_THRESHOLD = 0.5  # 헬멧 결과 집계 임계값

# 동적 크롭 설정
RIDER_CROP_PADDING = 0.2  # 라이더 크롭 시 추가 여백 비율

# 라벨 시각화 설정
LABEL_COLORS = {
    "motorcycle": (0, 0, 255),    # 빨간색
    "person": (0, 255, 0),        # 녹색
    "helmet": (255, 0, 0),        # 파란색
    "no_helmet": (255, 0, 255)    # 보라색
}
LABEL_THICKNESS = 2
LABEL_FONT_SCALE = 0.6

# API 설정
API_DESCRIPTION = """
오토바이 운전자의 헬멧 착용 여부를 판단하는 API
"""
API_TITLE = "Helmet Detection API"
API_VERSION = "1.0.0"

# WebSocket 설정
WS_PING_INTERVAL = 30  # WebSocket ping 간격(초)
