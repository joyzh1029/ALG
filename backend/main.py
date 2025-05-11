from fastapi import FastAPI, UploadFile, File, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from ultralytics import YOLO
import json
from typing import List, Dict
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

# YOLO 모델 로드
try:
    model = YOLO(MODEL_PATH)
except Exception as e:
    print(f"Error loading model: {e}")
    # 커스텀 모델 로드 실패 시 사전 학습된 모델 사용
    model = YOLO("models/yolo11n.pt")

def process_detection(img) -> Dict:
    """이미지 감지 처리 및 결과 반환"""
    results = model(img)
    detections = []
    has_motorcycle = False
    has_person = False
    has_helmet = False
    no_helmet = False
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = box.conf[0].item()
            cls = box.cls[0].item()
            class_name = model.names[int(cls)]
            
            if conf > CONFIDENCE_THRESHOLD:
                if class_name == "motorcycle":
                    has_motorcycle = True
                elif class_name == "person":
                    has_person = True
                elif class_name == "helmet":
                    has_helmet = True
                elif class_name == "no_helmet":
                    no_helmet = True
                
                detection = {
                    "bbox": [round(x, 2) for x in [x1, y1, x2, y2]],
                    "confidence": round(conf, 3),
                    "class": class_name
                }
                detections.append(detection)
    
    warning_message = ""
    if has_motorcycle and has_person:
        if not has_helmet or no_helmet:
            warning_message = "경고: 헬멧을 착용하지 않은 오토바이 운전자가 감지되었습니다!"
        else:
            warning_message = "안전: 헬멧을 착용한 오토바이 운전자가 감지되었습니다."
    
    return {
        "timestamp": datetime.now().isoformat(),
        "detections": detections,
        "warning": warning_message,
        "has_helmet": has_helmet,
        "has_motorcycle": has_motorcycle,
        "has_person": has_person
    }

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
        _, buffer = cv2.imencode('.jpg', img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
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
