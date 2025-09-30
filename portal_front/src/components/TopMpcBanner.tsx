import React from 'react';

export default function TopMpcBanner() {
  const raw = (import.meta as any).env?.VITE_MPC_TOP_IMAGE as string | undefined;
  const v = (globalThis as any).__APP_VERSION__ || '';
  const imageSrc = raw ? `${raw}${raw.includes('?') ? '&' : '?'}v=${v}` : undefined;
  const hasImage = typeof imageSrc === 'string' && imageSrc.trim().length > 0;

  return (
    <div className="w-full relative">
      {hasImage ? (
        <div className="w-full overflow-hidden">
          <img
            src={imageSrc}
            alt="MPCStudy.com Top"
            className="w-full h-auto object-cover"
            referrerPolicy="no-referrer"
          />
        </div>
      ) : null}
      <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/60 to-transparent p-3 sm:p-4">
        <div className="text-white text-sm sm:text-base">
          <span className="font-semibold">DreamSeedAI</span>는{' '}
          <a href="https://mpcstudy.com" target="_blank" rel="noreferrer" className="underline">
            MPCStudy.com
          </a>
          의 업그레이드 버전입니다.
        </div>
      </div>
    </div>
  );
}


