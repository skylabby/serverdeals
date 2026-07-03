import { useState } from 'react';
import type { Category } from '../types';

interface CategorySidebarProps {
  categories: Category[];
  selectedKey: string | null;
  onSelect: (key: string | null) => void;
}

const GROUP_ORDER = [
  'server',
  'cpu',
  'ram',
  'storage',
  'mainboard',
  'gpu',
  'network',
  'systems',
  'build',
];

export function CategorySidebar({
  categories,
  selectedKey,
  onSelect,
}: CategorySidebarProps) {
  const [collapsed, setCollapsed] = useState<Set<string>>(
    new Set(),
  );

  const groups = new Map<string, Category[]>();
  for (const c of categories) {
    const existing = groups.get(c.group_key);
    if (existing) {
      existing.push(c);
    } else {
      groups.set(c.group_key, [c]);
    }
  }

  const orderedKeys = GROUP_ORDER.filter((k) =>
    groups.has(k),
  );

  function toggleGroup(key: string) {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  return (
    <aside className="w-64 shrink-0 rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
      <h2 className="mb-3 text-sm font-semibold text-slate-200">
        Categories
      </h2>

      <button
        onClick={() => onSelect(null)}
        className={`mb-3 block w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
          selectedKey === null
            ? 'bg-blue-900/40 text-blue-300 font-medium'
            : 'text-slate-400 hover:bg-slate-700/50 hover:text-slate-200'
        }`}
      >
        All Deals
      </button>

      {orderedKeys.map((group) => {
        const cats = groups.get(group)!;
        const isCollapsed = collapsed.has(group);

        return (
          <div key={group} className="mb-3">
            <button
              onClick={() => toggleGroup(group)}
              className="flex w-full items-center justify-between px-3 py-1 text-xs font-semibold uppercase tracking-wider text-slate-500 transition-colors hover:text-slate-300"
            >
              <span>{group}</span>
              <span className="text-[10px]">
                {isCollapsed ? '▶' : '▼'}
              </span>
            </button>

            {!isCollapsed &&
              cats.map((cat) => (
                <button
                  key={cat.key}
                  onClick={() => onSelect(cat.key)}
                  className={`flex w-full items-center justify-between rounded-lg px-3 py-1.5 text-sm transition-colors ${
                    selectedKey === cat.key
                      ? 'bg-blue-900/40 text-blue-300 font-medium'
                      : 'text-slate-400 hover:bg-slate-700/50 hover:text-slate-200'
                  }`}
                >
                  <span className="truncate">
                    {cat.display_name}
                  </span>
                  <span className="ml-2 text-xs text-slate-600">
                    {cat.listing_count}
                  </span>
                </button>
              ))}
          </div>
        );
      })}
    </aside>
  );
}
