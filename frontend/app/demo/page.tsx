"use client"

import { useState, useRef, useEffect } from "react"
import type React from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Upload, Camera, AlertTriangle, CheckCircle, Loader2, Video, Tv } from "lucide-react"
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
    withHelmet: number
    withoutHelmet: number
    detections: Array<{
      box: [number, number, number, number]
      class: "helmet" | "no-helmet"
      confidence: number
    }>
  } | null>(null)
  const [isWebcamActive, setIsWebcamActive] = useState(false)
  const [webcamWs, setWebcamWs] = useState<WebSocket | null>(null)
  const videoRef = useRef<HTMLCanvasElement>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const isMobile = useMobile()

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

  // Process the image with mock YOLO detection
  const processImage = async () => {
    if (!preview) return

    setIsProcessing(true)

    // Simulate processing time
    await new Promise((resolve) => setTimeout(resolve, 2000))

    // Mock detection results
    const mockResults = {
      withHelmet: Math.floor(Math.random() * 3),
      withoutHelmet: Math.floor(Math.random() * 3) + 1,
      detections: [
        {
          box: [50, 50, 150, 150],
          class: "no-helmet" as const,
          confidence: 0.92,
        },
        {
          box: [250, 100, 350, 200],
          class: "helmet" as const,
          confidence: 0.88,
        },
      ],
    }

    setResults(mockResults)
    setIsProcessing(false)

    // Draw bounding boxes on canvas
    drawDetections(mockResults.detections)
  }

  // Draw detection boxes on canvas
  const drawDetections = (
    detections:
      | Array<{
          box: [number, number, number, number]
          class: "helmet" | "no-helmet"
          confidence: number
        }>
      | undefined,
  ) => {
    if (!canvasRef.current || !preview || !detections) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // Load the image to get dimensions
    const img = new Image()
    img.crossOrigin = "anonymous"
    img.onload = () => {
      // Set canvas dimensions to match image
      canvas.width = img.width
      canvas.height = img.height

      // Draw the image
      ctx.drawImage(img, 0, 0)

      // Draw detection boxes
      detections.forEach((detection) => {
        const [x, y, width, height] = detection.box

        // Set styles based on class
        if (detection.class === "helmet") {
          ctx.strokeStyle = "#10b981" // Green
        } else {
          ctx.strokeStyle = "#ef4444" // Red
        }

        ctx.lineWidth = 3
        ctx.strokeRect(x, y, width, height)

        // Add label
        ctx.fillStyle = detection.class === "helmet" ? "#10b981" : "#ef4444"
        ctx.font = "16px Arial"
        const label = `${detection.class === "helmet" ? "헬멧 착용" : "헬멧 미착용"} ${Math.round(detection.confidence * 100)}%`
        const textWidth = ctx.measureText(label).width

        ctx.fillRect(x, y - 25, textWidth + 10, 25)
        ctx.fillStyle = "#ffffff"
        ctx.fillText(label, x + 5, y - 7)
      })
    }
    img.src = preview
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
          if (videoRef.current) {
            const context = videoRef.current.getContext('2d');
            if (context) {
              context.drawImage(img, 0, 0, videoRef.current.width, videoRef.current.height);
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
    };
  }, []);

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
              <Tabs defaultValue="image" value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid grid-cols-4">
                  <TabsTrigger value="image" className="text-sm">
                    <Upload className="mr-1 h-4 w-4" /> 이미지
                  </TabsTrigger>
                  <TabsTrigger value="video" className="text-sm">
                    <Video className="mr-1 h-4 w-4" /> 동영상
                  </TabsTrigger>
                  <TabsTrigger value="webcam" className="text-sm">
                    <Camera className="mr-1 h-4 w-4" /> 웹캠
                  </TabsTrigger>
                  <TabsTrigger value="stream" className="text-sm">
                    <Tv className="mr-1 h-4 w-4" /> 실시간
                  </TabsTrigger>
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

                <TabsContent value="video" className="mt-6">
                  <div className="text-center py-12">
                    <Video className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                    <h3 className="text-lg font-medium mb-2">동영상 업로드</h3>
                    <p className="text-gray-500 mb-4">이 기능은 곧 제공될 예정입니다!</p>
                  </div>
                </TabsContent>

                <TabsContent value="webcam" className="mt-6">
                  <h3 className="text-lg font-medium mb-2">웹캠</h3>
                  <p className="text-sm text-gray-500 mb-4">
                    웹캠을 통해 실시간으로 헬멧 착용 여부를 감지합니다
                  </p>

                  <div className="border border-gray-200 rounded-md bg-gray-50 h-[400px] flex items-center justify-center mb-6">
                    {isWebcamActive ? (
                      <canvas
                        ref={videoRef}
                        width={640}
                        height={480}
                        className="max-h-full max-w-full object-contain"
                      />
                    ) : (
                      <p className="text-gray-400">웹캠이 시작되면 여기에 영상이 표시됩니다</p>
                    )}
                  </div>

                  <div className="flex justify-end">
                    <Button
                      onClick={isWebcamActive ? stopWebcam : startWebcam}
                      className={cn(
                        "min-w-[100px]",
                        isWebcamActive ? "bg-red-600 hover:bg-red-700" : "bg-gray-700 hover:bg-gray-800"
                      )}
                    >
                      {isWebcamActive ? (
                        <>
                          <Camera className="mr-2 h-4 w-4" />
                          중지
                        </>
                      ) : (
                        <>
                          <Camera className="mr-2 h-4 w-4" />
                          시작
                        </>
                      )}
                    </Button>
                  </div>
                </TabsContent>

                <TabsContent value="stream" className="mt-6">
                  <h3 className="text-lg font-medium mb-2">실시간 스트림</h3>
                  <p className="text-sm text-gray-500 mb-4">
                    실시간 CCTV 영상에서 헬멧 착용 여부를 감지합니다
                  </p>

                  <div className="border border-gray-200 rounded-md bg-gray-50 h-[400px] flex items-center justify-center mb-6">
                    {streamImage ? (
                      <img 
                        src={streamImage} 
                        alt="CCTV Stream" 
                        className="max-h-full max-w-full object-contain"
                      />
                    ) : (
                      <p className="text-gray-400">스트리밍이 시작되면 여기에 영상이 표시됩니다</p>
                    )}
                  </div>

                  <div className="flex justify-end">
                    <Button
                      onClick={isStreaming ? stopStream : startStream}
                      className={cn(
                        "min-w-[100px]",
                        isStreaming ? "bg-red-600 hover:bg-red-700" : "bg-gray-700 hover:bg-gray-800"
                      )}
                    >
                      {isStreaming ? (
                        <>
                          <Tv className="mr-2 h-4 w-4" />
                          중지
                        </>
                      ) : (
                        <>
                          <Tv className="mr-2 h-4 w-4" />
                          시작
                        </>
                      )}
                    </Button>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* 오른쪽 패널: 감지 결과 */}
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-medium mb-4">감지 결과</h3>

              {!results ? (
                <div className="border border-gray-200 rounded-md bg-gray-50 h-64 flex items-center justify-center">
                  <p className="text-gray-400">이미지를 업로드하고 감지를 실행하여 여기서 결과를 확인하세요</p>
                </div>
              ) : (
                <div>
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div
                      className={cn(
                        "p-4 rounded-lg flex items-center",
                        results.withHelmet > 0 ? "bg-green-100" : "bg-gray-100",
                      )}
                    >
                      <CheckCircle
                        className={cn("h-6 w-6 mr-2", results.withHelmet > 0 ? "text-green-600" : "text-gray-400")}
                      />
                      <div>
                        <p className="font-medium">헬멧 착용</p>
                        <p className="text-2xl font-bold">{results.withHelmet}</p>
                      </div>
                    </div>

                    <div
                      className={cn(
                        "p-4 rounded-lg flex items-center",
                        results.withoutHelmet > 0 ? "bg-red-100" : "bg-gray-100",
                      )}
                    >
                      <AlertTriangle
                        className={cn("h-6 w-6 mr-2", results.withoutHelmet > 0 ? "text-red-600" : "text-gray-400")}
                      />
                      <div>
                        <p className="font-medium">헬멧 미착용</p>
                        <p className="text-2xl font-bold">{results.withoutHelmet}</p>
                      </div>
                    </div>
                  </div>

                  {results.withoutHelmet > 0 && (
                    <div className="bg-red-50 border-l-4 border-red-500 p-4 text-red-700 mb-6">
                      <div className="flex">
                        <AlertTriangle className="h-6 w-6 mr-2 flex-shrink-0" />
                        <div>
                          <p className="font-bold">경고</p>
                          <p>
                            헬멧을 착용하지 않은 운전자 {results.withoutHelmet}명이 감지되었습니다. 이는 심각한 안전
                            위험을 초래합니다.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex justify-between">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setPreview(null)
                        setSelectedFile(null)
                        setResults(null)
                      }}
                    >
                      다시 시작
                    </Button>
                    <Button asChild>
                      <Link href="/statistics">통계 보기</Link>
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>

      <footer className="bg-gray-900 text-white py-6 mt-12">
        <div className="container mx-auto px-4 text-center">
          <p>© {new Date().getFullYear()} 오토바이 라이프 가드. 모든 권리 보유.</p>
        </div>
      </footer>
    </div>
  )
}
