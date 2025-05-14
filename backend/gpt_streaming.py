from ultralytics import YOLO
import cv2
import numpy as np
import os

# 모델 로드
model = YOLO("best5.pt")

# 횡단보도 영역 다각형 정의
crosswalk_polygon = np.array([[2, 2], [711, 2], [711, 254], [2, 254]], dtype=np.int32)

# 결과 저장 디렉토리 생성
os.makedirs("result", exist_ok=True)

# 실시간 스트림 URL (예: RTSP, HTTP Live Stream 등)
# 스트리밍 URL로 교체하세요
stream_url = "https://kbscctv-cache.loomex.net/lowStream/_definst_/9999_low.stream/chunklist.m3u8"  # 예: rtsp://..., http://.../video

cap = cv2.VideoCapture(stream_url)

if not cap.isOpened():
    raise ValueError("스트리밍을 열 수 없습니다. URL 또는 연결을 확인하세요.")

# 해상도 및 FPS (스트리밍의 경우 종종 0으로 나올 수 있음)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
fps = cap.get(cv2.CAP_PROP_FPS) or 25.0  # 기본 FPS fallback

# 결과 저장 (원한다면)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('result/stream_output.mp4', fourcc, fps, (width, height))

# 클래스 이름을 문자열로 매핑
target_class_name = "helmet"
target_class_index = None

for idx, name in model.names.items():
    if name == target_class_name:
        target_class_index = idx
        break

if target_class_index is None:
    raise ValueError(f"클래스 '{target_class_name}'이(가) 모델 클래스에 없습니다.")

# 스트리밍 루프
while True:
    ret, frame = cap.read()
    if not ret:
        print("프레임을 가져올 수 없습니다. 연결이 끊겼거나 종료되었습니다.")
        break

    # YOLO 추론 (single image)
    results = model.predict(source=frame, stream=False)[0]

    for box in results.boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])

        if cls != target_class_index:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        inside = cv2.pointPolygonTest(crosswalk_polygon, (cx, cy), False)

        if inside < 0:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{model.names[cls]} {conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    out.write(frame)

    # 원한다면 실시간 창에 띄우기
    cv2.imshow("Live CCTV Monitor", frame)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()
