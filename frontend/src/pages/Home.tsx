import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import type { Stats, Deal, Category } from '../types';
import { ListingCard } from '../components/ListingCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorState } from '../components/ErrorState';

export default function Home() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [topDeal, setTopDeal] = useState<Deal | null>(null);
  const [hotDeals, setHotDeals] = useState<Deal[]>([]);
  const [latestDeals, setLatestDeals] = useState<Deal[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, h, l, c] = await Promise.all([
        api.getStats(),
        api.getHotDeals(20),
        api.getDeals({ sort: 'date', per_page: 12 }),
        api.getCategories(),
      ]);
      setStats(s);
      setTopDeal(h[0] ?? null);
      setHotDeals(h.slice(0, 8));
      setLatestDeals(l.items);
      setCategories(c);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorState message={error} onRetry={fetchAll} />;

  const top9Categories = categories.slice(0, 9);

  return (
    <div className="space-y-12">
      {/* Hero Stats */}
      <section className="rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 p-8 text-white md:p-12">
        <h1 className="mb-3 text-3xl font-bold md:text-4xl">
          Find the Best Server Deals on eBay
        </h1>
        <p className="mb-8 text-lg text-brand-100">
          Scored, categorized, and price-tracked. Stop overpaying for used enterprise hardware.
        </p>
        <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
          <StatBox label="Total Listings" value={stats?.total_listings ?? 0} />
          <StatBox label="Hot Deals" value={stats?.hot_deals_count ?? 0} />
          <StatBox label="Categories" value={stats?.total_categories ?? 0} />
          <StatBox label="Good Deals" value={stats?.good_deals_count ?? 0} />
        </div>
      </section>

      {/* Top Deal */}
      {topDeal && (
        <section>
          <h2 className="mb-4 text-xl font-bold text-gray-900">🔥 Featured Deal</h2>
          <div className="rounded-2xl border-2 border-brand-200 bg-gradient-to-r from-brand-50 to-white p-1">
            <div className="flex flex-col gap-4 md:flex-row">
              <div className="md:w-1/2">
                {topDeal.image_url ? (
                  <img src={topDeal.image_url} alt={topDeal.title} className="h-64 w-full rounded-xl object-contain" />
                ) : (
                  <div className="flex h-64 w-full items-center justify-center rounded-xl bg-gray-100 text-gray-400">
                    No image
                  </div>
                )}
              </div>
              <div className="flex flex-col justify-center md:w-1/2">
                <span className="mb-1 text-sm font-semibold text-brand-600">{topDeal.category_display}</span>
                <h3 className="mb-2 text-xl font-bold text-gray-900">{topDeal.title}</h3>
                <p className="mb-4 text-3xl font-bold text-gray-900">
                  ${topDeal.price?.toLocaleString('en-US', { minimumFractionDigits: 2 }) ?? 'N/A'}
                </p>
                <div className="flex gap-3">
                  <a
                    href={topDeal.view_url ?? `https://www.ebay.com/itm/${topDeal.ebay_item_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rounded-lg bg-brand-600 px-6 py-2.5 text-white hover:bg-brand-700 transition-colors"
                  >
                    View on eBay
                  </a>
                  <Link
                    to={`/model/${topDeal.category_key}`}
                    className="rounded-lg border border-brand-300 px-6 py-2.5 text-brand-700 hover:bg-brand-50 transition-colors"
                  >
                    See All in Category
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Category Quick Links */}
      <section>
        <h2 className="mb-4 text-xl font-bold text-gray-900">Browse by Category</h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
          {top9Categories.map((cat) => (
            <Link
              key={cat.key}
              to={`/model/${cat.key}`}
              className="flex flex-col items-center rounded-xl border border-gray-200 bg-white p-4 text-center transition-all hover:shadow-md hover:border-brand-300"
            >
              <span className="mb-2 text-2xl">{getCategoryIcon(cat.key)}</span>
              <span className="text-sm font-medium text-gray-900">{cat.display_name}</span>
              <span className="text-xs text-gray-400">{cat.listing_count} listings</span>
            </Link>
          ))}
          {categories.length > 9 && (
            <Link
              to="/deals"
              className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 p-4 text-center transition-all hover:bg-white hover:border-brand-300"
            >
              <span className="text-sm font-medium text-brand-600">+{categories.length - 9} more</span>
              <span className="text-xs text-gray-400">View all categories</span>
            </Link>
          )}
        </div>
      </section>

      {/* Hottest Deals Grid */}
      {hotDeals.length > 0 && (
        <section>
          <h2 className="mb-4 text-xl font-bold text-gray-900">🔥 Hottest Deals</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {hotDeals.map((deal) => (
              <ListingCard key={deal.id} deal={deal} />
            ))}
          </div>
        </section>
      )}

      {/* Latest Deals Feed */}
      {latestDeals.length > 0 && (
        <section>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900">Latest Deals</h2>
            <Link to="/deals?sort=date" className="text-sm font-medium text-brand-600 hover:text-brand-700">
              View all →
            </Link>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {latestDeals.map((deal) => (
              <ListingCard key={deal.id} deal={deal} />
            ))}
          </div>
        </section>
      )}

      {/* CTA */}
      <section className="rounded-2xl bg-gray-900 p-8 text-center md:p-12">
        <h2 className="mb-2 text-2xl font-bold text-white">Never Miss a Deal</h2>
        <p className="mb-6 text-gray-400">
          Get alerts for new hot deals via Telegram or Email. (Coming soon)
        </p>
        <div className="flex justify-center gap-4">
          <button disabled className="rounded-lg bg-brand-500/50 px-6 py-2.5 text-sm text-white cursor-not-allowed">
            Telegram Alerts
          </button>
          <button disabled className="rounded-lg bg-gray-700/50 px-6 py-2.5 text-sm text-gray-300 cursor-not-allowed">
            Email Alerts
          </button>
        </div>
      </section>
    </div>
  );
}

function StatBox({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <p className="text-3xl font-bold">{value.toLocaleString()}</p>
      <p className="text-sm text-brand-200">{label}</p>
    </div>
  );
}

function getCategoryIcon(key: string): string {
  const icons: Record<string, string> = {
    'dell-poweredge': '🖥️',
    'hpe-proliant': '🖥️',
    'lenovo-thinksystem': '🖥️',
    'supermicro': '🖥️',
    'cisco-ucs': '🔌',
    'intel-xeon': '⚡',
    'amd-epyc': '⚡',
    'samsung-ssd': '💾',
    'wd-hdd': '💾',
    'seagate-hdd': '💾',
    'nvidia-gpu': '🎮',
    'memory-ram': '🧠',
    'network-switch': '🌐',
  };
  return icons[key] ?? '📦';
}
