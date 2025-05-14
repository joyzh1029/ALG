from ultralytics import YOLO
import cv2
import numpy as np
import os

# 모델 로드
model = YOLO("best5.pt")

# 횡단보도 영역 (사각형 대신 다각형 정의)
crosswalk_polygon = np.array([[2, 2], [711, 2], [711, 254], [2, 254]], dtype=np.int32)

# 결과 저장 디렉토리 생성
os.makedirs("result", exist_ok=True)

# 비디오 설정
video_path = "test/sample.mp4"
cap = cv2.VideoCapture(video_path)

fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('result/filtered_output.mp4', fourcc, fps, (width, height))

# 클래스 이름을 문자열로 매핑
target_class_name = "helmet"  # 예시: 헬멧을 착용한 사람
target_class_index = None

# 클래스 인덱스 탐색 (모델에서 helmet가 몇 번인지 확인)
for idx, name in model.names.items():
    if name == target_class_name:
        target_class_index = idx
        break

if target_class_index is None:
    raise ValueError(f"클래스 '{target_class_name}'이(가) 모델 클래스에 없습니다.")

# 프레임별 예측
for result in model.predict(source=video_path, stream=True):
    frame = result.orig_img.copy()

    for box in result.boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])

        if cls != target_class_index:
            continue  # helmet 클래스만 처리

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        # 중심점이 횡단보도 다각형 영역 안에 있는지 검사
        inside = cv2.pointPolygonTest(crosswalk_polygon, (cx, cy), False)

        if inside < 0:  # 영역 밖일 때만 표시
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{model.names[cls]} {conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    out.write(frame)

cap.release()
out.release()
