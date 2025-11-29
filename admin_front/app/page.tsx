'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function Home() {
  const router = useRouter();
  const [activeMenu, setActiveMenu] = useState('');

  const menuItems = [
    { id: 'questions', label: '문항 관리', path: '/questions', icon: '📝' },
    { id: 'topics', label: '주제 관리', path: '/topics', icon: '📚' },
    { id: 'stats', label: '통계', path: '/stats', icon: '📊' },
    { id: 'settings', label: '설정', path: '/settings', icon: '⚙️' },
  ];

  const handleMenuClick = (path: string, id: string) => {
    setActiveMenu(id);
    router.push(path);
  };

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-100 dark:bg-gray-800 shadow-lg">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-8">
            관리자 대시보드
          </h1>
          <nav className="space-y-2">
            {menuItems.map((item) => (
              <button
                key={item.id}
                onClick={() => handleMenuClick(item.path, item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  activeMenu === item.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
              >
                <span className="text-xl">{item.icon}</span>
                <span className="font-medium">{item.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8">
        <div className="max-w-4xl">
          <h2 className="text-3xl font-bold mb-4">환영합니다</h2>
          <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
            왼쪽 메뉴에서 원하는 관리 기능을 선택하세요.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {menuItems.map((item) => (
              <div
                key={item.id}
                onClick={() => handleMenuClick(item.path, item.id)}
                className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer border border-gray-200 dark:border-gray-700"
              >
                <div className="text-4xl mb-3">{item.icon}</div>
                <h3 className="text-xl font-semibold mb-2">{item.label}</h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  {item.id === 'questions' && '문항을 추가, 수정, 삭제할 수 있습니다.'}
                  {item.id === 'topics' && '주제를 관리하고 분류할 수 있습니다.'}
                  {item.id === 'stats' && '문항 통계를 확인할 수 있습니다.'}
                  {item.id === 'settings' && '시스템 설정을 변경할 수 있습니다.'}
                </p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
