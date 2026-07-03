import { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../lib/api';
import type { Deal, Category } from '../types';
import { ListingCard } from '../components/ListingCard';
import { PriceChart } from '../components/PriceChart';
import { PageSpinner } from '../components/LoadingSpinner';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

export default function ModelPage() {
  const { categoryKey } = useParams<{ categoryKey: string }>();

  const [deals, setDeals] = useState<Deal[]>([]);
  const [category, setCategory] = useState<Category | null>(null);
  const [priceHistory, setPriceHistory] = useState<
    { price: number; captured_at: string }[]
  >([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!categoryKey) return;
    setLoading(true);
    setError(null);
    try {
      const [dealsRes, catsRes] = await Promise.all([
        api.getDeals({
          category: categoryKey,
          per_page: 100,
          sort: 'date',
        }),
        api.getCategories(),
      ]);

      const cat =
        catsRes.find((c) => c.key === categoryKey) ?? null;
      setCategory(cat);
      setDeals(dealsRes.items);

      // Build price history from deal snapshots
      if (dealsRes.items.length > 0) {
        try {
          const detail = await api.getDeal(
            dealsRes.items[0].id,
          );
          if (detail?.price_history) {
            setPriceHistory(detail.price_history);
          } else {
            setPriceHistory([]);
          }
        } catch {
          setPriceHistory([]);
        }
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to load category',
      );
    } finally {
      setLoading(false);
    }
  }, [categoryKey]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) return <PageSpinner />;
  if (error)
    return (
      <ErrorState message={error} onRetry={fetchData} />
    );

  return (
    <div>
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-slate-400">
        <Link
          to="/"
          className="hover:text-blue-400 transition-colors"
        >
          Home
        </Link>
        <span className="mx-2">/</span>
        <Link
          to="/"
          className="hover:text-blue-400 transition-colors"
        >
          Deals
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-600">
          {category?.display_name ?? categoryKey}
        </span>
      </nav>

      {/* Header */}
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold text-slate-100">
          {category?.display_name ?? categoryKey}
        </h1>
        <p className="text-slate-400">
          {deals.length} listings • {category?.group_key ?? ''}
          {category?.median_price != null && (
            <>
              {' '}
              • Median: $
              {category.median_price.toLocaleString(
                'en-US',
                { minimumFractionDigits: 2 },
              )}
            </>
          )}
        </p>
      </div>

      {/* Price Chart */}
      {priceHistory.length > 0 && (
        <div className="mb-8">
          <PriceChart data={priceHistory} />
        </div>
      )}

      {/* Listings */}
      {deals.length === 0 ? (
        <EmptyState
          title="No listings yet"
          message="Check back soon for new deals in this category."
          icon="box"
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {deals.map((deal) => (
            <ListingCard key={deal.id} deal={deal} />
          ))}
        </div>
      )}
    </div>
  );
}
