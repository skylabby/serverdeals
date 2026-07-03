import type { Category } from '../types';

interface CategoryChipsProps {
  categories: Category[];
  selectedKey: string | null;
  onSelect: (key: string | null) => void;
}

const TOP_CATEGORIES = [
  'sas-drive',
  'ssd-sata',
  'intel-xeon',
  'network-switch',
  'dell-poweredge',
  'ecc-ram',
  'ssd-m2-nvme',
  'gpu',
];

export function CategoryChips({
  categories,
  selectedKey,
  onSelect,
}: CategoryChipsProps) {
  // Filter to top categories, sorted by listing count
  const topCats = TOP_CATEGORIES.map((key) =>
    categories.find((c) => c.key === key),
  ).filter(Boolean) as Category[];

  return (
    <div className="mb-6 flex flex-wrap items-center gap-2">
      <button
        onClick={() => onSelect(null)}
        className={`rounded-full px-4 py-2 text-sm font-medium transition-all ${
          selectedKey === null
            ? 'bg-brand-600 text-white shadow-md shadow-brand-500/25'
            : 'bg-surface-overlay text-slate-300 hover:bg-brand-900/20 hover:text-brand-400 border border-border'
        }`}
      >
        All Deals
      </button>
      {topCats.map((cat) => (
        <button
          key={cat.key}
          onClick={() => onSelect(cat.key)}
          className={`rounded-full px-4 py-2 text-sm font-medium transition-all ${
            selectedKey === cat.key
              ? 'bg-brand-600 text-white shadow-md shadow-brand-600/25'
              : 'bg-slate-800/50 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700/50'
          }`}
        >
          {cat.display_name}
          <span className="ml-1.5 text-xs opacity-60">
            {cat.listing_count}
          </span>
        </button>
      ))}
    </div>
  );
}
