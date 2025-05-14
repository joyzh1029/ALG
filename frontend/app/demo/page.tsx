"use client"

import { useState, useRef, useEffect } from "react"
import type React from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Upload, Camera, AlertTriangle, CheckCircle, Loader2, Video, Tv, FileVideo } from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { useMobile } from "@/hooks/use-mobile"

export default function Demo() {
  const [activeTab, setActiveTab] = useState("image")
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamImage, setStreamImage] = useState<string | null>(null)
  const ws = useRef<WebSocket | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [results, setResults] = useState<{
    timestamp: string;
    all_detections: Array<{
      bbox: number[];
      confidence: number;
      class: string;
      model: string;
    }>;
    rider_pairs: Array<any>;
    helmet_results: Array<{
      status: string;
      message: string;
      helmet_confidence: number;
      no_helmet_confidence: number;
    }>;
    warning: string;
    image: string;
  } | null>(null)
  const [isWebcamActive, setIsWebcamActive] = useState(false)
  const [webcamWs, setWebcamWs] = useState<WebSocket | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const [videoProcessingStatus, setVideoProcessingStatus] = useState<{
    isProcessing: boolean;
    success?: boolean;
    message?: string;
    detectionCount?: number;
    outputPath?: string;
    thumbnail?: string;
  } | null>(null)
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [videoPreview, setVideoPreview] = useState<string | null>(null)
  const videoInputRef = useRef<HTMLInputElement>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const isMobile = useMobile()

  // Backend API URL - adjust this to match your backend configuration
  const BACKEND_API_URL = "http://localhost:8000"
  const BACKEND_WS_URL = "ws://localhost:8000/ws"

  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      setSelectedFile(file)

      // Create preview
      const reader = new FileReader()
      reader.onload = (event) => {
        if (event.target) {
          setPreview(event.target.result as string)
        }
      }
      reader.readAsDataURL(file)

      // Reset results
      setResults(null)
    }
  }

  // Trigger file input click
  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  // Process the image with backend API
  const processImage = async () => {
    if (!preview || !selectedFile) return

    setIsProcessing(true)

    try {
      // Create form data for file upload
      const formData = new FormData()
      formData.append("file", selectedFile)

      console.log("이미지 시작 업로드")
      
      // Call backend API
      const response = await fetch(`${BACKEND_API_URL}/detect`, {
        method: "POST",
        body: formData,
      })

      console.log("API 응답 상태:", response.status)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error("API 오류:", errorText)
        throw new Error(`API error: ${response.status} - ${errorText}`)
      }

      console.log("API 응답 데이터 파싱")
      const data = await response.json()
      console.log("API 응답 데이터:", data)
      
      setResults(data)

      // Draw bounding boxes on canvas using the received image
      if (data.image) {
        console.log("결과 이미지 렌더링")
        const img = new Image()
        img.src = `data:image/jpeg;base64,${data.image}`
        img.onload = () => {
          if (!canvasRef.current) return
          const canvas = canvasRef.current
          const ctx = canvas.getContext("2d")
          if (!ctx) return

          canvas.width = img.width
          canvas.height = img.height
          ctx.drawImage(img, 0, 0)
          console.log("결과 이미지 렌더링 완료")
        }
      } else {
        console.warn("API 응답 데이터에 이미지 데이터가 없습니다")
      }
    } catch (error) {
      console.error("이미지 처리 중 오류:", error)
      alert(`이미지 처리 중 오류: ${error instanceof Error ? error.message : String(error)}`)
    } finally {
      setIsProcessing(false)
    }
  }

  const startStream = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      console.log("WebSocket is already open");
      return;
    }

    try {
      ws.current = new WebSocket('ws://localhost:8000/ws/stream');
      
      ws.current.onopen = () => {
        console.log('WebSocket Connected');
        setIsStreaming(true);
      };

      ws.current.onmessage = (event) => {
        setStreamImage(`data:image/jpeg;base64,${event.data}`);
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket Error:', error);
        setIsStreaming(false);
      };

      ws.current.onclose = () => {
        console.log('WebSocket Disconnected');
        setIsStreaming(false);
      };
    } catch (error) {
      console.error('WebSocket Connection Error:', error);
    }
  };

  const stopStream = () => {
    if (ws.current) {
      ws.current.close();
      ws.current = null;
      setIsStreaming(false);
      setStreamImage(null);
    }
  };

  const startWebcam = async () => {
    try {
      // WebSocket 연결 시작
      const ws = new WebSocket('ws://localhost:8000/ws/webcam');
      
      ws.onopen = () => {
        console.log('WebSocket Connected for webcam');
        setIsWebcamActive(true);
        setWebcamWs(ws);
      };

      ws.onmessage = (event) => {
        // base64 이미지를 새로운 Image 객체로 변환
        const img = new Image();
        img.onload = () => {
          if (canvasRef.current) {
            const context = canvasRef.current.getContext('2d');
            if (context) {
              context.drawImage(img, 0, 0, canvasRef.current.width, canvasRef.current.height);
            }
          }
        };
        img.src = `data:image/jpeg;base64,${event.data}`;
      };

      ws.onclose = () => {
        console.log('WebSocket Disconnected');
        setIsWebcamActive(false);
        setWebcamWs(null);
      };

      ws.onerror = (error) => {
        console.error('WebSocket Error:', error);
        setIsWebcamActive(false);
      };
      
    } catch (error) {
      console.error('웹캠 연결 실패:', error);
    }
  };

  const stopWebcam = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
      setIsWebcamActive(false);
    }
    
    if (webcamWs) {
      webcamWs.close();
      setWebcamWs(null);
    }
  };

  // 컴포넌트 언마운트 시 웹캠 정리
  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, []);

  // 컴포넌트 언마운트 시 WebSocket 연결 정리
  useEffect(() => {
    return () => {
      if (ws.current) {
        ws.current.close();
      }
      if (webcamWs) {
        webcamWs.close();
      }
      if (cctvWs.current) {
        cctvWs.current.close();
      }
    };
  }, [webcamWs]);

  // 비디오 파일 선택 처리
  const handleVideoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      setVideoFile(file)
      
      // 비디오 미리보기 URL 생성
      const videoURL = URL.createObjectURL(file)
      setVideoPreview(videoURL)
      
      // 결과 초기화
      setVideoProcessingStatus(null)
    }
  }

  // 비디오 파일 업로드 버튼 클릭
  const handleVideoUploadClick = () => {
    videoInputRef.current?.click()
  }

  // 비디오 처리 함수
  const processVideo = async () => {
    if (!videoFile) return

    setVideoProcessingStatus({
      isProcessing: true
    })

    try {
      // 폼 데이터 생성
      const formData = new FormData()
      formData.append("file", videoFile)

      console.log("비디오 업로드 시작")
      
      // 백엔드 API 호출
      const response = await fetch(`${BACKEND_API_URL}/process-video`, {
        method: "POST",
        body: formData,
      })

      console.log("API 응답 상태:", response.status)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error("API 오류:", errorText)
        throw new Error(`API error: ${response.status} - ${errorText}`)
      }

      console.log("API 응답 데이터 파싱")
      const data = await response.json()
      console.log("API 응답 데이터:", data)
      
      setVideoProcessingStatus({
        isProcessing: false,
        success: data.success,
        message: data.message,
        detectionCount: data.detection_count,
        outputPath: data.output_path,
        thumbnail: data.thumbnail
      })
    } catch (error) {
      console.error("비디오 처리 오류:", error)
      setVideoProcessingStatus({
        isProcessing: false,
        success: false,
        message: `오류: ${error instanceof Error ? error.message : String(error)}`
      })
    }
  }

  const [cctvImage, setCctvImage] = useState<string | null>(null)
  const cctvWs = useRef<WebSocket | null>(null)
  const [isCctvStreaming, setIsCctvStreaming] = useState(false)

  const startCctvStream = () => {
    if (cctvWs.current?.readyState === WebSocket.OPEN) {
      console.log("CCTV WebSocket is already open");
      return;
    }

    try {
      cctvWs.current = new WebSocket(`ws://${window.location.hostname}:8000/ws/cctv`);
      
      cctvWs.current.onopen = () => {
        console.log('WebSocket Connected for CCTV');
        setIsCctvStreaming(true);
      };

      cctvWs.current.onmessage = (event) => {
        setCctvImage(event.data);
      };

      cctvWs.current.onerror = (error) => {
        console.error('WebSocket Error for CCTV:', error);
        setIsCctvStreaming(false);
      };

      cctvWs.current.onclose = () => {
        console.log('WebSocket Disconnected for CCTV');
        setIsCctvStreaming(false);
      };
    } catch (error) {
      console.error('WebSocket Connection Error for CCTV:', error);
    }
  };

  const stopCctvStream = () => {
    if (cctvWs.current) {
      cctvWs.current.close();
      cctvWs.current = null;
      setIsCctvStreaming(false);
      setCctvImage(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-red-600 text-white py-4">
        <div className="container mx-auto px-4 flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold">
            오토바이 라이프 가드
          </Link>
          <nav className="hidden md:block">
            <ul className="flex space-x-6">
              <li>
                <Link href="/" className="hover:underline">
                  홈
                </Link>
              </li>
              <li>
                <Link href="/demo" className="hover:underline font-bold">
                  데모
                </Link>
              </li>
              <li>
                <Link href="/statistics" className="hover:underline">
                  통계
                </Link>
              </li>
              <li>
                <Link href="/about" className="hover:underline">
                  소개
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-2">헬멧 감지</h1>
        <p className="text-gray-600 mb-8">
          오토바이 운전자의 헬멧 착용 여부를 확인하기 위해 이미지나 영상을 업로드하세요.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 왼쪽 패널: 업로드 옵션 */}
          <Card>
            <CardContent className="p-6">
              <Tabs defaultValue={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="image">이미지</TabsTrigger>
                  <TabsTrigger value="video">비디오</TabsTrigger>
                  <TabsTrigger value="cctv">CCTV</TabsTrigger>
                </TabsList>

                <TabsContent value="image" className="mt-6">
                  <h3 className="text-lg font-medium mb-2">이미지 업로드</h3>
                  <p className="text-sm text-gray-500 mb-4">
                    오토바이 운전자의 헬멧 착용 여부를 감지할 이미지를 업로드하세요
                  </p>

                  <div className="flex space-x-2 mb-6">
                    <Button onClick={handleUploadClick} variant="outline" size="sm">
                      파일 선택
                    </Button>
                    <p className="text-sm text-gray-500 flex items-center">
                      {selectedFile ? selectedFile.name : "선택된 파일 없음"}
                    </p>
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileChange}
                      accept="image/*"
                      className="hidden"
                    />
                  </div>

                  <div className="border border-gray-200 rounded-md bg-gray-50 h-64 flex items-center justify-center mb-6">
                    {preview ? (
                      <canvas ref={canvasRef} className="max-h-full max-w-full object-contain" />
                    ) : (
                      <p className="text-gray-400">업로드된 이미지 없음</p>
                    )}
                  </div>

                  <div className="flex justify-end">
                    <Button
                      onClick={processImage}
                      disabled={!preview || isProcessing}
                      className="bg-gray-700 hover:bg-gray-800"
                    >
                      {isProcessing ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          처리 중...
                        </>
                      ) : (
                        "감지 실행"
                      )}
                    </Button>
                  </div>
                </TabsContent>

                <TabsContent value="video" className="py-4">
                  <div className="flex flex-col items-center space-y-4">
                    <input
                      type="file"
                      accept="video/mp4,video/x-m4v,video/*"
                      onChange={handleVideoChange}
                      ref={videoInputRef}
                      className="hidden"
                    />
                    
                    <div className="flex space-x-2">
                      <Button 
                        onClick={handleVideoUploadClick}
                        variant="outline"
                      >
                        <Upload className="mr-2 h-4 w-4" />
                        비디오 선택
                      </Button>
                      
                      <Button 
                        onClick={processVideo}
                        disabled={!videoFile || videoProcessingStatus?.isProcessing}
                      >
                        {videoProcessingStatus?.isProcessing ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            처리 중...
                          </>
                        ) : (
                          <>
                            <Video className="mr-2 h-4 w-4" />
                            비디오 처리
                          </>
                        )}
                      </Button>
                    </div>

                    {/* 비디오 미리보기 추가 */}
                    <div className="border border-gray-200 rounded-md bg-gray-50 w-full aspect-video flex items-center justify-center mb-6">
                      {videoPreview ? (
                        <video 
                          src={videoPreview} 
                          className="max-h-full max-w-full object-contain" 
                          controls
                        />
                      ) : (
                        <p className="text-gray-400">업로드된 비디오 없음</p>
                      )}
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="cctv" className="py-4">
                  <div className="flex flex-col items-center space-y-4">
                    <h3 className="text-lg font-medium mb-2">실시간 CCTV 모니터링</h3>
                    <p className="text-sm text-gray-500 mb-4">
                      실시간 CCTV 스트림에서 헬멧 착용 여부를 감지합니다
                    </p>
                    
                    <div className="flex space-x-2 mb-4">
                      <Button 
                        onClick={() => {
                          if (isCctvStreaming) {
                            stopCctvStream();
                          } else {
                            startCctvStream();
                          }
                        }}
                      >
                        {isCctvStreaming ? (
                          <>
                            <Tv className="mr-2 h-4 w-4" />
                            스트리밍 중지
                          </>
                        ) : (
                          <>
                            <Tv className="mr-2 h-4 w-4" />
                            스트리밍 시작
                          </>
                        )}
                      </Button>
                    </div>
                    
                    <div className="border border-gray-200 rounded-md bg-gray-50 w-full aspect-video flex items-center justify-center">
                      {cctvImage ? (
                        <img 
                          src={`data:image/jpeg;base64,${cctvImage}`} 
                          className="max-h-full max-w-full object-contain" 
                          alt="CCTV Stream"
                        />
                      ) : (
                        <div className="text-center">
                          {isCctvStreaming ? (
                            <Loader2 className="mx-auto h-8 w-8 animate-spin text-gray-400 mb-2" />
                          ) : (
                            <p className="text-gray-400">스트리밍이 시작되지 않았습니다</p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* 오른쪽 패널: 감지 결과 */}
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-medium mb-4">감지 결과</h3>

              {!results && activeTab === "image" ? (
                <div className="border border-gray-200 rounded-md bg-gray-50 h-64 flex items-center justify-center">
                  <p className="text-gray-400">이미지를 업로드하고 감지를 실행하여 여기서 결과를 확인하세요</p>
                </div>
              ) : activeTab === "video" && !videoProcessingStatus ? (
                <div className="border border-gray-200 rounded-md bg-gray-50 h-64 flex items-center justify-center">
                  <p className="text-gray-400">비디오를 업로드하고 처리를 실행하여 여기서 결과를 확인하세요</p>
                </div>
              ) : activeTab === "video" && videoProcessingStatus?.isProcessing ? (
                <div className="border border-gray-200 rounded-md bg-gray-50 h-64 flex items-center justify-center">
                  <div className="text-center">
                    <Loader2 className="mx-auto h-8 w-8 animate-spin text-gray-400 mb-2" />
                    <p className="text-gray-500">비디오 처리 중...</p>
                  </div>
                </div>
              ) : activeTab === "video" && videoProcessingStatus && !videoProcessingStatus.isProcessing ? (
                <div className={`p-4 rounded-lg border ${videoProcessingStatus.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                  <h4 className="font-medium mb-2">
                    {videoProcessingStatus.success ? '처리 완료' : '처리 실패'}
                  </h4>
                  <p className="text-sm mb-2">{videoProcessingStatus.message}</p>
                  
                  {videoProcessingStatus.success && (
                    <div className="mt-4">
                      <div className="flex items-center mb-2">
                        <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                        <span>감지된 헬멧: {videoProcessingStatus.detectionCount}</span>
                      </div>
                      
                      {/* 비디오 직접 표시 */}
                      <div className="mt-4">
                        {videoProcessingStatus?.outputPath && (
                          <div className="mb-4">
                            <p className="text-sm font-medium mb-2">처리된 비디오:</p>
                            <div className="w-full aspect-video bg-black rounded-md overflow-hidden">
                              <video 
                                src={`${BACKEND_API_URL}/result/${videoProcessingStatus.outputPath}`}
                                className="w-full h-full"
                                controls
                                autoPlay
                                onError={(e) => {
                                  console.error("비디오 로드 오류:", e);
                                  console.log("비디오 경로:", videoProcessingStatus.outputPath);
                                  console.log("시도한 URL:", `${BACKEND_API_URL}/result/${videoProcessingStatus.outputPath}`);
                                }}
                              />
                            </div>
                          </div>
                        )}
                        
                        {/* 다운로드 버튼 */}
                        {videoProcessingStatus?.outputPath && (
                          <div className="flex justify-center">
                            <a 
                              href={`${BACKEND_API_URL}/result/${videoProcessingStatus.outputPath}`}
                              download
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="7 10 12 15 17 10"></polyline>
                                <line x1="12" y1="15" x2="12" y2="3"></line>
                              </svg>
                              처리된 비디오 다운로드
                            </a>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : results && (
                <div>
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div
                      className={cn(
                        "p-4 rounded-lg flex items-center",
                        results.helmet_results.some(r => r.status === "helmet") ? "bg-green-100" : "bg-gray-100",
                      )}
                    >
                      <CheckCircle
                        className={cn(
                          "h-6 w-6 mr-2", 
                          results.helmet_results.some(r => r.status === "helmet") ? "text-green-600" : "text-gray-400"
                        )}
                      />
                      <div>
                        <p className="font-medium">헬멧 착용</p>
                        <p className="text-2xl font-bold">
                          {results.helmet_results.filter(r => r.status === "helmet").length}
                        </p>
                      </div>
                    </div>

                    <div
                      className={cn(
                        "p-4 rounded-lg flex items-center",
                        results.helmet_results.some(r => r.status === "no_helmet") ? "bg-red-100" : "bg-gray-100",
                      )}
                    >
                      <AlertTriangle
                        className={cn(
                          "h-6 w-6 mr-2", 
                          results.helmet_results.some(r => r.status === "no_helmet") ? "text-red-600" : "text-gray-400"
                        )}
                      />
                      <div>
                        <p className="font-medium">헬멧 미착용</p>
                        <p className="text-2xl font-bold">
                          {results.helmet_results.filter(r => r.status === "no_helmet").length}
                        </p>
                      </div>
                    </div>
                  </div>

                  {results.warning && results.warning.startsWith("경고") && (
                    <div className="bg-red-50 border-l-4 border-red-500 p-4 text-red-700 mb-6">
                      <div className="flex">
                        <AlertTriangle className="h-6 w-6 mr-2 flex-shrink-0" />
                        <div>
                          <p className="font-bold">경고</p>
                          <p>{results.warning}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>

      <footer className="bg-gray-900 text-white py-6 mt-12">
        <div className="container mx-auto px-4 text-center">
          <p> 2024 오토바이 라이프 가드. 모든 권리 보유.</p>
        </div>
      </footer>
    </div>
  )
}
