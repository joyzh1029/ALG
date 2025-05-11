"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Shield, TrendingUp, AlertTriangle, CheckCircle, Info } from "lucide-react"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent } from "@/components/ui/card"

// 차트를 위한 임시 데이터
const weeklyData = {
  labels: ["월", "화", "수", "목", "금", "토", "일"],
  withHelmet: [120, 145, 135, 165, 180, 190, 180],
  withoutHelmet: [140, 165, 160, 190, 210, 225, 215],
}

export default function Statistics() {
  const [mounted, setMounted] = useState(false)
  const [timeRange, setTimeRange] = useState("주간")

  // 통계 데이터
  const stats = {
    totalDetections: 1248,
    totalIncrease: 12.5,
    withoutHelmet: 205,
    withoutHelmetPercentage: 16.4,
    withHelmet: 1043,
    withHelmetPercentage: 83.6,
    accuracy: 94.8,
    accuracyIncrease: 2.1,
    correctDetection: 83.6,
    detectionAccuracy: 94.8,
    falsePositive: 2.3,
    falseNegative: 2.9,
  }

  useEffect(() => {
    setMounted(true)

    // 차트 그리기
    if (typeof window !== "undefined") {
      const drawChart = () => {
        const canvas = document.getElementById("detectionChart") as HTMLCanvasElement
        if (!canvas) return

        const ctx = canvas.getContext("2d")
        if (!ctx) return

        const width = canvas.width
        const height = canvas.height

        // 캔버스 초기화
        ctx.clearRect(0, 0, width, height)

        // 배경 그리드 그리기
        ctx.strokeStyle = "#e5e7eb"
        ctx.beginPath()

        // 수평선
        for (let i = 0; i <= 4; i++) {
          const y = height - (i * height) / 4 - 30
          ctx.moveTo(40, y)
          ctx.lineTo(width - 20, y)
        }

        // 수직선
        for (let i = 0; i < weeklyData.labels.length; i++) {
          const x = 40 + i * ((width - 60) / (weeklyData.labels.length - 1))
          ctx.moveTo(x, 20)
          ctx.lineTo(x, height - 30)
        }

        ctx.stroke()

        // x축 레이블 그리기
        ctx.fillStyle = "#6b7280"
        ctx.font = "12px Arial"
        ctx.textAlign = "center"

        for (let i = 0; i < weeklyData.labels.length; i++) {
          const x = 40 + i * ((width - 60) / (weeklyData.labels.length - 1))
          ctx.fillText(weeklyData.labels[i], x, height - 10)
        }

        // 헬멧 착용 데이터 그리기 (녹색 영역)
        const maxValue = Math.max(...weeklyData.withoutHelmet)

        ctx.fillStyle = "rgba(16, 185, 129, 0.2)"
        ctx.beginPath()
        ctx.moveTo(40, height - 30)

        for (let i = 0; i < weeklyData.withHelmet.length; i++) {
          const x = 40 + i * ((width - 60) / (weeklyData.withHelmet.length - 1))
          const y = height - 30 - (weeklyData.withHelmet[i] / maxValue) * (height - 50)
          ctx.lineTo(x, y)
        }

        ctx.lineTo(width - 20, height - 30)
        ctx.closePath()
        ctx.fill()

        // 헬멧 착용 선 그리기
        ctx.strokeStyle = "#10b981"
        ctx.lineWidth = 2
        ctx.beginPath()

        for (let i = 0; i < weeklyData.withHelmet.length; i++) {
          const x = 40 + i * ((width - 60) / (weeklyData.withHelmet.length - 1))
          const y = height - 30 - (weeklyData.withHelmet[i] / maxValue) * (height - 50)

          if (i === 0) {
            ctx.moveTo(x, y)
          } else {
            ctx.lineTo(x, y)
          }
        }

        ctx.stroke()

        // 헬멧 미착용 선 그리기
        ctx.strokeStyle = "#ef4444"
        ctx.lineWidth = 2
        ctx.beginPath()

        for (let i = 0; i < weeklyData.withoutHelmet.length; i++) {
          const x = 40 + i * ((width - 60) / (weeklyData.withoutHelmet.length - 1))
          const y = height - 30 - (weeklyData.withoutHelmet[i] / maxValue) * (height - 50)

          if (i === 0) {
            ctx.moveTo(x, y)
          } else {
            ctx.lineTo(x, y)
          }
        }

        ctx.stroke()

        // 범례 그리기
        const legendY = height - 60

        // 헬멧 착용 범례
        ctx.fillStyle = "#10b981"
        ctx.beginPath()
        ctx.arc(width / 2 - 80, legendY, 6, 0, Math.PI * 2)
        ctx.fill()

        ctx.fillStyle = "#374151"
        ctx.font = "12px Arial"
        ctx.textAlign = "left"
        ctx.fillText("헬멧 착용", width / 2 - 70, legendY + 4)

        // 헬멧 미착용 범례
        ctx.fillStyle = "#ef4444"
        ctx.beginPath()
        ctx.arc(width / 2 + 20, legendY, 6, 0, Math.PI * 2)
        ctx.fill()

        ctx.fillStyle = "#374151"
        ctx.fillText("헬멧 미착용", width / 2 + 30, legendY + 4)
      }

      drawChart()

      // 창 크기 변경 시 차트 다시 그리기
      window.addEventListener("resize", drawChart)
      return () => {
        window.removeEventListener("resize", drawChart)
      }
    }
  }, [mounted])

  // 진행 바 렌더링 함수
  const renderProgressBar = (value: number, color: string) => {
    return (
      <div className="w-full bg-gray-200 rounded-full h-2.5 mt-1 mb-4">
        <div className={`h-2.5 rounded-full ${color}`} style={{ width: `${value}%` }}></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-red-600 text-white py-4">
        <div className="container mx-auto px-4 flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold flex items-center">
            <Shield className="mr-2" /> 오토바이 라이프 가드
          </Link>
          <nav className="hidden md:block">
            <ul className="flex space-x-6">
              <li>
                <Link href="/" className="hover:underline">
                  홈
                </Link>
              </li>
              <li>
                <Link href="/demo" className="hover:underline">
                  데모
                </Link>
              </li>
              <li>
                <Link href="/statistics" className="hover:underline font-bold">
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
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">통계</h1>
          <p className="text-gray-600">헬멧 감지 결과의 종합적인 통계 및 분석.</p>
        </div>

        {/* 주요 통계 카드 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {/* 총 감지 */}
          <Card>
            <CardContent className="p-6">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-1">총 감지</p>
                  <h3 className="text-3xl font-bold">{stats.totalDetections.toLocaleString()}</h3>
                  <p className="text-sm text-green-600 flex items-center mt-1">
                    <TrendingUp className="h-4 w-4 mr-1" />
                    지난 주 대비 +{stats.totalIncrease}%
                  </p>
                </div>
                <div className="bg-blue-100 p-2 rounded-full">
                  <Shield className="h-5 w-5 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 헬멧 미착용 */}
          <Card>
            <CardContent className="p-6">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-1">헬멧 미착용</p>
                  <h3 className="text-3xl font-bold">{stats.withoutHelmet.toLocaleString()}</h3>
                  <p className="text-sm text-gray-500 mt-1">총 감지의 {stats.withoutHelmetPercentage}%</p>
                </div>
                <div className="bg-red-100 p-2 rounded-full">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 헬멧 착용 */}
          <Card>
            <CardContent className="p-6">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-1">헬멧 착용</p>
                  <h3 className="text-3xl font-bold">{stats.withHelmet.toLocaleString()}</h3>
                  <p className="text-sm text-gray-500 mt-1">총 감지의 {stats.withHelmetPercentage}%</p>
                </div>
                <div className="bg-green-100 p-2 rounded-full">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 감지 정확도 */}
          <Card>
            <CardContent className="p-6">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-1">감지 정확도</p>
                  <h3 className="text-3xl font-bold">{stats.accuracy}%</h3>
                  <p className="text-sm text-green-600 flex items-center mt-1">
                    <TrendingUp className="h-4 w-4 mr-1" />
                    지난 주 대비 +{stats.accuracyIncrease}%
                  </p>
                </div>
                <div className="bg-blue-100 p-2 rounded-full">
                  <Info className="h-5 w-5 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 상세 통계 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* 헬멧 감지 통계 차트 */}
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold mb-1">헬멧 감지 통계</h3>
              <p className="text-sm text-gray-500 mb-4">시간에 따른 헬멧 사용 분석</p>

              <Tabs defaultValue="주간" className="mb-4">
                <TabsList>
                  <TabsTrigger value="주간" onClick={() => setTimeRange("주간")}>
                    주간
                  </TabsTrigger>
                  <TabsTrigger value="월간" onClick={() => setTimeRange("월간")}>
                    월간
                  </TabsTrigger>
                </TabsList>
              </Tabs>

              <div className="relative h-64 w-full">
                <canvas id="detectionChart" width="600" height="300" className="w-full h-full"></canvas>
              </div>
            </CardContent>
          </Card>

          {/* 감지 지표 */}
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold mb-1">감지 지표</h3>
              <p className="text-sm text-gray-500 mb-4">모델 성능 및 정확도 지표</p>

              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">정확 인식 지수</span>
                    <span className="text-sm font-medium">{stats.correctDetection}%</span>
                  </div>
                  {renderProgressBar(stats.correctDetection, "bg-green-500")}
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">감지 정확도</span>
                    <span className="text-sm font-medium">{stats.detectionAccuracy}%</span>
                  </div>
                  {renderProgressBar(stats.detectionAccuracy, "bg-blue-600")}
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">거짓 양성</span>
                    <span className="text-sm font-medium">{stats.falsePositive}%</span>
                  </div>
                  {renderProgressBar(stats.falsePositive, "bg-yellow-400")}
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">거짓 음성</span>
                    <span className="text-sm font-medium">{stats.falseNegative}%</span>
                  </div>
                  {renderProgressBar(stats.falseNegative, "bg-red-500")}
                </div>
              </div>
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
