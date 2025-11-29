"use client";

import React from "react";

type Props = {
  open: boolean;
  title: string;
  message: React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  disabled?: boolean;
  testId?: string;
};

export function ConfirmModal({
  open,
  title,
  message,
  confirmLabel = "확인",
  cancelLabel = "취소",
  onConfirm,
  onCancel,
  disabled = false,
  testId = "confirm-delete-dialog",
}: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/40"
        onClick={() => {
          if (!disabled) onCancel();
        }}
      />
      <div
        className="relative z-50 w-full max-w-sm rounded-md bg-white shadow-lg border p-4"
        role="dialog"
        aria-modal="true"
        data-testid={testId}
      >
        <h2 className="text-sm font-semibold mb-2">{title}</h2>
        <div className="text-sm text-gray-700 mb-4">{message}</div>
        <div className="flex items-center justify-end gap-2">
          <button
            className="px-3 py-1.5 rounded border text-sm"
            onClick={onCancel}
            disabled={disabled}
          >
            {cancelLabel}
          </button>
          <button
            className={`px-3 py-1.5 rounded text-sm ${disabled ? "bg-red-400 text-white" : "bg-red-600 text-white hover:bg-red-700"}`}
            onClick={onConfirm}
            disabled={disabled}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
