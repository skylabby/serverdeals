import { useState, useEffect, useCallback } from 'react';
import { Routes, Route, useSearchParams } from 'react-router-dom';
import type { Deal, Category, Stats } from './types';
import { api } from './lib/api';
import { ListingCard } from './components/ListingCard';
import { CategorySidebar } from './components/CategorySidebar';
import { DealBadge } from './components/DealBadge';
import { EmptyState } from './components/EmptyState';
import { ErrorState } from './components/ErrorState';
import { LoadingSpinner } from './components/LoadingSpinner';
import ModelPage from './pages/ModelPage';

/* ── Home page ─────────────────────────────────────────── */

function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [deals, setDeals] = useState<Deal[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);

  const selectedCategory = searchParams.get('category') ?? null;
  const classification = searchParams.get('class') ?? undefined;

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [dealsRes, cats, statsRes] = await Promise.all([
        api.getDeals({
          page,
          per_page: 24,
          category: selectedCategory ?? undefined,
          classification,
        }),
        api.getCategories(),
        api.getStats(),
      ]);
      setDeals(dealsRes.items);
      setTotalPages(dealsRes.total_pages);
      setCategories(cats);
      setStats(statsRes);
    } catch {
      setError('Failed to load deals. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [page, selectedCategory, classification]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  function handleCategorySelect(key: string | null) {
    setPage(1);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (key) {
        next.set('category', key);
      } else {
        next.delete('category');
      }
      return next;
    });
  }

  return (
    <div className="flex gap-6">
      {/* Sidebar */}
      <CategorySidebar
        categories={categories}
        selectedKey={selectedCategory}
        onSelect={handleCategorySelect}
      />

      {/* Main content */}
      <div className="flex-1 min-w-0">
        {/* Stats bar */}
        {stats && (
          <div className="mb-6 flex flex-wrap gap-4 rounded-xl border border-slate-700/50 bg-slate-800/50 px-5 py-3">
            <StatPill
              label="Total Listings"
              value={stats.total_listings.toLocaleString()}
            />
            <StatPill
              label="Categories"
              value={stats.total_categories.toLocaleString()}
            />
            <StatPill
              label="Hot Deals"
              value={stats.hot_deals_count.toLocaleString()}
              className="text-red-400"
            />
            <StatPill
              label="Good Deals"
              value={stats.good_deals_count.toLocaleString()}
              className="text-amber-400"
            />
            {stats.last_updated && (
              <StatPill
                label="Updated"
                value={new Date(
                  stats.last_updated,
                ).toLocaleDateString()}
              />
            )}
          </div>
        )}

        {/* Filters row */}
        <div className="mb-4 flex flex-wrap items-center gap-2">
          {(['hot', 'good', 'fair'] as const).map((cls) => (
            <button
              key={cls}
              onClick={() => {
                setPage(1);
                setSearchParams((prev) => {
                  const next = new URLSearchParams(prev);
                  if (classification === cls) {
                    next.delete('class');
                  } else {
                    next.set('class', cls);
                  }
                  return next;
                });
              }}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                classification === cls
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              <DealBadge classification={cls} />
            </button>
          ))}
          {classification && (
            <button
              onClick={() => {
                setPage(1);
                setSearchParams((prev) => {
                  const next = new URLSearchParams(prev);
                  next.delete('class');
                  return next;
                });
              }}
              className="text-xs text-slate-500 hover:text-slate-300"
            >
              Clear filter
            </button>
          )}
        </div>

        {/* Content */}
        {error ? (
          <ErrorState
            message={error}
            onRetry={fetchData}
          />
        ) : loading ? (
          <LoadingSpinner />
        ) : deals.length === 0 ? (
          <EmptyState
            title="No deals found"
            message="Try adjusting your filters or check back later."
            icon="search"
          />
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {deals.map((deal) => (
                <ListingCard key={deal.id} deal={deal} />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-8 flex items-center justify-center gap-2">
                <button
                  onClick={() =>
                    setPage((p) => Math.max(1, p - 1))
                  }
                  disabled={page <= 1}
                  className="rounded-lg bg-slate-800 px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-slate-700 disabled:opacity-40"
                >
                  Previous
                </button>
                <span className="text-sm text-slate-400">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() =>
                    setPage((p) =>
                      Math.min(totalPages, p + 1),
                    )
                  }
                  disabled={page >= totalPages}
                  className="rounded-lg bg-slate-800 px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-slate-700 disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function StatPill({
  label,
  value,
  className = '',
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div className="flex items-center gap-1.5 text-sm">
      <span className="text-slate-500">{label}:</span>
      <span className={`font-semibold ${className || 'text-slate-200'}`}>
        {value}
      </span>
    </div>
  );
}

/* ── App shell ──────────────────────────────────────────── */

function App() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-200">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-800/30 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <a
            href="/"
            className="text-xl font-bold tracking-tight text-slate-100"
          >
            <span className="text-blue-400">Server</span>Deals
          </a>
          <span className="text-xs text-slate-500">
            US eBay Deals for Homelab Gear
          </span>
        </div>
      </header>

      {/* Main */}
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route
            path="/model/:categoryKey"
            element={<ModelPage />}
          />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-700/50 py-6 text-center text-xs text-slate-600">
        ServerDeals — Deals data sourced from eBay. Not affiliated
        with eBay.
      </footer>
    </div>
  );
}

export default App;
