from ultralytics import YOLO
import cv2
import numpy as np
import os
import tempfile
import asyncio
import uuid
from fastapi import UploadFile

# 결과 저장 디렉토리 생성
os.makedirs("result", exist_ok=True)

async def process_video(file: UploadFile):
    """
    업로드된 비디오 파일을 처리하고 결과를 반환하는 함수
    """
    # 고유한 파일명 생성
    unique_id = str(uuid.uuid4())
    output_filename = f"processed_{unique_id}.mp4"
    output_path = os.path.join("result", output_filename)
    
    # 임시 파일로 저장
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_file.close()
    
    try:
        # 업로드된 파일 내용 읽기
        content = await file.read()
        
        # 임시 파일에 저장
        with open(temp_file.name, "wb") as f:
            f.write(content)
        
        # 모델 로드
        model = YOLO("models/best5.pt")
        
        # 비디오 설정
        cap = cv2.VideoCapture(temp_file.name)
        
        if not cap.isOpened():
            raise ValueError("비디오 파일을 열 수 없습니다.")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
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
        
        # 횡단보도 영역 (사각형 대신 다각형 정의)
        # 기본값으로 전체 이미지 영역을 사용하되, 필요에 따라 조정 가능
        crosswalk_polygon = np.array([[2, 2], [width-2, 2], [width-2, height-2], [2, height-2]], dtype=np.int32)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        detection_count = 0
        
        # 프레임별 예측
        for result in model.predict(source=temp_file.name, stream=True):
            frame = result.orig_img.copy()
            
            frame_detections = 0
            
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
                    frame_detections += 1
            
            detection_count += frame_detections
            out.write(frame)
        
        # 리소스 해제
        cap.release()
        out.release()
        
        # 썸네일 생성 (첫 프레임)
        cap = cv2.VideoCapture(output_path)
        ret, thumbnail_frame = cap.read()
        cap.release()
        
        thumbnail_path = os.path.join("result", f"thumbnail_{unique_id}.jpg")
        if ret:
            cv2.imwrite(thumbnail_path, thumbnail_frame)
            _, thumbnail_buffer = cv2.imencode('.jpg', thumbnail_frame)
            thumbnail_base64 = f"data:image/jpeg;base64,{np.array(thumbnail_buffer).tobytes().decode('latin1')}"
        else:
            thumbnail_base64 = None
        
        # 결과 반환
        return {
            "success": True,
            "message": "비디오 처리가 완료되었습니다.",
            "detection_count": detection_count,
            "output_path": output_filename,
            "thumbnail": thumbnail_base64,
            "totalFrames": total_frames,
            "duration": total_frames / fps if fps > 0 else 0
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"비디오 처리 중 오류가 발생했습니다: {str(e)}"
        }
    
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
