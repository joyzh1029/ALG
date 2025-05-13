from fastapi import FastAPI, UploadFile, File, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from ultralytics import YOLO
import json
from typing import List, Dict, Tuple, Optional
import base64
from datetime import datetime
import asyncio
from config import *

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션 환경에서는 구체적인 오리진 설정 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 모델 로드
try:
    yolo_world_model = YOLO(YOLO_WORLD_MODEL_PATH)
    yolov11n_model = YOLO(YOLOV11N_MODEL_PATH)
    helmet_model = YOLO(HELMET_MODEL_PATH)
except Exception as e:
    print(f"Error loading models: {e}")
    # 모델 로드 실패 시 기본 모델 사용
    yolo_world_model = YOLO("models/yolov8s-world.pt")
    yolov11n_model = YOLO("models/yolo11n.pt")
    helmet_model = YOLO("models/helmet_model.pt")

def rider_motorcycle_pairing(detections: List[Dict]) -> List[Dict]:
    """라이더와 오토바이 페어링 처리"""
    riders = [d for d in detections if d["class"] == "person"]
    motorcycles = [d for d in detections if d["class"] == "motorcycle"]
    pairs = []
    
    for rider in riders:
        rider_center_x = (rider["bbox"][0] + rider["bbox"][2]) / 2
        rider_center_y = (rider["bbox"][1] + rider["bbox"][3]) / 2
        
        best_match = None
        best_distance = float('inf')
        
        for motorcycle in motorcycles:
            moto_center_x = (motorcycle["bbox"][0] + motorcycle["bbox"][2]) / 2
            moto_center_y = (motorcycle["bbox"][1] + motorcycle["bbox"][3]) / 2
            
            # 유클리드 거리 계산
            distance = ((rider_center_x - moto_center_x) ** 2 + (rider_center_y - moto_center_y) ** 2) ** 0.5
            
            # 거리가 임계값보다 작으면 페어링
            if distance < best_distance:
                best_distance = distance
                best_match = motorcycle
        
        if best_match and best_distance < RIDER_MOTORCYCLE_PAIRING_THRESHOLD * max(
            rider["bbox"][2] - rider["bbox"][0],
            rider["bbox"][3] - rider["bbox"][1]
        ):
            pairs.append({
                "rider": rider,
                "motorcycle": best_match,
                "confidence": 1.0 - (best_distance / (best_match["bbox"][2] - best_match["bbox"][0]))
            })
    
    return pairs

def rider_crop(img: np.ndarray, rider: Dict) -> Tuple[np.ndarray, List[int]]:
    """라이더 부분만 크롭"""
    x1, y1, x2, y2 = map(int, rider["bbox"])
    
    # 패딩 추가
    height, width = img.shape[:2]
    padding_x = int((x2 - x1) * RIDER_CROP_PADDING)
    padding_y = int((y2 - y1) * RIDER_CROP_PADDING)
    
    crop_x1 = max(0, x1 - padding_x)
    crop_y1 = max(0, y1 - padding_y)
    crop_x2 = min(width, x2 + padding_x)
    crop_y2 = min(height, y2 + padding_y)
    
    cropped_img = img[crop_y1:crop_y2, crop_x1:crop_x2]
    crop_coords = [crop_x1, crop_y1, crop_x2, crop_y2]
    
    return cropped_img, crop_coords

def helmet_result_aggregation(helmet_detections: List[Dict]) -> Dict:
    """헬멧 감지 결과 집계"""
    helmets = [d for d in helmet_detections if d["class"] == "helmet"]
    no_helmets = [d for d in helmet_detections if d["class"] == "no_helmet"]
    
    # 헬멧과 노헬멧 감지 결과 중 가장 높은 신뢰도 값 찾기
    max_helmet_conf = max([h["confidence"] for h in helmets]) if helmets else 0
    max_no_helmet_conf = max([nh["confidence"] for nh in no_helmets]) if no_helmets else 0
    
    # 결과 판단
    has_helmet = max_helmet_conf > HELMET_RESULT_AGGREGATION_THRESHOLD
    no_helmet_detected = max_no_helmet_conf > HELMET_RESULT_AGGREGATION_THRESHOLD
    
    if has_helmet and not no_helmet_detected:
        status = "helmet"
        message = "안전: 헬멧을 착용한 오토바이 운전자가 감지되었습니다."
    elif no_helmet_detected:
        status = "no_helmet"
        message = "경고: 헬멧을 착용하지 않은 오토바이 운전자가 감지되었습니다!"
    else:
        status = "unknown"
        message = "헬멧 착용 여부를 판단할 수 없습니다."
    
    return {
        "status": status,
        "message": message,
        "helmet_confidence": max_helmet_conf,
        "no_helmet_confidence": max_no_helmet_conf,
        "detections": helmet_detections
    }

def helmet_label_visualization(img: np.ndarray, results: Dict) -> np.ndarray:
    """감지 결과 시각화"""
    img_copy = img.copy()
    
    # 모든 감지 결과 표시
    for detection in results.get("all_detections", []):
        x1, y1, x2, y2 = map(int, detection["bbox"])
        cls = detection["class"]
        conf = detection["confidence"]
        
        color = LABEL_COLORS.get(cls, (255, 255, 255))  # 기본 색상은 흰색
        
        # 바운딩 박스 그리기
        cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, LABEL_THICKNESS)
        
        # 라벨 텍스트
        label = f"{cls}: {conf:.2f}"
        
        # 라벨 배경 그리기
        text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, LABEL_FONT_SCALE, LABEL_THICKNESS)[0]
        cv2.rectangle(img_copy, (x1, y1 - text_size[1] - 5), (x1 + text_size[0], y1), color, -1)
        
        # 라벨 텍스트 그리기
        cv2.putText(img_copy, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, LABEL_FONT_SCALE, (255, 255, 255), LABEL_THICKNESS)
    
    # 경고 메시지 표시
    if results.get("warning"):
        cv2.putText(img_copy, results["warning"], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    return img_copy

def process_detection(img: np.ndarray) -> Dict:
    """이미지 감지 처리 및 결과 반환"""
    # 1. 입력 이미지 처리
    input_img = img.copy()
    
    # 2. YOLO-World 모델과 YOLO11n모델로 초기 감지
    print("2. YOLO-World 모델과 YOLO11n모델로 초기 감지")
    yolo_world_results = yolo_world_model(input_img)
    print(f"   YOLO-World 결과: {len(yolo_world_results)}")
    yolov11n_results = yolov11n_model(input_img)
    print(f"   YOLO11n 결과: {len(yolov11n_results)}")
    
    # 결과 통합
    all_detections = []
    
    # YOLO-World 결과 처리
    for result in yolo_world_results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = box.conf[0].item()
            cls = box.cls[0].item()
            class_name = yolo_world_model.names[int(cls)]
            
            if conf > CONFIDENCE_THRESHOLD:
                detection = {
                    "bbox": [round(x, 2) for x in [x1, y1, x2, y2]],
                    "confidence": round(conf, 3),
                    "class": class_name,
                    "model": "yolo_world"
                }
                all_detections.append(detection)
    
    # YOLOv1n 결과 처리
    print("   YOLOv11n 결과 처리")
    for result in yolov11n_results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = box.conf[0].item()
            cls = box.cls[0].item()
            class_name = yolov11n_model.names[int(cls)]
            
            if conf > CONFIDENCE_THRESHOLD:
                detection = {
                    "bbox": [round(x, 2) for x in [x1, y1, x2, y2]],
                    "confidence": round(conf, 3),
                    "class": class_name,
                    "model": "yolov11n"
                }
                all_detections.append(detection)
    
    # 3. 라이더와 오토바이 페어링
    rider_pairs = rider_motorcycle_pairing(all_detections)
    
    # 결과 저장
    results = {
        "timestamp": datetime.now().isoformat(),
        "all_detections": all_detections,
        "rider_pairs": [],
        "helmet_results": []
    }
    
    # 4. 각 라이더에 대해 처리
    for pair in rider_pairs:
        rider = pair["rider"]
        motorcycle = pair["motorcycle"]
        
        # 5. 라이더 부분 크롭
        rider_img, crop_coords = rider_crop(input_img, rider)
        
        # 6. 헬멧 모델로 헬멧 감지
        helmet_results = helmet_model(rider_img)
        
        helmet_detections = []
        for result in helmet_results:
            boxes = result.boxes
            for box in boxes:
                # 크롭된 이미지 내의 좌표
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = box.conf[0].item()
                cls = box.cls[0].item()
                class_name = helmet_model.names[int(cls)]
                
                if conf > CONFIDENCE_THRESHOLD:
                    # 원본 이미지 좌표로 변환
                    orig_x1 = crop_coords[0] + x1
                    orig_y1 = crop_coords[1] + y1
                    orig_x2 = crop_coords[0] + x2
                    orig_y2 = crop_coords[1] + y2
                    
                    detection = {
                        "bbox": [round(x, 2) for x in [orig_x1, orig_y1, orig_x2, orig_y2]],
                        "confidence": round(conf, 3),
                        "class": class_name,
                        "model": "helmet_model"
                    }
                    helmet_detections.append(detection)
                    all_detections.append(detection)
        
        # 7. 헬멧 결과 집계
        helmet_result = helmet_result_aggregation(helmet_detections)
        
        # 페어 결과 저장
        pair_result = {
            "rider": rider,
            "motorcycle": motorcycle,
            "helmet_result": helmet_result,
            "crop_coords": crop_coords
        }
        results["rider_pairs"].append(pair_result)
        results["helmet_results"].append(helmet_result)
    
    # 경고 메시지 설정
    warning_message = ""
    for helmet_result in results["helmet_results"]:
        if helmet_result["status"] == "no_helmet":
            warning_message = helmet_result["message"]
            break
        elif helmet_result["status"] == "helmet" and not warning_message:
            warning_message = helmet_result["message"]
    
    results["warning"] = warning_message
    
    # 8. 라벨 시각화
    visualized_img = helmet_label_visualization(input_img, results)
    results["visualized_img"] = visualized_img
    
    return results

@app.get("/")
async def root():
    return {"message": "Helmet Detection API is running"}

@app.post("/detect")
async def detect_helmet(file: UploadFile = File(...)):
    try:
        # 업로드된 이미지 읽기
        contents = await file.read()
        nparr = np.fromstring(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # 감지 처리
        result = process_detection(img)
        
        # 이미지를 base64 형식으로 변환
        _, buffer = cv2.imencode('.jpg', result["visualized_img"])
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # 결과에서 이미지 객체 제거 (JSON 직렬화 불가)
        del result["visualized_img"]
        result["image"] = img_base64
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                # 수신된 base64 이미지 데이터 처리
                img_data = base64.b64decode(data.split(',')[1])
                nparr = np.fromstring(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img is None:
                    raise ValueError("Invalid image data")
                
                # 감지 처리
                result = process_detection(img)
                
                # 이미지를 base64 형식으로 변환
                _, buffer = cv2.imencode('.jpg', result["visualized_img"])
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # 결과에서 이미지 객체 제거 (JSON 직렬화 불가)
                del result["visualized_img"]
                result["image"] = img_base64
                
                # 감지 결과 전송
                await websocket.send_text(json.dumps(result))
                
                # 헬멧 미착용 감지 시 추가 경고 전송
                if result["warning"].startswith("경고"):
                    await asyncio.sleep(0.5)  # 경고 메시지 독립 표시를 위한 지연
                    await websocket.send_text(json.dumps({
                        "alert": True,
                        "message": result["warning"]
                    }))
            
            except ValueError as ve:
                await websocket.send_text(json.dumps({
                    "error": str(ve)
                }))
            
            # 연결 유지를 위한 주기적인 ping
            await asyncio.sleep(WS_PING_INTERVAL)
            
    except Exception as e:
        print(f"WebSocket Error: {e}")
    finally:
        await websocket.close()
