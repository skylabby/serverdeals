import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../lib/api';
import type { Deal, Category } from '../types';
import { ListingCard } from '../components/ListingCard';
import { CategorySidebar } from '../components/CategorySidebar';
import { CategoryChips } from '../components/CategoryChips';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

const SORT_OPTIONS = [
  { value: 'score', label: 'Best Score', defaultDir: 'desc' },
  { value: 'price', label: 'Price: Low → High', dir: 'asc' },
  { value: '-price', label: 'Price: High → Low', dir: null },
  { value: 'date', label: 'Newest', dir: 'desc' },
] as const;

export default function Deals() {
  const [searchParams, setSearchParams] = useSearchParams();

  const page = parseInt(searchParams.get('page') || '1', 10);
  const selectedCategory = searchParams.get('category') || null;
  const currentSort = searchParams.get('sort') || 'score';

  const [deals, setDeals] = useState<Deal[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [totalPages, setTotalPages] = useState(0);
  const [totalItems, setTotalItems] = useState(0);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDeals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const sortParam = currentSort.startsWith('-') ? currentSort.slice(1) : currentSort;
      const [dealsRes, catsRes] = await Promise.all([
        api.getDeals({
          page,
          per_page: 24,
          category: selectedCategory ?? undefined,
          sort: sortParam,
        }),
        api.getCategories(),
      ]);

      // Client-side reverse sort for high-to-low price
      let items = dealsRes.items;
      if (currentSort === '-price') {
        items = [...items].sort((a, b) => (b.price ?? 0) - (a.price ?? 0));
      }

      setDeals(items);
      setTotalPages(dealsRes.total_pages);
      setTotalItems(dealsRes.total_items);
      setCategories(catsRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load deals');
    } finally {
      setLoading(false);
    }
  }, [page, selectedCategory, currentSort]);

  useEffect(() => {
    fetchDeals();
  }, [fetchDeals]);

  const updateParams = (updates: Record<string, string | null>) => {
    const next = new URLSearchParams(searchParams);
    for (const [key, val] of Object.entries(updates)) {
      if (val === null || val === '') {
        next.delete(key);
      } else {
        next.set(key, val);
      }
    }
    if (!updates.page) {
      next.set('page', '1');
    }
    setSearchParams(next);
  };

  const handleCategorySelect = (key: string | null) => {
    updateParams({ category: key });
  };

  const handleSortChange = (sort: string) => {
    const next = new URLSearchParams(searchParams);
    next.set('sort', sort);
    next.set('page', '1');
    setSearchParams(next);
  };

  const handlePageChange = (newPage: number) => {
    const next = new URLSearchParams(searchParams);
    next.set('page', String(newPage));
    setSearchParams(next);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">
          {selectedCategory
            ? categories.find((c) => c.key === selectedCategory)?.display_name ?? 'Deals'
            : 'All Deals'}
          <span className="ml-2 text-base font-normal text-gray-400">
            ({totalItems.toLocaleString()} listings)
          </span>
        </h1>

        {/* Sort Controls */}
        <div className="flex flex-wrap gap-2">
          {SORT_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleSortChange(opt.value)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                currentSort === opt.value
                  ? 'bg-brand-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-6">
        <CategorySidebar
          categories={categories}
          selectedKey={selectedCategory}
          onSelect={handleCategorySelect}
        />

        <div className="flex-1">
          {/* Quick filter chips */}
          <CategoryChips
            categories={categories}
            selectedKey={selectedCategory}
            onSelect={handleCategorySelect}
          />

          {loading ? (
            <LoadingSpinner />
          ) : error ? (
            <ErrorState message={error} onRetry={fetchDeals} />
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
                    onClick={() => handlePageChange(page - 1)}
                    disabled={page <= 1}
                    className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    ← Prev
                  </button>
                  <span className="px-4 py-2 text-sm text-gray-500">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    onClick={() => handlePageChange(page + 1)}
                    disabled={page >= totalPages}
                    className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Next →
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
