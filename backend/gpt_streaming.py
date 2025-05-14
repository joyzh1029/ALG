from ultralytics import YOLO
import cv2
import numpy as np
import os
import base64
import asyncio
import time

# 결과 저장 디렉토리 생성
os.makedirs("result", exist_ok=True)

# 모델 및 설정 전역 변수 (성능 향상을 위해)
model = None
crosswalk_polygon = np.array([[2, 2], [711, 2], [711, 254], [2, 254]], dtype=np.int32)
target_class_name = "helmet"
target_class_index = None

async def process_frame(frame, model, target_class_index, crosswalk_polygon):
    """단일 프레임 처리 함수"""
    # 프레임 복사
    processed_frame = frame.copy()
    
    # YOLO 추론 (single image)
    results = model.predict(source=frame, stream=False)[0]
    
    detection_count = 0
    
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
            cv2.rectangle(processed_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{model.names[cls]} {conf:.2f}"
            cv2.putText(processed_frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            detection_count += 1
    
    return processed_frame, detection_count

async def initialize_model():
    """모델 초기화 함수"""
    global model, target_class_index
    
    if model is None:
        try:
            # 모델 로드
            model = YOLO("models/best5.pt")
            
            # 타겟 클래스 인덱스 찾기
            for idx, name in model.names.items():
                if name == target_class_name:
                    target_class_index = idx
                    break
                    
            if target_class_index is None:
                print(f"경고: 클래스 '{target_class_name}'이(가) 모델 클래스에 없습니다.")
        except Exception as e:
            print(f"모델 로드 오류: {e}")
            return False
    
    return True

async def get_stream_frame():
    """스트리밍 프레임을 가져오는 함수"""
    # 모델 초기화 확인
    if not await initialize_model():
        # 모델 초기화 실패 시 오류 이미지 반환
        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(dummy_img, "Model initialization failed", (50, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        _, buffer = cv2.imencode('.jpg', dummy_img)
        return base64.b64encode(buffer).decode('utf-8')
    
    # 실시간 스트림 URL
    stream_url = "https://kbscctv-cache.loomex.net/lowStream/_definst_/9999_low.stream/chunklist.m3u8"
    
    # 비디오 캡처 객체 생성
    cap = cv2.VideoCapture(stream_url)
    
    # 스트림을 열 수 없는 경우 로컬 비디오 파일 시도
    if not cap.isOpened():
        print("스트리밍 URL을 열 수 없습니다. 로컬 비디오 파일로 대체합니다.")
        
        # 로컬 비디오 파일 경로 (result 폴더에 있는 파일 사용)
        local_videos = [f for f in os.listdir("result") if f.endswith(('.mp4', '.avi', '.mov'))]
        
        if local_videos:
            local_video_path = os.path.join("result", local_videos[0])
            cap = cv2.VideoCapture(local_video_path)
        
        # 로컬 비디오도 없는 경우
        if not cap.isOpened():
            dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(dummy_img, "No video source available", (50, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            _, buffer = cv2.imencode('.jpg', dummy_img)
            return base64.b64encode(buffer).decode('utf-8')
    
    try:
        # 프레임 읽기
        ret, frame = cap.read()
        
        if not ret:
            # 프레임을 읽을 수 없는 경우 더미 이미지 반환
            dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(dummy_img, "No frame available", (50, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            _, buffer = cv2.imencode('.jpg', dummy_img)
            return base64.b64encode(buffer).decode('utf-8')
        
        # 프레임 처리
        processed_frame, detection_count = await process_frame(frame, model, target_class_index, crosswalk_polygon)
        
        # 현재 시간 표시
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(processed_frame, current_time, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # 감지 정보 표시
        cv2.putText(processed_frame, f"Helmet detected: {detection_count}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # 처리된 프레임을 JPEG로 인코딩 후 base64로 변환
        _, buffer = cv2.imencode('.jpg', processed_frame)
        base64_image = base64.b64encode(buffer).decode('utf-8')
        
        return base64_image
    
    except Exception as e:
        print(f"프레임 처리 오류: {e}")
        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(dummy_img, f"Error: {str(e)}", (50, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        _, buffer = cv2.imencode('.jpg', dummy_img)
        return base64.b64encode(buffer).decode('utf-8')
    
    finally:
        # 자원 해제
        cap.release()

async def start_streaming_server(websocket):
    """WebSocket을 통한 스트리밍 서버 시작"""
    try:
        print("CCTV 스트리밍 서버 시작")
        while True:
            # 프레임 가져오기
            base64_frame = await get_stream_frame()
            
            # 클라이언트로 전송
            await websocket.send_text(base64_frame)
            
            # 프레임 레이트 조절 (약 5 FPS - 부하 감소)
            await asyncio.sleep(0.2)
    except Exception as e:
        print(f"스트리밍 오류: {e}")
    finally:
        print("CCTV 스트리밍 서버 종료")
