import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, Shield, AlertTriangle, Upload, BarChart } from "lucide-react"

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      <header className="bg-red-600 text-white py-4">
        <div className="container mx-auto px-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold flex items-center">
            <Shield className="mr-2" /> 오토바이 라이프 가드
          </h1>
          <nav>
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

      <main className="flex-grow">
        {/* Hero Section */}
        <section className="bg-gradient-to-b from-red-500 to-red-600 text-white py-20">
          <div className="container mx-auto px-4 text-center">
            <h2 className="text-4xl md:text-5xl font-bold mb-6">AI 기반 오토바이 헬멧 감지 시스템</h2>
            <p className="text-xl mb-8 max-w-3xl mx-auto">
              YOLO 기반 경량화 AI 모델을 활용해 이미지 및 영상에서 헬멧 착용 여부를 감지하여 오토바이 운전자의 안전을
              향상시킵니다.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Button asChild size="lg" className="bg-white text-red-600 hover:bg-gray-100">
                <Link href="/demo">
                  데모 시작하기 <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button asChild size="lg" className="bg-white text-red-600 hover:bg-gray-100">
                <Link href="/statistics">
                  통계 보기 <BarChart className="ml-2 h-5 w-5" />
                </Link>
              </Button>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-16 bg-white">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12">주요 기능</h2>
            <div className="grid md:grid-cols-4 gap-8">
              <div className="bg-gray-50 p-6 rounded-lg shadow-sm">
                <div className="bg-red-100 p-3 rounded-full w-12 h-12 flex items-center justify-center mb-4">
                  <AlertTriangle className="text-red-600" />
                </div>
                <h3 className="text-xl font-semibold mb-3">실시간 감지</h3>
                <p className="text-gray-600">
                  이미지와 영상에서 헬멧을 착용하지 않은 오토바이 운전자를 즉시 식별합니다.
                </p>
              </div>
              <div className="bg-gray-50 p-6 rounded-lg shadow-sm">
                <div className="bg-red-100 p-3 rounded-full w-12 h-12 flex items-center justify-center mb-4">
                  <Upload className="text-red-600" />
                </div>
                <h3 className="text-xl font-semibold mb-3">쉬운 통합</h3>
                <p className="text-gray-600">
                  기존 카메라 시스템 및 감시 인프라와 함께 작동하도록 설계된 경량 모델입니다.
                </p>
              </div>
              <div className="bg-gray-50 p-6 rounded-lg shadow-sm">
                <div className="bg-red-100 p-3 rounded-full w-12 h-12 flex items-center justify-center mb-4">
                  <Shield className="text-red-600" />
                </div>
                <h3 className="text-xl font-semibold mb-3">안전 경고</h3>
                <p className="text-gray-600">헬멧을 착용하지 않은 운전자가 감지되면 자동 경고를 생성합니다.</p>
              </div>
              <div className="bg-gray-50 p-6 rounded-lg shadow-sm">
                <div className="bg-red-100 p-3 rounded-full w-12 h-12 flex items-center justify-center mb-4">
                  <BarChart className="text-red-600" />
                </div>
                <h3 className="text-xl font-semibold mb-3">통계 분석</h3>
                <p className="text-gray-600">
                  헬멧 착용 데이터를 수집하고 분석하여 안전 개선을 위한 인사이트를 제공합니다.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="bg-gray-900 text-white py-8">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0">
              <h2 className="text-xl font-bold flex items-center">
                <Shield className="mr-2" /> 오토바이 라이프 가드
              </h2>
              <p className="text-gray-400 mt-2">AI로 도로 안전 향상하기</p>
            </div>
            <div>
              <p className="text-gray-400">© {new Date().getFullYear()} 오토바이 라이프 가드. 모든 권리 보유.</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
