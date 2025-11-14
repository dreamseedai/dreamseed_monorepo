/**
 * i18n 환경 설정
 * ===============
 * 지원 언어 및 기본값 정의.
 */

/** 지원 언어 */
export const SUPPORTED = ["ko", "en", "zh-Hans", "zh-Hant"] as const;

/** 언어 타입 */
export type Lang = typeof SUPPORTED[number];

/** 기본 언어 (환경 변수 또는 'ko') */
export const FALLBACK: Lang = (import.meta.env.VITE_LANG_FALLBACK || "ko") as Lang;

/**
 * 언어 코드를 지원 언어로 제한.
 * 
 * @param lang - 언어 코드
 * @returns 지원하는 언어 또는 기본값
 */
export const clamp = (lang?: string): Lang =>
  (SUPPORTED as readonly string[]).includes(lang || "")
    ? (lang as Lang)
    : FALLBACK;
