"use client";

import { useEffect, useState } from "react";
import { getCurrentUser, User } from "@/lib/authClient";

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [isEditingName, setIsEditingName] = useState(false);
  const [fullName, setFullName] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    getCurrentUser()
      .then((userData) => {
        setUser(userData);
        setFullName(userData?.full_name || "");
      })
      .catch(console.error);
  }, []);

  const handleUpdateName = async () => {
    if (!fullName.trim()) {
      setMessage({ type: "error", text: "이름을 입력해주세요." });
      return;
    }

    setIsUpdating(true);
    setMessage(null);

    try {
      // TODO: API 엔드포인트 구현 필요 (PUT /api/auth/me)
      // const response = await fetch('http://localhost:8000/api/auth/me', {
      //   method: 'PATCH',
      //   headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
      //   body: JSON.stringify({ full_name: fullName })
      // });
      // const updatedUser = await response.json();
      
      // 임시: 로컬 상태만 업데이트
      setUser({ ...user!, full_name: fullName });
      setIsEditingName(false);
      setMessage({ type: "success", text: "이름이 업데이트되었습니다." });
    } catch (error) {
      console.error("Failed to update name:", error);
      setMessage({ type: "error", text: "업데이트에 실패했습니다." });
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">프로필 설정</h1>

      {message && (
        <div
          className={`rounded-lg p-4 ${
            message.type === "success" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* 계정 정보 */}
      <div className="rounded-lg border bg-white p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">계정 정보</h2>
          <div className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-700 font-semibold">
              {user?.full_name?.[0]?.toUpperCase() || "U"}
            </div>
          </div>
        </div>

        <div className="mt-6 space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-600">이메일</label>
            <div className="mt-1 text-gray-900">{user?.email || "로딩 중..."}</div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-600">역할</label>
            <div className="mt-1">
              <span className="inline-flex rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-800">
                {user?.role || "로딩 중..."}
              </span>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-600">이름</label>
            {isEditingName ? (
              <div className="mt-1 flex gap-2">
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="이름을 입력하세요"
                />
                <button
                  onClick={handleUpdateName}
                  disabled={isUpdating}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {isUpdating ? "저장 중..." : "저장"}
                </button>
                <button
                  onClick={() => {
                    setIsEditingName(false);
                    setFullName(user?.full_name || "");
                    setMessage(null);
                  }}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  취소
                </button>
              </div>
            ) : (
              <div className="mt-1 flex items-center justify-between">
                <span className="text-gray-900">{user?.full_name || "미설정"}</span>
                <button
                  onClick={() => setIsEditingName(true)}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  수정
                </button>
              </div>
            )}
          </div>

          <div>
            <label className="text-sm font-medium text-gray-600">가입일</label>
            <div className="mt-1 text-gray-900">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString("ko-KR") : "-"}
            </div>
          </div>
        </div>
      </div>

      {/* 학습 통계 */}
      <div className="rounded-lg border bg-white p-6">
        <h2 className="text-lg font-semibold">학습 통계</h2>
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">12</div>
            <div className="mt-1 text-sm text-gray-600">완료한 시험</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">87</div>
            <div className="mt-1 text-sm text-gray-600">평균 점수</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">24h</div>
            <div className="mt-1 text-sm text-gray-600">총 학습 시간</div>
          </div>
        </div>
      </div>

      {/* 비밀번호 변경 */}
      <div className="rounded-lg border bg-white p-6">
        <h2 className="text-lg font-semibold">비밀번호 변경</h2>
        <p className="mt-2 text-sm text-gray-500">
          비밀번호 변경 기능은 Phase 1B에서 구현 예정입니다.
        </p>
        <button
          disabled
          className="mt-4 rounded-lg bg-gray-300 px-4 py-2 text-sm font-medium text-gray-500 cursor-not-allowed"
        >
          비밀번호 변경
        </button>
      </div>

      {/* 알림 설정 */}
      <div className="rounded-lg border bg-white p-6">
        <h2 className="text-lg font-semibold">알림 설정</h2>
        <div className="mt-4 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-gray-900">이메일 알림</div>
              <div className="text-sm text-gray-500">시험 결과 및 학습 리포트</div>
            </div>
            <label className="relative inline-flex cursor-pointer items-center">
              <input type="checkbox" className="peer sr-only" defaultChecked />
              <div className="peer h-6 w-11 rounded-full bg-gray-200 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-blue-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300"></div>
            </label>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-gray-900">푸시 알림</div>
              <div className="text-sm text-gray-500">시험 일정 알림</div>
            </div>
            <label className="relative inline-flex cursor-pointer items-center">
              <input type="checkbox" className="peer sr-only" />
              <div className="peer h-6 w-11 rounded-full bg-gray-200 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-blue-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300"></div>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
