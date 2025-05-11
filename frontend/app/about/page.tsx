import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Shield, ArrowRight, Brain, BarChart, AlertTriangle } from "lucide-react"

export default function About() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-red-600 text-white py-4">
        <div className="container mx-auto px-4 flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold flex items-center">
            <Shield className="mr-2" /> 오토바이 라이프 가드
          </Link>
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
                <Link href="/about" className="hover:underline font-bold">
                  소개
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </header>

      <main className="flex-grow">
        <section className="bg-gradient-to-b from-red-500 to-red-600 text-white py-16">
          <div className="container mx-auto px-4">
            <h1 className="text-4xl font-bold mb-6">프로젝트 소개</h1>
            <p className="text-xl max-w-3xl">
              오토바이 라이프 가드는 오토바이 운전자가 헬멧을 착용하지 않았을 때 이를 감지하고 경고하는 AI 기반 안전
              시스템으로, 부상을 줄이고 생명을 구하는 데 도움을 줍니다.
            </p>
          </div>
        </section>

        <section className="py-16 bg-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-3xl font-bold mb-8">우리의 미션</h2>
              <p className="text-lg mb-6">
                오토바이 사고는 전 세계적으로 교통 사망의 주요 원인이며, 머리 부상은 사망의 주요 원인입니다. 헬멧 착용은
                사망 위험을 최대 42%, 머리 부상 위험을 69%까지 줄일 수 있습니다.
              </p>
              <p className="text-lg mb-6">
                우리의 미션은 인공지능을 활용하여 오토바이 운전자들의 헬멧 착용률을 높이고, 궁극적으로 생명을 구하고
                사고 시 부상의 심각성을 줄이는 것입니다.
              </p>
              <div className="bg-red-50 border-l-4 border-red-500 p-4 my-8">
                <div className="flex">
                  <AlertTriangle className="h-6 w-6 text-red-600 mr-3 flex-shrink-0" />
                  <div>
                    <p className="font-bold text-red-700">문제점</p>
                    <p className="text-red-700">
                      많은 국가에서 헬멧 착용을 의무화하는 법률이 있음에도 불구하고, 준수는 여전히 과제로 남아 있습니다.
                      수동 단속은 자원 집약적이며 모든 지역을 항상 커버할 수 없습니다.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="py-16 bg-gray-50">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-3xl font-bold mb-8">기술</h2>

              <div className="mb-12">
                <h3 className="text-2xl font-semibold mb-4 flex items-center">
                  <Brain className="mr-2 text-red-600" /> YOLO (You Only Look Once)
                </h3>
                <p className="text-lg mb-4">
                  우리 시스템은 단일 프레임에서 여러 객체를 식별할 수 있는 최첨단 실시간 객체 감지 알고리즘인 YOLO를
                  사용합니다. 우리는 특별히 오토바이 헬멧 감지를 위해 모델을 최적화하고 훈련시켰습니다.
                </p>
                <div className="grid md:grid-cols-2 gap-6 mt-8">
                  <div className="bg-white p-6 rounded-lg shadow-sm">
                    <h4 className="font-semibold text-xl mb-3">YOLO 작동 방식</h4>
                    <p>
                      YOLO는 입력 이미지를 그리드로 나누고 각 그리드 셀에 대한 경계 상자와 클래스 확률을 예측합니다. 이
                      접근 방식은 여러 오토바이 운전자가 있는 복잡한 장면에서도 빠르고 효율적인 감지를 가능하게 합니다.
                    </p>
                  </div>
                  <div className="bg-white p-6 rounded-lg shadow-sm">
                    <h4 className="font-semibold text-xl mb-3">모델 최적화</h4>
                    <p>
                      우리는 헬멧 감지에서 높은 정확도를 유지하면서 다양한 하드웨어 구성에서 효율적으로 실행할 수 있는
                      YOLO 모델의 경량 버전을 만들었습니다.
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-2xl font-semibold mb-4 flex items-center">
                  <BarChart className="mr-2 text-red-600" /> 성능 지표
                </h3>
                <p className="text-lg mb-6">
                  우리 모델은 다양한 조건에서 오토바이 운전자의 다양한 데이터셋으로 훈련되고 테스트되어 다음과 같은
                  성과를 달성했습니다:
                </p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                  <div className="bg-white p-4 rounded-lg shadow-sm text-center">
                    <p className="text-3xl font-bold text-red-600">95%</p>
                    <p className="text-gray-600">정확도</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg shadow-sm text-center">
                    <p className="text-3xl font-bold text-red-600">92%</p>
                    <p className="text-gray-600">정밀도</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg shadow-sm text-center">
                    <p className="text-3xl font-bold text-red-600">94%</p>
                    <p className="text-gray-600">재현율</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg shadow-sm text-center">
                    <p className="text-3xl font-bold text-red-600">30ms</p>
                    <p className="text-gray-600">처리 시간</p>
                  </div>
                </div>
                <p className="text-lg">
                  이러한 지표는 우리 시스템이 다양한 조명 조건, 다양한 헬멧 유형, 단일 프레임에 여러 운전자가 있는
                  경우를 포함한 실제 시나리오에서 헬멧 착용 여부를 안정적으로 감지할 수 있음을 보장합니다.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="py-16 bg-red-50">
          <div className="container mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold mb-6">시도해 보시겠습니까?</h2>
            <p className="text-xl mb-8 max-w-2xl mx-auto">우리의 대화형 데모로 헬멧 감지 기술을 경험해 보세요.</p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Button asChild size="lg" className="bg-red-600 hover:bg-red-700">
                <Link href="/demo">
                  데모 시작하기 <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button asChild size="lg" className="bg-gray-700 hover:bg-gray-800">
                <Link href="/statistics">
                  통계 보기 <BarChart className="ml-2 h-5 w-5" />
                </Link>
              </Button>
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
