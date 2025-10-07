import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useLanguage } from "../contexts/LanguageContext";

type Me = { anon: boolean; name?: string };

export default function UserStatus() {
  const [me, setMe] = useState<Me>({ anon: true });
  const [showMenu, setShowMenu] = useState(false);
  const { t } = useLanguage();

  const reload = async () => {
    try {
      const j = await api<Me>("/auth/me");
      setMe(j);
    } catch {
      setMe({ anon: true });
    }
  };

  useEffect(() => {
    reload();
    const handler = () => { reload(); };
    window.addEventListener("auth:changed", handler);
    return () => window.removeEventListener("auth:changed", handler);
  }, []);

  const handleMenuClick = (path: string) => {
    window.location.href = path;
    setShowMenu(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        className="flex items-center gap-2 px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      >
        <span className="text-xs opacity-75">
          {me.anon ? "(anon)" : me.name ?? "(unknown)"}
        </span>
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {showMenu && (
        <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 z-50">
          <div className="py-1">
            <button
              onClick={() => handleMenuClick('/pricing')}
              className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              {t('nav.plans')}
            </button>
            <button
              onClick={() => handleMenuClick('/saved')}
              className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              {t('nav.saved')}
            </button>
            <button
              onClick={() => handleMenuClick('/content/list')}
              className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              {t('nav.content')}
            </button>
            <hr className="my-1 border-gray-200 dark:border-gray-600" />
            <button
              onClick={() => handleMenuClick('/login')}
              className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              {t('nav.login')}
            </button>
          </div>
        </div>
      )}

      {/* Overlay to close menu when clicking outside */}
      {showMenu && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowMenu(false)}
        />
      )}
    </div>
  );
}
