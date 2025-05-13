from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import cv2
import base64
import numpy as np
from typing import Optional
import asyncio

app = FastAPI()

# 웹캠 스트림을 처리하는 클래스
class WebcamStream:
    def __init__(self):
        self.cap = None
        self.is_active = False

    async def start(self):
        self.cap = cv2.VideoCapture(0)  # 웹캠 디바이스 번호 (보통 0)
        self.is_active = True

    def stop(self):
        if self.cap:
            self.cap.release()
        self.is_active = False

    def get_frame(self):
        if not self.cap:
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

webcam = WebcamStream()

@app.websocket("/ws/webcam")
async def webcam_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # 웹캠 시작
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            await websocket.close()
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 이미지를 base64로 인코딩
            _, buffer = cv2.imencode('.jpg', frame)
            encoded_frame = base64.b64encode(buffer).decode('utf-8')
            
            # 클라이언트로 스트림 전송
            await websocket.send_text(encoded_frame)
            
            # 프레임 레이트 조절 (30 FPS)
            await asyncio.sleep(1/30)
            
    except WebSocketDisconnect:
        print("클라이언트 연결 종료")
    finally:
        cap.release()

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    # 클라이언트 연결
    await websocket.accept()
    
    # CCTV 실시간 스트리밍 URL (예시)
    url = "https://kbscctv-cache.loomex.net/lowStream/_definst_/9999_low.stream/chunklist.m3u8"
    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        print("스트림 열기 실패")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("영상 수신 실패")
            break

        # 이미지를 base64로 인코딩
        _, buffer = cv2.imencode('.jpg', frame)
        encoded_frame = base64.b64encode(buffer).decode('utf-8')

        # 클라이언트로 이미지를 전송
        await websocket.send_text(encoded_frame)

    cap.release()
