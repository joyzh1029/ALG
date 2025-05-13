import cv2

# CCTV 실시간 스트리밍 URL
url = "https://kbscctv-cache.loomex.net/lowStream/_definst_/9999_low.stream/chunklist.m3u8"

# 스트리밍 캡처 객체 생성
cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("스트림 열기 실패")
else:
    print("스트리밍 시작")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("영상 수신 실패")
            break
        cv2.imshow("KBS CCTV 스트리밍", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
