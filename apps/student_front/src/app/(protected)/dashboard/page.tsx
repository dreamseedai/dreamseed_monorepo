import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">학생 대시보드</h1>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-3">
        <Link
          href="/exams"
          className="block rounded-lg border bg-white p-6 transition hover:border-blue-500 hover:shadow-md"
        >
          <div className="text-3xl">📝</div>
          <h3 className="mt-2 font-semibold">시험 보기</h3>
          <p className="mt-1 text-sm text-gray-500">
            진단 평가 및 학습 평가 응시
          </p>
        </Link>

        <Link
          href="/study-plan"
          className="block rounded-lg border bg-white p-6 transition hover:border-blue-500 hover:shadow-md"
        >
          <div className="text-3xl">📚</div>
          <h3 className="mt-2 font-semibold">학습 계획</h3>
          <p className="mt-1 text-sm text-gray-500">
            개인화된 학습 플랜 확인
          </p>
        </Link>

        <Link
          href="/results"
          className="block rounded-lg border bg-white p-6 transition hover:border-blue-500 hover:shadow-md"
        >
          <div className="text-3xl">📊</div>
          <h3 className="mt-2 font-semibold">성적 분석</h3>
          <p className="mt-1 text-sm text-gray-500">
            시험 결과 및 추이 분석
          </p>
        </Link>
      </div>

      {/* Upcoming Exams */}
      <div className="rounded-lg border bg-white p-6">
        <h2 className="text-lg font-semibold">다가오는 시험</h2>
        <div className="mt-4 text-sm text-gray-500">
          예정된 시험이 없습니다.
        </div>
      </div>

      {/* Recent Results */}
      <div className="rounded-lg border bg-white p-6">
        <h2 className="text-lg font-semibold">최근 결과</h2>
        <div className="mt-4 space-y-3">
          <div className="text-sm text-gray-500">
            아직 응시한 시험이 없습니다.
          </div>
          {/* Future: Map through recent exam results */}
        </div>
      </div>

      {/* Study Progress (Placeholder) */}
      <div className="rounded-lg border bg-white p-6">
        <h2 className="text-lg font-semibold">학습 진행 상황</h2>
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">이번 주 학습 시간</span>
            <span className="font-semibold text-gray-900">0시간</span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-gray-200">
            <div className="h-full w-0 bg-blue-600"></div>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-gray-900">0</div>
              <div className="text-xs text-gray-500">완료한 문제</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">0</div>
              <div className="text-xs text-gray-500">정답률</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">0</div>
              <div className="text-xs text-gray-500">연속 학습일</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
