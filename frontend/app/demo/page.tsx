"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Upload, Camera, AlertTriangle, CheckCircle, Loader2, Video, Tv } from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { useMobile } from "@/hooks/use-mobile"

export default function Demo() {
  const [activeTab, setActiveTab] = useState("image")
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
  const [websocket, setWebsocket] = useState<WebSocket | null>(null)
  const [streamActive, setStreamActive] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
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

  // Start/stop webcam stream
  const toggleWebcamStream = async () => {
    if (streamActive) {
      // Stop the stream
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.close()
      }
      
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = (videoRef.current.srcObject as MediaStream).getTracks()
        tracks.forEach(track => track.stop())
        videoRef.current.srcObject = null
      }
      
      setStreamActive(false)
      setWebsocket(null)
    } else {
      try {
        // Start the webcam
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: { facingMode: isMobile ? "environment" : "user" } 
        })
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream
        }
        
        // Connect to WebSocket
        const ws = new WebSocket(BACKEND_WS_URL)
        
        ws.onopen = () => {
          console.log("WebSocket connection established")
          setStreamActive(true)
        }
        
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data)
          
          if (data.alert) {
            // Handle alert messages
            console.log("Alert:", data.message)
            // You could show a notification here
          } else if (data.error) {
            console.error("WebSocket error:", data.error)
          } else {
            // Handle detection results
            setResults(data)
            
            // Update canvas with the received image
            if (data.image) {
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
              }
            }
          }
        }
        
        ws.onerror = (error) => {
          console.error("WebSocket error:", error)
          alert("WebSocket 연결 중 오류가 발생했습니다.")
          setStreamActive(false)
        }
        
        ws.onclose = () => {
          console.log("WebSocket connection closed")
          setStreamActive(false)
        }
        
        setWebsocket(ws)
        
        // Start sending frames
        const sendFrame = () => {
          if (ws.readyState === WebSocket.OPEN && videoRef.current && streamActive) {
            const canvas = document.createElement("canvas")
            canvas.width = videoRef.current.videoWidth
            canvas.height = videoRef.current.videoHeight
            const ctx = canvas.getContext("2d")
            
            if (ctx) {
              ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height)
              const dataUrl = canvas.toDataURL("image/jpeg", 0.8)
              ws.send(dataUrl)
            }
            
            if (streamActive) {
              requestAnimationFrame(sendFrame)
            }
          }
        }
        
        // Wait for video to be ready
        videoRef.current!.onloadedmetadata = () => {
          videoRef.current!.play()
          sendFrame()
        }
      } catch (error) {
        console.error("Error accessing webcam:", error)
        alert("웹캠에 접근할 수 없습니다.")
      }
    }
  }

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      if (websocket) {
        websocket.close()
      }
      
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = (videoRef.current.srcObject as MediaStream).getTracks()
        tracks.forEach(track => track.stop())
      }
    }
  }, [websocket])

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
                  <div className="text-center py-12">
                    <Camera className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                    <h3 className="text-lg font-medium mb-2">웹캠 업로드</h3>
                    <p className="text-gray-500 mb-4">이 기능은 곧 제공될 예정입니다!</p>
                  </div>
                </TabsContent>

                <TabsContent value="stream" className="mt-0">
                  <div className="p-4">
                    <h3 className="text-lg font-medium mb-2">실시간 스트림</h3>
                    <div className="mb-4">
                      <Button 
                        onClick={toggleWebcamStream}
                        className={streamActive ? "bg-red-500 hover:bg-red-600" : ""}
                      >
                        {streamActive ? (
                          <>
                            <Tv className="mr-2 h-4 w-4" /> 스트림 중지
                          </>
                        ) : (
                          <>
                            <Video className="mr-2 h-4 w-4" /> 스트림 시작
                          </>
                        )}
                      </Button>
                    </div>
                    
                    <div className="relative aspect-video bg-black rounded-md overflow-hidden">
                      <video
                        ref={videoRef}
                        className="absolute inset-0 w-full h-full object-contain"
                        muted
                        playsInline
                      />
                      <canvas
                        ref={canvasRef}
                        className="absolute inset-0 w-full h-full object-contain z-10"
                      />
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
