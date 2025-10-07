import React, { createContext, useContext, useState, useEffect } from 'react';

export type Language = 'en' | 'ko' | 'zh-TW' | 'zh-CN';

export interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

// Translation data
const translations = {
  en: {
    // Common
    'common.loading': 'Loading...',
    'common.error': 'Error',
    'common.success': 'Success',
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.confirm': 'Confirm',
    'common.close': 'Close',
    'common.back': 'Back',
    'common.next': 'Next',
    'common.finish': 'Finish',

    // Navigation
    'nav.home': 'Home',
    'nav.guides': 'Guides',
    'nav.plans': 'Plans',
    'nav.saved': 'Saved Plans',
    'nav.content': 'Content',
    'nav.login': 'Login',
    'nav.logout': 'Logout',

    // Home page
    'home.hero.title': 'Plan your path with DreamSeedAI',
    'home.hero.subtitle': 'Personalised guides, study plans, and expert recommendations for US/CA students',
    'home.hero.cta': 'Browse US Guides',
    'home.quick_start.title': 'Quick Start',
    'home.quick_start.subtitle': 'Select your country, grade, and goals to get a personalized study plan',
    'home.quick_start.cta': 'Get My Strategy',
    'home.quick_start.country': 'Country',
    'home.quick_start.grade': 'Grade',
    'home.quick_start.goal': 'Goal',
    'home.quick_start.loading': 'Running diagnostics...',
    'home.quick_start.error': 'Diagnostics failed. Please try again.',

    // Plans
    'plans.title': 'Pricing Plans',
    'plans.status': 'Billing Status:',
    'plans.note_enabled': 'Enabled',
    'plans.note_disabled': 'Disabled',
    'plans.free.name': 'Free',
    'plans.free.price': 'Free',
    'plans.free.blurb': 'Basic learning materials and guides',
    'plans.free.cta': 'Start Free',
    'plans.free.features': 'Basic learning materials|Study guides|Community support',
    'plans.pro.name': 'Pro',
    'plans.pro.price': '$25/month',
    'plans.pro.blurb': 'Personalized study plans and advanced features',
    'plans.pro.cta': 'Upgrade to Pro',
    'plans.pro.features': 'Everything in Free|Personalized study plans|Advanced analytics|Priority support',
    'plans.premium.name': 'Premium',
    'plans.premium.price': '$99/month (Student)',
    'plans.premium.blurb': 'Premium features with 1:1 mentoring',
    'plans.premium.cta': 'Upgrade to Premium',
    'plans.premium.features': 'Everything in Pro|1:1 mentoring sessions|Custom study schedules|Premium content access',
    'plans.compare_plans': 'Compare Plans',

    // Pricing page
    'pricing.title': 'Choose Your Plan',
    'pricing.subtitle': 'Select the perfect plan for your learning journey',
    'pricing.faq_title': 'Frequently Asked Questions',
    'pricing.faq1_q': 'Can I change my plan anytime?',
    'pricing.faq1_a': 'Yes, you can upgrade or downgrade your plan at any time. Changes will be reflected in your next billing cycle.',
    'pricing.faq2_q': 'What payment methods do you accept?',
    'pricing.faq2_a': 'We accept all major credit cards, PayPal, and bank transfers.',
    'pricing.faq3_q': 'Is there a free trial?',
    'pricing.faq3_a': 'Yes, you can start with our free plan and upgrade when you\'re ready for more features.',

    // Plan Result
    'plan.title': 'Plan Results',
    'plan.summary.title': 'Custom Strategy Summary',
    'plan.summary.label': 'Summary',
    'plan.weaknesses.title': 'Weaknesses',
    'plan.modules.title': 'Recommended Modules',
    'plan.problems.title': 'Recommended Problems',
    'plan.next_week.title': 'Next Week Plan',
    'plan.actions.save': 'Save Locally',
    'plan.actions.copy': 'Copy Link',
    'plan.actions.pdf': 'Export PDF',
    'plan.actions.calendar': 'Calendar(.ics)',
    'plan.actions.reset': 'Reset',
    'plan.actions.start_pro': 'Start with Pro',
    'plan.calendar.add_to_google': 'Add to Google Calendar',

    // Language selector
    'language.selector': 'Language',
    'language.english': 'English',
    'language.korean': '한국어',
    'language.chinese_traditional': '繁體中文',
    'language.chinese_simplified': '简体中文',
  },
  ko: {
    // Common
    'common.loading': '로딩 중...',
    'common.error': '오류',
    'common.success': '성공',
    'common.save': '저장',
    'common.cancel': '취소',
    'common.confirm': '확인',
    'common.close': '닫기',
    'common.back': '뒤로',
    'common.next': '다음',
    'common.finish': '완료',

    // Navigation
    'nav.home': '홈',
    'nav.guides': '가이드',
    'nav.plans': '플랜',
    'nav.saved': '저장된 플랜',
    'nav.content': '콘텐츠',
    'nav.login': '로그인',
    'nav.logout': '로그아웃',

    // Home page
    'home.hero.title': 'DreamSeedAI와 함께 경로를 계획하세요',
    'home.hero.subtitle': '미국/캐나다 학생들을 위한 맞춤형 가이드, 학습 계획 및 전문가 추천',
    'home.hero.cta': '미국 가이드 둘러보기',
    'home.quick_start.title': '빠른 시작',
    'home.quick_start.subtitle': '국가, 학년, 목표를 선택하여 맞춤형 학습 계획을 받으세요',
    'home.quick_start.cta': '내 전략 보기',
    'home.quick_start.country': '국가',
    'home.quick_start.grade': '학년',
    'home.quick_start.goal': '목표',
    'home.quick_start.loading': '진단 실행 중...',
    'home.quick_start.error': '진단 실행에 실패했습니다. 다시 시도해주세요.',

    // Plans
    'plans.title': '요금제',
    'plans.status': '결제 상태:',
    'plans.note_enabled': '활성화됨',
    'plans.note_disabled': '비활성화됨',
    'plans.free.name': '무료',
    'plans.free.price': '무료',
    'plans.free.blurb': '기본 학습 자료 및 가이드',
    'plans.free.cta': '무료로 시작',
    'plans.free.features': '기본 학습 자료|학습 가이드|커뮤니티 지원',
    'plans.pro.name': '프로',
    'plans.pro.price': '월 $25',
    'plans.pro.blurb': '맞춤형 학습 계획 및 고급 기능',
    'plans.pro.cta': '프로로 업그레이드',
    'plans.pro.features': '무료 플랜의 모든 기능|맞춤형 학습 계획|고급 분석|우선 지원',
    'plans.premium.name': '프리미엄',
    'plans.premium.price': '월 $99 (학생)',
    'plans.premium.blurb': '1:1 멘토링이 포함된 프리미엄 기능',
    'plans.premium.cta': '프리미엄으로 업그레이드',
    'plans.premium.features': '프로 플랜의 모든 기능|1:1 멘토링 세션|맞춤형 학습 일정|프리미엄 콘텐츠 접근',
    'plans.compare_plans': '플랜 비교',

    // Pricing page
    'pricing.title': '플랜 선택',
    'pricing.subtitle': '학습 여정에 맞는 완벽한 플랜을 선택하세요',
    'pricing.faq_title': '자주 묻는 질문',
    'pricing.faq1_q': '언제든지 플랜을 변경할 수 있나요?',
    'pricing.faq1_a': '네, 언제든지 플랜을 업그레이드하거나 다운그레이드할 수 있습니다. 변경사항은 다음 결제 주기에 반영됩니다.',
    'pricing.faq2_q': '어떤 결제 방법을 지원하나요?',
    'pricing.faq2_a': '모든 주요 신용카드, PayPal, 은행 송금을 지원합니다.',
    'pricing.faq3_q': '무료 체험판이 있나요?',
    'pricing.faq3_a': '네, 무료 플랜으로 시작하여 더 많은 기능이 필요할 때 업그레이드할 수 있습니다.',

    // Plan Result
    'plan.title': '플랜 결과',
    'plan.summary.title': '맞춤 전략 요약',
    'plan.summary.label': '요약',
    'plan.weaknesses.title': '약점',
    'plan.modules.title': '권장 모듈',
    'plan.problems.title': '권장 문제',
    'plan.next_week.title': '다음 주 계획',
    'plan.actions.save': '로컬 저장',
    'plan.actions.copy': '링크 복사',
    'plan.actions.pdf': 'PDF 내보내기',
    'plan.actions.calendar': '캘린더(.ics)',
    'plan.actions.reset': '다시 설정',
    'plan.actions.start_pro': 'Pro로 시작',
    'plan.calendar.add_to_google': 'Google 캘린더에 추가',

    // Language selector
    'language.selector': '언어',
    'language.english': 'English',
    'language.korean': '한국어',
    'language.chinese_traditional': '繁體中文',
    'language.chinese_simplified': '简体中文',
  },
  'zh-TW': {
    // Common
    'common.loading': '載入中...',
    'common.error': '錯誤',
    'common.success': '成功',
    'common.save': '儲存',
    'common.cancel': '取消',
    'common.confirm': '確認',
    'common.close': '關閉',
    'common.back': '返回',
    'common.next': '下一步',
    'common.finish': '完成',

    // Navigation
    'nav.home': '首頁',
    'nav.guides': '指南',
    'nav.plans': '方案',
    'nav.saved': '已儲存的方案',
    'nav.content': '內容',
    'nav.login': '登入',
    'nav.logout': '登出',

    // Home page
    'home.hero.title': '與 DreamSeedAI 一起規劃您的道路',
    'home.hero.subtitle': '為美國/加拿大學生提供個人化指南、學習計劃和專家建議',
    'home.hero.cta': '瀏覽美國指南',
    'home.quick_start.title': '快速開始',
    'home.quick_start.subtitle': '選擇您的國家、年級和目標，獲得個人化學習計劃',
    'home.quick_start.cta': '查看我的策略',
    'home.quick_start.country': '國家',
    'home.quick_start.grade': '年級',
    'home.quick_start.goal': '目標',
    'home.quick_start.loading': '正在執行診斷...',
    'home.quick_start.error': '診斷執行失敗。請重試。',

    // Plans
    'plans.title': '定價方案',
    'plans.free.name': '免費',
    'plans.free.price': '免費',
    'plans.free.blurb': '基本學習材料和指南',
    'plans.free.cta': '免費開始',
    'plans.pro.name': '專業版',
    'plans.pro.price': '每月 $25',
    'plans.pro.blurb': '個人化學習計劃和高級功能',
    'plans.pro.cta': '升級到專業版',
    'plans.premium.name': '高級版',
    'plans.premium.price': '每月 $99 (學生)',
    'plans.premium.blurb': '包含 1:1 指導的高級功能',
    'plans.premium.cta': '升級到高級版',

    // Plan Result
    'plan.title': '方案結果',
    'plan.summary.title': '個人化策略摘要',
    'plan.summary.label': '摘要',
    'plan.weaknesses.title': '弱點',
    'plan.modules.title': '推薦模組',
    'plan.problems.title': '推薦問題',
    'plan.next_week.title': '下週計劃',
    'plan.actions.save': '本地儲存',
    'plan.actions.copy': '複製連結',
    'plan.actions.pdf': '匯出 PDF',
    'plan.actions.calendar': '日曆(.ics)',
    'plan.actions.reset': '重新設定',
    'plan.actions.start_pro': '開始使用專業版',
    'plan.calendar.add_to_google': '新增到 Google 日曆',

    // Language selector
    'language.selector': '語言',
    'language.english': 'English',
    'language.korean': '한국어',
    'language.chinese_traditional': '繁體中文',
    'language.chinese_simplified': '简体中文',
  },
  'zh-CN': {
    // Common
    'common.loading': '加载中...',
    'common.error': '错误',
    'common.success': '成功',
    'common.save': '保存',
    'common.cancel': '取消',
    'common.confirm': '确认',
    'common.close': '关闭',
    'common.back': '返回',
    'common.next': '下一步',
    'common.finish': '完成',

    // Navigation
    'nav.home': '首页',
    'nav.guides': '指南',
    'nav.plans': '方案',
    'nav.saved': '已保存的方案',
    'nav.content': '内容',
    'nav.login': '登录',
    'nav.logout': '登出',

    // Home page
    'home.hero.title': '与 DreamSeedAI 一起规划您的道路',
    'home.hero.subtitle': '为美国/加拿大学生提供个性化指南、学习计划和专家建议',
    'home.hero.cta': '浏览美国指南',
    'home.quick_start.title': '快速开始',
    'home.quick_start.subtitle': '选择您的国家、年级和目标，获得个性化学习计划',
    'home.quick_start.cta': '查看我的策略',
    'home.quick_start.country': '国家',
    'home.quick_start.grade': '年级',
    'home.quick_start.goal': '目标',
    'home.quick_start.loading': '正在执行诊断...',
    'home.quick_start.error': '诊断执行失败。请重试。',

    // Plans
    'plans.title': '定价方案',
    'plans.free.name': '免费',
    'plans.free.price': '免费',
    'plans.free.blurb': '基本学习材料和指南',
    'plans.free.cta': '免费开始',
    'plans.pro.name': '专业版',
    'plans.pro.price': '每月 $25',
    'plans.pro.blurb': '个性化学习计划和高级功能',
    'plans.pro.cta': '升级到专业版',
    'plans.premium.name': '高级版',
    'plans.premium.price': '每月 $99 (学生)',
    'plans.premium.blurb': '包含 1:1 指导的高级功能',
    'plans.premium.cta': '升级到高级版',

    // Plan Result
    'plan.title': '方案结果',
    'plan.summary.title': '个性化策略摘要',
    'plan.summary.label': '摘要',
    'plan.weaknesses.title': '弱点',
    'plan.modules.title': '推荐模块',
    'plan.problems.title': '推荐问题',
    'plan.next_week.title': '下周计划',
    'plan.actions.save': '本地保存',
    'plan.actions.copy': '复制链接',
    'plan.actions.pdf': '导出 PDF',
    'plan.actions.calendar': '日历(.ics)',
    'plan.actions.reset': '重新设置',
    'plan.actions.start_pro': '开始使用专业版',
    'plan.calendar.add_to_google': '添加到 Google 日历',

    // Language selector
    'language.selector': '语言',
    'language.english': 'English',
    'language.korean': '한국어',
    'language.chinese_traditional': '繁體中文',
    'language.chinese_simplified': '简体中文',
  }
};

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    try {
      // Get language from localStorage or detect from browser
      const saved = localStorage.getItem('dreamseed.language') as Language;
      if (saved && ['en', 'ko', 'zh-TW', 'zh-CN'].includes(saved)) {
        return saved;
      }

      // Detect from browser language
      const browserLang = navigator.language;
      if (browserLang.startsWith('ko')) return 'ko';
      if (browserLang.startsWith('zh-TW') || browserLang.startsWith('zh-HK')) return 'zh-TW';
      if (browserLang.startsWith('zh')) return 'zh-CN';
      return 'en'; // Default to English
    } catch (error) {
      console.warn('Language detection failed:', error);
      return 'en';
    }
  });

  const setLanguage = (lang: Language) => {
    try {
      setLanguageState(lang);
      localStorage.setItem('dreamseed.language', lang);
    } catch (error) {
      console.warn('Failed to save language:', error);
    }
  };

  const t = (key: string): string => {
    try {
      return translations[language]?.[key] || key;
    } catch (error) {
      console.warn('Translation failed:', error);
      return key;
    }
  };

  const contextValue = {
    language,
    setLanguage,
    t
  };

  return (
    <LanguageContext.Provider value={contextValue}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    // Fallback for when context is not available
    return {
      language: 'en' as Language,
      setLanguage: () => {},
      t: (key: string) => {
        // Fallback translations
        const fallbackTranslations: { [key: string]: string } = {
          'home.hero.title': 'Plan your path with DreamSeedAI',
          'home.hero.subtitle': 'Personalised guides, study plans, and expert recommendations for US/CA students',
          'home.hero.cta': 'Browse US Guides',
          'home.quick_start.title': 'Quick Start',
          'home.quick_start.subtitle': 'Select your country, grade, and goals to get a personalized study plan',
          'home.quick_start.country': 'Country',
          'home.quick_start.grade': 'Grade',
          'home.quick_start.goal': 'Goal',
          'home.quick_start.loading': 'Running diagnostics...',
          'home.quick_start.error': 'Diagnostics failed. Please try again.',
          'home.quick_start.cta': 'Get My Strategy',
          'nav.home': 'Home',
          'nav.guides': 'Guides',
          'nav.plans': 'Plans',
          'nav.saved': 'Saved Plans',
          'nav.content': 'Content',
          'nav.login': 'Login'
        };
        return fallbackTranslations[key] || key;
      }
    };
  }
  return context;
};
