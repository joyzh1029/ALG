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
    print(f"라이더-오토바이 페어링， {len(detections)} ")
    
    # 모델이 인식한 모든 클래스를 출력
    classes = [d["class"] for d in detections]
    unique_classes = set(classes)
    print(f"CLASSES: {unique_classes}")
    print(f"CLASSES COUNT: {[(cls, classes.count(cls)) for cls in unique_classes]}")
    
    riders = [d for d in detections if d["class"] == "person"]
    motorcycles = [d for d in detections if d["class"] == "motorcycle"]
    
    print(f"라이더: {len(riders)}  오토바이: {len(motorcycles)}")
    
    # 라이더가 없으면 다른 클래스를 사용하여 찾음
    if len(riders) == 0:
        possible_rider_classes = ["person", "rider", "human", "pedestrian"]
        for cls in possible_rider_classes:
            riders = [d for d in detections if d["class"].lower() == cls.lower()]
            if len(riders) > 0:
                print(f"라이더 클래스 '{cls}'로 찾은 {len(riders)}")
                break
    
    if len(motorcycles) == 0:
        possible_moto_classes = ["motorcycle", "motorbike", "bike", "motor"]
        for cls in possible_moto_classes:
            motorcycles = [d for d in detections if d["class"].lower() == cls.lower()]
            if len(motorcycles) > 0:
                print(f"오토바이 클래스 '{cls}'로 찾은 {len(motorcycles)}")
                break
    
    pairs = []
    
    for rider_idx, rider in enumerate(riders):
        rider_center_x = (rider["bbox"][0] + rider["bbox"][2]) / 2
        rider_center_y = (rider["bbox"][1] + rider["bbox"][3]) / 2
        
        best_match = None
        best_distance = float('inf')
        
        for moto_idx, motorcycle in enumerate(motorcycles):
            moto_center_x = (motorcycle["bbox"][0] + motorcycle["bbox"][2]) / 2
            moto_center_y = (motorcycle["bbox"][1] + motorcycle["bbox"][3]) / 2
            
            # 유클리드 거리 계산
            distance = ((rider_center_x - moto_center_x) ** 2 + (rider_center_y - moto_center_y) ** 2) ** 0.5
            
            # 거리가 임계값보다 작으면 페어링
            if distance < best_distance:
                best_distance = distance
                best_match = motorcycle
        
        # 페어링 임계값 계산
        rider_width = rider["bbox"][2] - rider["bbox"][0]
        rider_height = rider["bbox"][3] - rider["bbox"][1]
        threshold = RIDER_MOTORCYCLE_PAIRING_THRESHOLD * max(rider_width, rider_height)
        
        if best_match and best_distance < threshold:
            confidence = 1.0 - (best_distance / (best_match["bbox"][2] - best_match["bbox"][0]))
            print(f"라이더 {rider_idx} 페어링 성공，오토바이: {best_match['class']}, 거리: {best_distance:.2f}，임계값: {threshold:.2f}，신뢰도: {confidence:.2f}")
            pairs.append({
                "rider": rider,
                "motorcycle": best_match,
                "confidence": confidence
            })
        else:
            print(f"라이더 {rider_idx} 페어링 실패，오토바이: {best_match['class']}, 거리: {best_distance:.2f}，임계값: {threshold:.2f}")
    
    print(f"페어링 결과: {len(pairs)} 대")
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
    
    print(f"      감지된 객체: {[d['class'] for d in helmet_detections]}")
    print(f"      헬멧 객체 수: {len(helmets)}, 노헬멧 객체 수: {len(no_helmets)}")
    
    # 헬멧과 노헬멧 감지 결과 중 가장 높은 신뢰도 값 찾기
    max_helmet_conf = max([h["confidence"] for h in helmets]) if helmets else 0
    max_no_helmet_conf = max([nh["confidence"] for nh in no_helmets]) if no_helmets else 0
    
    # 결과 판단
    has_helmet = max_helmet_conf > HELMET_RESULT_AGGREGATION_THRESHOLD
    no_helmet_detected = max_no_helmet_conf > HELMET_RESULT_AGGREGATION_THRESHOLD
    
    # 헬멧 위치 확인
    helmet_on_head = False
    if has_helmet and helmets:
        # 헬멧이 머리 위에 있는지 확인
        for helmet in helmets:
            # 헬멧의 y 좌표
            helmet_y1 = helmet["bbox"][1]  # 헬멧 상단 y좌표
            helmet_y2 = helmet["bbox"][3]  # 헬멧 하단 y좌표
            helmet_height = helmet_y2 - helmet_y1
            
            # 헬멧이 머리 위에 있는지 확인
            if helmet_y1 < helmet_height * 1.5:  # 헬멧이 머리 위에 있는지 확인
                helmet_on_head = True
                print(f"      헬멧이 머리 위에 있음: y1={helmet_y1}, height={helmet_height}")
                break
            else:
                print(f"      헬멧이 머리 위에 없음: y1={helmet_y1}, height={helmet_height}")
    
    print(f"      헬멧 감지: {has_helmet}, 헬멧 위치 올바름: {helmet_on_head}")
    
    # 중요: 헬멧 감지 객체가 있지만 헬멧/노헬멧으로 분류되지 않은 경우에도 
    # 미착용으로 처리 
    if len(helmet_detections) > 0 and len(helmets) == 0 and len(no_helmets) == 0:
        print("      헬멧 관련 객체가 감지되었으나 헬멧/노헬멧으로 분류되지 않음 -> 미착용으로 처리")
        status = "no_helmet"
        message = "경고: 헬멧을 착용하지 않은 오토바이 운전자가 감지되었습니다!"
    elif has_helmet and helmet_on_head:
        status = "helmet"
        message = "안전: 헬멧을 착용한 오토바이 운전자가 감지되었습니다."
        status = "helmet"
        message = "안전: 헬멧을 착용한 오토바이 운전자가 감지되었습니다."
    elif has_helmet and not helmet_on_head:
        status = "helmet_not_worn"
        message = "경고: 헬멧이 감지되었으나 착용하지 않았습니다!"
    elif no_helmet_detected:
        status = "no_helmet"
        message = "경고: 헬멧을 착용하지 않은 오토바이 운전자가 감지되었습니다!"
    else:
        # 헬멧 감지 결과가 없는 경우에도 미착용으로 처리 (如果没有头盔检测结果，也视为未佩戴)
        status = "no_helmet"
        message = "경고: 헬멧을 착용하지 않은 것으로 판단됩니다!"
    
    return {
        "status": status,
        "message": message,
        "helmet_confidence": max_helmet_conf,
        "no_helmet_confidence": max_no_helmet_conf,
        "helmet_on_head": helmet_on_head if has_helmet else False,
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
    
    # 헬멧 미착용 라이더 강조 표시
    for pair in results.get("rider_pairs", []):
        helmet_result = pair.get("helmet_result", {})
        rider = pair.get("rider", {})
        status = helmet_result.get("status", "")
        
        if status in ["no_helmet", "helmet_not_worn"]:
            # 라이더 바운딩 박스를 빨간색으로 강조
            x1, y1, x2, y2 = map(int, rider["bbox"])
            cv2.rectangle(img_copy, (x1, y1), (x2, y2), (0, 0, 255), LABEL_THICKNESS * 2)
            
            # 경고 메시지
            warning_text = "헬멧 미착용!" if status == "no_helmet" else "헬멧 착용 필요!"
            text_size = cv2.getTextSize(warning_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            
            # 경고 텍스트 배경
            cv2.rectangle(img_copy, (x1, y1 - text_size[1] - 10), (x1 + text_size[0], y1), (0, 0, 255), -1)
            
            # 경고 텍스트
            cv2.putText(img_copy, warning_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # 전체 경고 메시지 표시
    warning_count = sum(1 for pair in results.get("rider_pairs", []) 
                      if pair.get("helmet_result", {}).get("status", "") in ["no_helmet", "helmet_not_worn"])
    
    if warning_count > 0:
        warning = f"경고: {warning_count}명의 라이더가 헬멧을 올바르게 착용하지 않았습니다!"
        cv2.putText(img_copy, warning, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    return img_copy

def process_detection(img: np.ndarray) -> Dict:
    """이미지 감지 처리 및 결과 반환"""
    # 1. 입력 이미지 처리
    print("1. 이미지 처리")
    input_img = img.copy()
    
    # 2. YOLO11n모델로 초기 감지 (只使用yolo11n模型)
    print("2. YOLO11n 모델로 초기 감지")
    yolov11n_results = yolov11n_model(input_img)
    print(f"   YOLO11n 결과: {len(yolov11n_results)}")
    
    # 결과 통합
    all_detections = []
    
    # YOLOv11n 결과 처리
    print("   YOLOv11n 결과 처리")
    for result in yolov11n_results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = box.conf[0].item()
            cls = box.cls[0].item()
            class_name = yolov11n_model.names[int(cls)]
            
            # "person"및"motorcycle" 클래스만 처리
            if conf > CONFIDENCE_THRESHOLD and class_name in ["person", "motorcycle"]:
                detection = {
                    "bbox": [round(x, 2) for x in [x1, y1, x2, y2]],
                    "confidence": round(conf, 3),
                    "class": class_name,
                    "model": "yolov11n"
                }
                all_detections.append(detection)
    
    print(f"   감지된 객체 수: {len(all_detections)}")
    print(f"   감지된 클래스: {set(d['class'] for d in all_detections)}")
    
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
    print("4. 라이더-오토바이 페어링")
    for pair_index, pair in enumerate(rider_pairs):
        print(f"   {pair_index+1}번째 라이더-오토바이 페어링")
        rider = pair["rider"]
        motorcycle = pair["motorcycle"]
        
        print(f"   라이더 정보: bbox={rider['bbox']}, confidence={rider['confidence']}")
        print(f"   오토바이 정보: bbox={motorcycle['bbox']}, confidence={motorcycle['confidence']}")
        
        # 5. 라이더 부분 크롭
        print("   5. 라이더 부분 크롭")
        try:
            rider_img, crop_coords = rider_crop(input_img, rider)
            print(f"      크롭 성공: 구역={crop_coords}, 크롭 이미지 크기={rider_img.shape}")
            
            # 6. 헬멧 모델로 헬멧 감지
            print("   6. 헬멧 모델로 헬멧 감지")
            helmet_results = helmet_model(rider_img)
            
            # 6.1 YOLO-World 모델로도 헬멧 감지 (비교용)
            print("   6.1 YOLO-World 모델로 헬멧 감지 (비교용)")
            yolo_world_helmet_results = yolo_world_model(rider_img)
            
            # 두 모델의 결과 비교를 위한 변수
            helmet_detections = []
            yolo_world_helmet_detections = []
            
            # Helmet 모델 결과 처리
            print("   Helmet 모델 결과 처리")
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
            
            # YOLO-World 모델 결과 처리
            print("   YOLO-World 모델 결과 처리")
            for result in yolo_world_helmet_results:
                boxes = result.boxes
                for box in boxes:
                    # 크롭된 이미지 내의 좌표
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = box.conf[0].item()
                    cls = box.cls[0].item()
                    class_name = yolo_world_model.names[int(cls)]
                    
                    # 헬멧 관련 클래스만 필터링 (helmet, hat 등)
                    helmet_related_classes = ["helmet", "hat", "cap", "headgear"]
                    is_helmet_related = any(helmet_class in class_name.lower() for helmet_class in helmet_related_classes)
                    
                    if conf > CONFIDENCE_THRESHOLD and is_helmet_related:
                        # 원본 이미지 좌표로 변환
                        orig_x1 = crop_coords[0] + x1
                        orig_y1 = crop_coords[1] + y1
                        orig_x2 = crop_coords[0] + x2
                        orig_y2 = crop_coords[1] + y2
                        
                        # YOLO-World 모델은 헬멧/노헬멧을 직접 구분하지 않으므로
                        # 감지된 클래스를 "helmet"으로 통일
                        detection = {
                            "bbox": [round(x, 2) for x in [orig_x1, orig_y1, orig_x2, orig_y2]],
                            "confidence": round(conf, 3),
                            "class": "helmet",
                            "model": "yolo_world",
                            "original_class": class_name  # 원래 클래스 이름 저장
                        }
                        yolo_world_helmet_detections.append(detection)
                        # 이 결과는 비교용이므로 all_detections에는 추가하지 않음
            
            # 두 모델의 결과 비교
            print(f"      Helmet 모델 감지 결과: {len(helmet_detections)}개")
            print(f"      YOLO-World 모델 감지 결과: {len(yolo_world_helmet_detections)}개")
            
            # 모델 성능 비교 (간단한 지표)
            if len(helmet_detections) > 0 and len(yolo_world_helmet_detections) > 0:
                print("      두 모델 모두 헬멧 관련 객체 감지")
                # 신뢰도 비교
                avg_helmet_conf = sum(d["confidence"] for d in helmet_detections) / len(helmet_detections)
                avg_yolo_world_conf = sum(d["confidence"] for d in yolo_world_helmet_detections) / len(yolo_world_helmet_detections)
                print(f"      Helmet 모델 평균 신뢰도: {avg_helmet_conf:.3f}")
                print(f"      YOLO-World 모델 평균 신뢰도: {avg_yolo_world_conf:.3f}")
                
                # 더 좋은 모델 선택 (여기서는 단순히 신뢰도가 높은 모델 선택)
                if avg_yolo_world_conf > avg_helmet_conf:
                    print("      YOLO-World 모델이 더 높은 신뢰도를 보임")
                    # 실제 적용 시에는 이 부분을 활성화하여 더 좋은 모델의 결과 사용 가능
                    # helmet_detections = yolo_world_helmet_detections
                else:
                    print("      Helmet 모델이 더 높은 신뢰도를 보임")
            elif len(yolo_world_helmet_detections) > 0 and len(helmet_detections) == 0:
                print("      YOLO-World 모델만 헬멧 관련 객체 감지")
                # 실제 적용 시에는 이 부분을 활성화하여 YOLO-World 모델 결과 사용 가능
                # helmet_detections = yolo_world_helmet_detections
            elif len(helmet_detections) > 0 and len(yolo_world_helmet_detections) == 0:
                print("      Helmet 모델만 헬멧 관련 객체 감지")
            
            print(f"      {len(helmet_detections)}개의 헬멧 관련 객체 감지")
            
            # 7. 헬멧 결과 집계
            print("   7. 헬멧 결과 집계")
            helmet_result = helmet_result_aggregation(helmet_detections)
            print(f"      결과 상태: {helmet_result['status']}")
            
            # 페어 결과 저장
            pair_result = {
                "rider": rider,
                "motorcycle": motorcycle,
                "helmet_result": helmet_result,
                "crop_coords": crop_coords
            }
            results["rider_pairs"].append(pair_result)
            results["helmet_results"].append(helmet_result)
        except Exception as e:
            print(f"   라이더 처리 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
    
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
