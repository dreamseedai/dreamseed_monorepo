import { QuestionFilter } from '../lib/questions';

interface SearchBarProps {
  value: QuestionFilter;
  onChange: (filter: QuestionFilter) => void;
  searching?: boolean;
  onSubmit?: () => void;
}

export function SearchBar({ value, onChange, searching, onSubmit }: SearchBarProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit?.();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3 mb-4">
      <div className="flex gap-2 flex-wrap">
        <input
          type="text"
          placeholder="검색어..."
          value={value.q || ''}
          onChange={(e) => onChange({ ...value, q: e.target.value, page: 1 })}
          className="border border-gray-300 dark:border-gray-600 rounded px-3 py-1.5 text-sm flex-1 min-w-[200px] bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:border-blue-500 dark:focus:border-blue-400 focus:outline-none"
        />
        <input
          type="text"
          placeholder="분류 (topic)..."
          value={value.topic || ''}
          onChange={(e) => onChange({ ...value, topic: e.target.value, page: 1 })}
          className="border border-gray-300 dark:border-gray-600 rounded px-3 py-1.5 text-sm w-40 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:border-blue-500 dark:focus:border-blue-400 focus:outline-none"
        />
        <select
          value={value.difficulty || ''}
          onChange={(e) =>
            onChange({
              ...value,
              difficulty: e.target.value as QuestionFilter['difficulty'],
              page: 1,
            })
          }
          className="border border-gray-300 dark:border-gray-600 rounded px-3 py-1.5 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:border-blue-500 dark:focus:border-blue-400 focus:outline-none"
        >
          <option value="">난이도 전체</option>
          <option value="easy">쉬움</option>
          <option value="medium">보통</option>
          <option value="hard">어려움</option>
        </select>
        <select
          value={value.status || ''}
          onChange={(e) =>
            onChange({
              ...value,
              status: e.target.value as QuestionFilter['status'],
              page: 1,
            })
          }
          className="border border-gray-300 dark:border-gray-600 rounded px-3 py-1.5 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:border-blue-500 dark:focus:border-blue-400 focus:outline-none"
        >
          <option value="">상태 전체</option>
          <option value="draft">Draft</option>
          <option value="review">Review</option>
          <option value="published">Published</option>
          <option value="archived">Archived</option>
        </select>
        <button
          type="submit"
          disabled={searching}
          className="rounded bg-blue-600 dark:bg-blue-500 px-4 py-1.5 text-white text-sm hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 transition-colors"
        >
          {searching ? '검색 중...' : '검색'}
        </button>
      </div>
    </form>
  );
}
