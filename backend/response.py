import requests
import certifi
import cv2
import ssl
import requests.adapters
from urllib3.poolmanager import PoolManager
from urllib3.util.ssl_ import create_urllib3_context

API_KEY = '2N5eiWa4zz2u3wj6ntsxPlT9YlgcIxZkLwKZQJJmmLo'
url = f'https://www.utic.go.kr/api/openApi/getCctvList?type=ex&key=2N5eiWa4zz2u3wj6ntsxPlT9YlgcIxZkLwKZQJJmmLo&target=sample'

class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    def _init_poolmanager(self, *args, **kwargs):  # 메서드 이름 수정
        context = create_urllib3_context()
        context.load_default_certs()
        kwargs['ssl_context'] = context
        return PoolManager(*args, **kwargs)

session = requests.Session()
session.mount('https://', CustomHttpAdapter())

# === 2. CCTV 목록 요청 ===
def get_cctv_stream_url():
    try:
        response = session.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()  # 응답이 JSON 형태일 경우
            cctvs = data.get("response", {}).get("data", [])
            if not cctvs:
                print("CCTV 목록이 없습니다.")
                return None
            for i, cctv in enumerate(cctvs):
                print(f"{i+1}. {cctv['cctvname']} - {cctv['cctvurl']}")
            index = int(input("\n시청할 CCTV 번호를 선택하세요: ")) - 1
            return cctvs[index]['cctvurl']
        else:
            print("API 요청 실패:", response.status_code)
    except Exception as e:
        print("예외 발생:", e)
    return None


# === 3. OpenCV 영상 처리 ===
def stream_video(url):
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        print("스트림 열기 실패:", url)
        return

    print("스트리밍 시작...")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("영상 수신 실패")
            break
        cv2.imshow("UTIC CCTV 스트리밍", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# === 4. 실행 ===
if __name__ == "__main__":
    stream_url = get_cctv_stream_url()
    if stream_url:
        stream_video(stream_url)

