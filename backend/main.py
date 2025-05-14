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
    
    # 멀리있는 오토바이를 위한 임계값 조정
    for moto_idx, motorcycle in enumerate(motorcycles):
        moto_width = motorcycle["bbox"][2] - motorcycle["bbox"][0]
        moto_height = motorcycle["bbox"][3] - motorcycle["bbox"][1]
        
        #  멀리있는 작은 오토바이를 위한 임계값 조정
        size_factor = 1.0
        if max(moto_width, moto_height) < 100:  # 100픽셀 미만은 멀리있는 작은 오토바이로 판단
            size_factor = 1.5  # 멀리있는 작은 오토바이를 위한 임계값 조정
            print(f"   멀리있는 작은 오토바이 임계값 조정: 尺寸={moto_width:.1f}x{moto_height:.1f}, 계수={size_factor}")
        
        moto_threshold = RIDER_MOTORCYCLE_PAIRING_THRESHOLD * max(moto_width, moto_height) * size_factor
    
    pairs = []
    paired_rider_indices = set()  # 이미 페어링된 라이더 인덱스 추적
    
    # 1단계: 각 오토바이에 대해 근처의 모든 라이더를 찾되, 각 라이더는 한 대의 오토바이에만 할당
    for moto_idx, motorcycle in enumerate(motorcycles):
        moto_center_x = (motorcycle["bbox"][0] + motorcycle["bbox"][2]) / 2
        moto_center_y = (motorcycle["bbox"][1] + motorcycle["bbox"][3]) / 2
        
        moto_width = motorcycle["bbox"][2] - motorcycle["bbox"][0]
        moto_height = motorcycle["bbox"][3] - motorcycle["bbox"][1]
        moto_threshold = RIDER_MOTORCYCLE_PAIRING_THRESHOLD * max(moto_width, moto_height)
        
        # 이 오토바이와 페어링 가능한 라이더들
        potential_riders = []
        
        # 모든 라이더에 대해 거리 계산
        for rider_idx, rider in enumerate(riders):
            # 이미 페어링된 라이더는 건너뜀
            if rider_idx in paired_rider_indices:
                continue
                
            rider_center_x = (rider["bbox"][0] + rider["bbox"][2]) / 2
            rider_center_y = (rider["bbox"][1] + rider["bbox"][3]) / 2
            
            # 유클리드 거리 계산
            distance = ((rider_center_x - moto_center_x) ** 2 + (rider_center_y - moto_center_y) ** 2) ** 0.5
            
            # 거리가 임계값보다 작으면 잠재적 페어링 대상
            if distance < moto_threshold:
                confidence = 1.0 - (distance / moto_width) if moto_width > 0 else 0.5
                potential_riders.append({
                    "rider_idx": rider_idx,
                    "rider": rider,
                    "distance": distance,
                    "confidence": confidence
                })
        
        # 거리순으로 정렬 (가까운 순)
        potential_riders.sort(key=lambda x: x["distance"])
        
        # 페어링 처리 (한 오토바이에 여러 라이더 가능)
        for rider_data in potential_riders:
            rider_idx = rider_data["rider_idx"]
            rider = rider_data["rider"]
            distance = rider_data["distance"]
            confidence = rider_data["confidence"]
            
            # 페어 생성
            pair = {
                "rider": rider,
                "motorcycle": motorcycle,
                "confidence": round(confidence, 3),
                "distance": round(distance, 3)
            }
            pairs.append(pair)
            
            # 이 라이더는 이제 다른 오토바이와 페어링 불가
            paired_rider_indices.add(rider_idx)
            
            print(f"오토바이 {moto_idx}와 라이더 페어링: 거리={distance:.3f}, 신뢰도={confidence:.3f}")
    
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
    items = [d for d in helmet_detections if d["class"] == "item"]
    
    print(f"      감지된 객체: {[d['class'] for d in helmet_detections]}")
    print(f"      헬멧 객체 수: {len(helmets)}, 노헬멧 객체 수: {len(no_helmets)}")
    
    max_helmet_conf = max([h["confidence"] for h in helmets]) if helmets else 0
    max_no_helmet_conf = max([nh["confidence"] for nh in no_helmets]) if no_helmets else 0
    
    # 결과 판단
    has_helmet = max_helmet_conf > HELMET_RESULT_AGGREGATION_THRESHOLD
    no_helmet_detected = max_no_helmet_conf > HELMET_RESULT_AGGREGATION_THRESHOLD
    
    # item이 헬멧일 가능성을 확인 - 매우 엄격한 기준 적용
    item_on_head = False
    helmet_like_item = None
    
    if items and not (has_helmet or no_helmet_detected):
        # 아이템 중 가장 높은 신뢰도를 가진 것을 선택
        items_sorted = sorted(items, key=lambda x: x["confidence"], reverse=True)
        
        for item in items_sorted:
            # 물체의 위치와 비율 특성을 계산
            item_y1 = item["bbox"][1]
            item_y2 = item["bbox"][3]
            item_height = item_y2 - item_y1
            item_width = item["bbox"][2] - item["bbox"][0]
            
            # 헬멧 형태 분석을 위한 추가 지표
            aspect_ratio = item_width / item_height if item_height > 0 else 0
            area = item_width * item_height
            relative_y_pos = item_y1 / item_height if item_height > 0 else 999
            
            # 멀리있는 작은 물체를 판단
            is_distant = item_height < 40
            
            print(f"      아이템 분석: 높이={item_height:.1f}, 비율={aspect_ratio:.2f}, 상대위치={relative_y_pos:.2f}, 면적={area:.1f}")
            
            # 헬멧 형태 분석 - 매우 엄격한 기준 적용
            # 상대 위치가 0.3 미만이어야 함 (상단 30% 이내)
            if relative_y_pos < 0.3:
                # 헬멧 형태 추가 검증
                is_helmet_shaped = (
                    # 헬멧은 일반적으로 너무 넓지 않음
                    aspect_ratio < 1.3 and
                    # 너무 작은 물체는 신뢰도 낮음 (멀리 있는 경우 제외)
                    (area > 1200 or is_distant) and
                    # 헬멧의 최소 크기 요구사항
                    (item_height > 35 or is_distant) and
                    # 신뢰도 요구사항
                    item["confidence"] > 0.65
                )
                
                if is_helmet_shaped:
                    item_on_head = True
                    helmet_like_item = item
                    print(f"      헬멧 가능성 높음: 높이={item_height:.1f}, 비율={aspect_ratio:.2f}, 상대위치={relative_y_pos:.2f}")
                    break
                else:
                    print(f"      헬멧 형태 불충분: 비율={aspect_ratio:.2f}, 면적={area:.1f}")
            else:
                print(f"      위치 부적합: 상대위치={relative_y_pos:.2f} (0.3 미만이어야 함)")
    
    # 향상된 판단 로직
    if len(helmet_detections) > 0 and len(helmets) == 0 and len(no_helmets) == 0:
        if item_on_head and helmet_like_item:
            # 헬멧 형태와 높은 신뢰도를 가진 아이템만 헬멧으로 인정
            print("      헬멧 가능성: 헬멧 형태의 물체가 머리 위에 위치")
            status = "helmet"
            message = "안전: 헬멧을 착용한 오토바이 운전자가 감지되었습니다."
        else:
            print("      헬멧으로 인정되지 않는 물체 감지 -> 미착용으로 처리")
            status = "no_helmet"
            message = "경고: 헬멧을 착용하지 않은 오토바이 운전자가 감지되었습니다!"
    elif has_helmet:
        status = "helmet"
        message = "안전: 헬멧을 착용한 오토바이 운전자가 감지되었습니다."
    elif no_helmet_detected:
        status = "no_helmet"
        message = "경고: 헬멧을 착용하지 않은 오토바이 운전자가 감지되었습니다!"
    else:
        status = "no_helmet"
        message = "경고: 헬멧을 착용하지 않은 것으로 판단됩니다!"
    
    return {
        "status": status,
        "message": message,
        "helmet_confidence": max_helmet_conf,
        "no_helmet_confidence": max_no_helmet_conf,
        "helmet_on_head": True if status == "helmet" else False,
        "detections": helmet_detections
    }

def helmet_label_visualization(img: np.ndarray, results: Dict) -> np.ndarray:
    """감지 결과 시각화"""
    img_copy = img.copy()
    
    # PIL 변환을 통한 한글 텍스트 처리
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    # OpenCV BGR → RGB 변환
    img_rgb = cv2.cvtColor(img_copy, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)
    
    # 글꼴 설정
    try:
        font_path = os.path.join(os.environ['WINDIR'], 'Fonts', 'malgun.ttf')
        if not os.path.exists(font_path):
            font_path = os.path.join(os.environ['WINDIR'], 'Fonts', 'gulim.ttc')
        
        label_font = ImageFont.truetype(font_path, 20)
        warning_font = ImageFont.truetype(font_path, 16)  # 경고 글꼴 크기 축소
        header_font = ImageFont.truetype(font_path, 28)
    except Exception as e:
        print(f"폰트 로드 오류: {e}")
        label_font = ImageFont.load_default()
        warning_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
    
        
    # 헬멧 착용/미착용 라이더 표시
    for pair in results.get("rider_pairs", []):
        helmet_result = pair.get("helmet_result", {})
        rider = pair.get("rider", {})
        status = helmet_result.get("status", "")
        
        x1, y1, x2, y2 = map(int, rider["bbox"])
        
        if status in ["no_helmet", "helmet_not_worn"]:
            # 미착용 라이더 - 빨간색 테두리
            draw.rectangle([(x1, y1), (x2, y2)], outline=(255, 0, 0), width=LABEL_THICKNESS * 2)
            
            warning_text = "no-helmet"
            text_color = (255, 0, 0)  # 빨간색
            
            text_bbox = draw.textbbox((0, 0), warning_text, font=warning_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            draw.rectangle([(x1, y1 - text_height - 5), (x1 + text_width, y1)], fill=text_color)
            draw.text((x1, y1 - text_height - 5), warning_text, font=warning_font, fill=(255, 255, 255))
            
        elif status == "helmet":
            # 착용 라이더 - 녹색 테두리
            draw.rectangle([(x1, y1), (x2, y2)], outline=(0, 255, 0), width=LABEL_THICKNESS * 2)
            
            safety_text = "helmet"
            text_color = (0, 155, 0)  # 녹색
            
            text_bbox = draw.textbbox((0, 0), safety_text, font=warning_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            draw.rectangle([(x1, y1 - text_height - 5), (x1 + text_width, y1)], fill=text_color)
            draw.text((x1, y1 - text_height - 5), safety_text, font=warning_font, fill=(255, 255, 255))
    
    # PIL 이미지를 OpenCV 형식으로 변환
    img_copy = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
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
            
            # 신뢰도 임계값 조정 (원거리 객체 감지 향상)
            distance_adjusted_threshold = CONFIDENCE_THRESHOLD * 0.8
            
            # "person"및"motorcycle" 클래스만 처리 (신뢰도 임계값 낮춤)
            if conf > distance_adjusted_threshold and class_name in ["person", "motorcycle"]:
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
            
            # 判断是否为远距离小物体
            is_distant = (rider["bbox"][2] - rider["bbox"][0]) < 100  # 小于100像素宽度视为远距离

            # 针对远距离物体使用更低的置信度阈值
            helmet_threshold = CONFIDENCE_THRESHOLD * (0.7 if is_distant else 1.0)

            helmet_results = helmet_model(rider_img)
            
            # 헬멧 감지 결과를 저장할 리스트
            helmet_detections = []
            
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
                    
                    # 远距离物体特殊处理
                    if is_distant and class_name == "item" and conf > helmet_threshold:
                        # 计算物体在头部的相对位置
                        rel_y_pos = (y1 - rider_crop_y1) / max((rider_crop_y2 - rider_crop_y1), 1)
                        
                        # 如果物体在头部上方，很可能是头盔
                        if rel_y_pos < 0.3:  # 位于头部上方30%区域
                            class_name = "helmet"  # 将item重新分类为helmet
                            print(f"      远距离物体重新分类: item -> helmet, 位置={rel_y_pos:.2f}")
                    
                    # 신뢰도 임계값 조정 (헬멧 감지 향상)
                    helmet_confidence_threshold = CONFIDENCE_THRESHOLD * 0.85
                    
                    if conf > helmet_confidence_threshold:
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
