// apps/tutor_front/src/app/page.tsx
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-4 py-10">
      <h1 className="text-2xl font-bold">튜터 포털에 오신 것을 환영합니다 👋</h1>
      <p className="text-sm text-gray-600">
        이 포털은 DreamSeedAI의 IRT/CAT 데이터를 기반으로
        학생 개입 우선순위를 보여주는 튜터 전용 대시보드입니다.
      </p>
      <Link
        href="/tutor/dashboard"
        className="inline-flex rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
      >
        대시보드로 이동
      </Link>
    </div>
  );
}
