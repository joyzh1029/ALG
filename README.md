# Motorcycle Life Guard

AI 기반 오토바이 헬멧 감지 시스템으로, 오토바이 운전자의 안전을 향상시키는 웹 애플리케이션 및 API 서비스입니다.

## 프로젝트 소개

Motorcycle Life Guard는 YOLO11n 기반 경량화 AI 모델을 활용하여 이미지 및 영상에서 오토바이, 사람, 헬멧 착용 여부를 감지합니다. 실시간 감지, 통계 분석, 사용자 친화적인 인터페이스, 그리고 강력한 백엔드 API를 통해 교통 안전 모니터링과 스마트 보안을 지원합니다.

## 주요 기능

- **실시간 헬멧 감지**
  - 이미지 업로드를 통한 헬멧 착용 여부 감지
  - 비디오 스트리밍 및 웹캠을 통한 실시간 모니터링
  - 실시간 CCTV 스트림 연동 지원
- **통계 및 분석**
  - 헬멧 착용률 통계 제공
  - 시간대별, 지역별 분석 데이터
  - 데이터 시각화 및 리포트 생성
- **알림 시스템**
  - 헬멧 미착용 감지 시 즉각적인 경고
  - 관리자 대시보드를 통한 모니터링
  - 커스터마이즈 가능한 알림 설정
- **API 및 WebSocket**
  - 이미지 업로드 및 실시간 스트리밍을 위한 RESTful API
  - WebSocket을 통한 실시간 헬멧 감지 스트리밍

## 기술 스택

### 프론트엔드

- Next.js 15.2.4
- React 19
- TypeScript
- Tailwind CSS
- shadcn/ui 컴포넌트
- Radix UI 프리미티브
- Lucide React 아이콘
- 반응형 디자인

### 백엔드

- FastAPI 0.104.1
- Python 3.10
- YOLO11n (Ultralytics 8.0.200)
- PyTorch 2.0.1 (CUDA 11.8지원)
- OpenCV 4.8.1.78
- WebSocket (websockets 12.0)

### 개발 도구

- pnpm (프론트엔드 패키지 매니저)
- ESLint
- PostCSS
- Python 가상 환경
- Uvicorn (백엔드 서버)

## 환경 요구 사항

- **프론트엔드**
  - Node.js 18.0.0 이상
  - pnpm 패키지 매니저
- **백엔드**
  - Python 3.10
  - NVIDIA GPU (권장, CUDA 11.8/12.1 지원)
  - CUDA 드라이버 ≥ 11.7
  - `yolo11n.pt` 모델 파일 (별도 준비 필요)

## 설치 및 시작하기

### 1. 저장소 클론

```bash
git clone https://github.com/joyzh1029/ALG.git
cd ALG
```

### 2. 프론트엔드 설치

```bash
cd frontend
pnpm install
```

### 3. 백엔드 설치

#### 가상환경설정
python=3.10

```bash
cd backend
pip install -r requirements.txt
```

#### PyTorch GPU 버전 설치

CUDA 버전에 맞는 명령어 선택:

- CUDA 11.8:

  ```bash
  pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
  ```

#### 모델 파일 준비

- `backend/models/` 디렉터리에 `yolo11n.pt` 파일 배치 (직접 훈련 또는 다운로드 필요)

### 4. 개발 서버 실행

#### 프론트엔드

```bash
cd frontend
pnpm dev
```

- 개발 서버: http://localhost:3000

#### 백엔드

```bash
cd backend
uvicorn main:app --reload
```

- API 문서: http://localhost:8000/docs

### 5. 빌드 (프론트엔드)

```bash
cd frontend
pnpm build
```

## 프로젝트 구조

```
├── frontend/              # 프론트엔드 디렉토리
│   ├── app/              # Next.js 앱 디렉토리
│   │   ├── about/       # 소개 페이지
│   │   ├── demo/        # 데모 페이지
│   │   ├── statistics/  # 통계 페이지
│   │   └── page.tsx     # 메인 페이지
│   ├── components/      # 리액트 컴포넌트
│   ├── hooks/          # 커스텀 훅
│   ├── lib/            # 유틸리티 함수
│   ├── public/         # 정적 파일
│   └── styles/         # 글로벌 스타일
├── backend/              # 백엔드 디렉토리
│   ├── models/         # YOLO 모델 파일
│   ├── main.py         # FastAPI 메인 애플리케이션
│   └── requirements.txt # 백엔드 의존성
```

## API 인터페이스

### 1. 서비스 상태 확인

- **GET /**\
  서비스 실행 상태 반환

### 2. 헬멧 감지 (이미지 업로드)

- **POST /detect**
  - 파라미터: 이미지 파일 (form-data, key: file)
  - 반환: 감지 결과 (바운딩 박스, 클래스, 신뢰도, 경고 메시지, base64 이미지 포함)

### 3. WebSocket

- **엔드포인트**: `/ws`
- **기능**: 실시간 이미지 스트림 기반 헬멧 감지
- **데이터 형식**: base64 인코딩 이미지 문자열 전송, JSON 형식 결과 수신

## 의존성 (백엔드)

`backend/requirements.txt`:

## 문제 해결

### 프론트엔드

- **의존성 설치 실패**: 새로운 터미널에서 `pnpm install` 재시도
- **스타일 깨짐**: Tailwind CSS 설정(`tailwind.config.js`) 확인

### 백엔드

- **PyTorch GPU 인식 불가**:
  - CUDA 드라이버와 PyTorch 버전 일치 확인
  - `python -c "import torch; print(torch.cuda.is_available())"` 실행 시 `True` 확인
- **모델 로드 실패**:
  - `models/yolo11n.pt` 파일 경로 및 유효성 확인
  - ultralytics 버전 8.0.200 이상 확인
- **의존성 충돌**:
  - 새로운 가상 환경에서 설치 권장

## 연락처

프로젝트 관리자: joyzh1029@gmail.com\
프로젝트 링크: https://github.com/joyzh1029/ALG.git

## 