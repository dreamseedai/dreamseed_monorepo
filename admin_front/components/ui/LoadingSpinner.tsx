/**
 * LoadingSpinner.tsx
 * 
 * DreamSeed Admin UI - Loading spinner component
 */

import React from "react";

export const LoadingSpinner: React.FC<{ message?: string }> = ({
  message = "로딩 중...",
}) => (
  <div className="flex flex-col items-center justify-center h-64 gap-4">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-600 dark:border-sky-400"></div>
    <p className="text-sm text-slate-500 dark:text-gray-400">{message}</p>
  </div>
);

export const ErrorMessage: React.FC<{ message?: string }> = ({
  message = "데이터를 불러올 수 없습니다.",
}) => (
  <div className="p-6">
    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
      <h3 className="text-red-800 dark:text-red-400 font-semibold mb-2">
        오류 발생
      </h3>
      <p className="text-red-600 dark:text-red-300 text-sm">{message}</p>
    </div>
  </div>
);
