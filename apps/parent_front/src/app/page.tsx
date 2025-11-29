// apps/parent_front/src/app/page.tsx
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-4 py-10">
      <h1 className="text-2xl font-bold">학부모 포털에 오신 것을 환영합니다 👨‍👩‍👧‍👦</h1>
      <p className="text-sm text-gray-600">
        이 포털에서는 자녀의 학습 리포트를 PDF 형태로 확인하실 수 있습니다.
        학교 선생님, 학원 선생님, 튜터의 의견이 함께 포함됩니다.
      </p>
      <Link
        href="/parent/reports"
        className="inline-flex rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
      >
        리포트 보기
      </Link>
    </div>
  );
}
