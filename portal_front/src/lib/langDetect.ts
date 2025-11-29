/**
 * 브라우저 언어 감지 유틸리티
 * ==============================
 * Accept-Language 파싱 및 지원 언어 화이트리스트 적용.
 */

/** 지원 언어 */
export const SUPPORTED_LANGS = ["ko", "en", "zh-Hans", "zh-Hant"] as const;
export type SupportedLang = typeof SUPPORTED_LANGS[number];

/** 기본 언어 */
export const DEFAULT_LANG: SupportedLang = "ko";

/**
 * Accept-Language 헤더 파싱
 * 
 * @param header - Accept-Language 헤더 값
 * @returns (언어코드, 우선순위) 배열, 우선순위 내림차순 정렬
 * 
 * @example
 * ```ts
 * parseAcceptLanguage("ko-KR,ko;q=0.9,en;q=0.8")
 * // [["ko-KR", 1.0], ["ko", 0.9], ["en", 0.8]]
 * ```
 */
export function parseAcceptLanguage(header: string): [string, number][] {
  if (!header) return [];

  const langs: [string, number][] = [];

  for (const part of header.split(",")) {
    const trimmed = part.trim();
    if (!trimmed) continue;

    if (trimmed.includes(";q=")) {
      const [lang, qStr] = trimmed.split(";q=");
      const q = parseFloat(qStr) || 1.0;
      langs.push([lang.trim(), q]);
    } else {
      langs.push([trimmed, 1.0]);
    }
  }

  // 우선순위 내림차순 정렬
  langs.sort((a, b) => b[1] - a[1]);

  return langs;
}

/**
 * 언어 코드 정규화
 * 
 * @param code - 언어 코드 (예: 'ko-KR', 'zh-Hans', 'en-US')
 * @returns 정규화된 언어 코드 또는 null
 * 
 * @example
 * ```ts
 * normalizeLangCode('ko-KR') // 'ko'
 * normalizeLangCode('zh-TW') // 'zh-Hant'
 * normalizeLangCode('ja')    // null (지원하지 않음)
 * ```
 */
export function normalizeLangCode(code: string): SupportedLang | null {
  const lower = code.toLowerCase().trim();

  // 한국어
  if (lower.startsWith("ko")) return "ko";

  // 영어
  if (lower.startsWith("en")) return "en";

  // 중국어 간체
  if (
    lower === "zh-hans" ||
    lower === "zh-cn" ||
    lower === "zh-sg" ||
    lower === "zh-cmn-hans"
  ) {
    return "zh-Hans";
  }

  // 중국어 번체
  if (
    lower === "zh-hant" ||
    lower === "zh-tw" ||
    lower === "zh-hk" ||
    lower === "zh-mo" ||
    lower === "zh-cmn-hant"
  ) {
    return "zh-Hant";
  }

  // 중국어 (기본값: 간체)
  if (lower === "zh") return "zh-Hans";

  return null;
}

/**
 * 브라우저 언어 감지
 * 
 * @param forcedLang - 강제 언어 (쿼리 파라미터 또는 로컬 스토리지)
 * @returns 감지된 언어 코드
 * 
 * @example
 * ```ts
 * detectBrowserLanguage() // 'ko' (브라우저 설정 기반)
 * detectBrowserLanguage('en') // 'en' (강제 지정)
 * ```
 */
export function detectBrowserLanguage(
  forcedLang?: string | null
): SupportedLang {
  // 1. 강제 언어 (최우선)
  if (forcedLang) {
    const normalized = normalizeLangCode(forcedLang);
    if (normalized) return normalized;
  }

  // 2. 브라우저 언어 (navigator.language)
  if (navigator.language) {
    const normalized = normalizeLangCode(navigator.language);
    if (normalized) return normalized;
  }

  // 3. 브라우저 언어 목록 (navigator.languages)
  if (navigator.languages) {
    for (const lang of navigator.languages) {
      const normalized = normalizeLangCode(lang);
      if (normalized) return normalized;
    }
  }

  // 4. 기본값
  return DEFAULT_LANG;
}

/**
 * 로컬 스토리지에서 언어 가져오기
 */
export function getLangFromStorage(): SupportedLang | null {
  try {
    const stored = localStorage.getItem("lang");
    if (stored && SUPPORTED_LANGS.includes(stored as SupportedLang)) {
      return stored as SupportedLang;
    }
  } catch {
    // localStorage 접근 실패 (SSR 등)
  }
  return null;
}

/**
 * 로컬 스토리지에 언어 저장
 */
export function saveLangToStorage(lang: SupportedLang): void {
  try {
    localStorage.setItem("lang", lang);
  } catch {
    // localStorage 접근 실패 무시
  }
}

/**
 * URL 쿼리 파라미터에서 언어 가져오기
 */
export function getLangFromQuery(): SupportedLang | null {
  try {
    const params = new URLSearchParams(window.location.search);
    const lang = params.get("lang");
    if (lang && SUPPORTED_LANGS.includes(lang as SupportedLang)) {
      return lang as SupportedLang;
    }
  } catch {
    // URL 파싱 실패
  }
  return null;
}

/**
 * 최종 언어 결정 (우선순위 적용)
 * 
 * 우선순위:
 * 1. URL 쿼리 파라미터 (?lang=)
 * 2. 로컬 스토리지
 * 3. 브라우저 설정
 * 4. 기본값
 */
export function resolveLanguage(): SupportedLang {
  // 1. URL 쿼리
  const queryLang = getLangFromQuery();
  if (queryLang) {
    saveLangToStorage(queryLang); // 저장
    return queryLang;
  }

  // 2. 로컬 스토리지
  const storedLang = getLangFromStorage();
  if (storedLang) {
    return storedLang;
  }

  // 3. 브라우저 설정
  const browserLang = detectBrowserLanguage();
  saveLangToStorage(browserLang); // 저장

  return browserLang;
}
