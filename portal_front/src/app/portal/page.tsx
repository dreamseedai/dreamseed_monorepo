// portal_front/src/app/portal/page.tsx

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";

type MeResponse = {
  id: string;
  email: string;
  role: string; // "student" | "teacher" | "parent" | ...
};

export default function PortalEntryPage() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        const me = await api<MeResponse>("/auth/me");
        if (cancelled) return;

        switch (me.role) {
          case "student":
            navigate("/portal/student", { replace: true });
            break;
          case "parent":
            navigate("/portal/parent", { replace: true });
            break;
          case "teacher":
            // 기본은 학교 선생님 포털로 보냄
            // (학원 튜터는 직접 /portal/tutor로 접근하거나,
            //  나중에 /auth/me 확장해서 org_type에 따라 자동 분기 가능)
            navigate("/portal/teacher", { replace: true });
            break;
          default:
            setError(`현재 역할(${me.role})에 대한 포털이 없습니다.`);
        }
      } catch (err: any) {
        if (!cancelled) {
          setError(
            err?.message ??
              "로그인을 확인할 수 없습니다. 다시 로그인 후 이용해 주세요."
          );
        }
      }
    }

    init();
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 max-w-md">
          <h2 className="text-lg font-semibold text-red-900 mb-2">접근 오류</h2>
          <p className="text-sm text-red-700 whitespace-pre-line">{error}</p>
          <a
            href="/"
            className="mt-4 inline-block text-sm text-red-600 hover:underline"
          >
            ← 홈으로 돌아가기
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
        <p className="text-sm text-gray-600">포털로 이동 중입니다...</p>
      </div>
    </div>
  );
}
