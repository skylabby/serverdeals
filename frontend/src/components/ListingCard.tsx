import { Link } from 'react-router-dom';
import type { Deal } from '../types';
import { DealBadge } from './DealBadge';

function ScoreBadge({ score }: { score: number | null }) {
  if (score == null) return null;

  // Score represents % below market
  const colorClass =
    score >= 40
      ? 'text-emerald-400'
      : score >= 20
        ? 'text-amber-400'
        : 'text-gray-400';

  return (
    <span className={`text-sm font-semibold ${colorClass}`}>
      {score.toFixed(1)}% below
    </span>
  );
}

function ConditionBadge({
  condition,
}: {
  condition: string | null;
}) {
  if (!condition) return null;

  const colorClass = (() => {
    const c = condition.toLowerCase();
    if (c.includes('new')) return 'bg-emerald-900/50 text-emerald-300';
    if (c.includes('refurbished'))
      return 'bg-amber-900/50 text-amber-300';
    return 'bg-gray-700/50 text-gray-300';
  })();

  return (
    <span
      className={`rounded px-2 py-0.5 text-xs font-medium ${colorClass}`}
    >
      {condition}
    </span>
  );
}

function PriceRangeBar({
  priceRange,
  price,
}: {
  priceRange: string | null;
  price: number | null;
}) {
  if (!priceRange || price == null) return null;

  // Parse "min - max" format and compute current position
  const parts = priceRange.split('-').map((s) =>
    parseFloat(s.trim().replace(/[$,]/g, '')),
  );
  if (parts.length < 2 || isNaN(parts[0]) || isNaN(parts[1]))
    return null;

  const [min, max] = parts;
  const range = max - min || 1;
  const pct = Math.max(0, Math.min(100, ((price - min) / range) * 100));

  return (
    <div className="mt-2">
      <div className="flex justify-between text-xs text-gray-500 mb-0.5">
        <span>${min.toLocaleString()}</span>
        <span>${max.toLocaleString()}</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-slate-700">
        <div
          className="h-1.5 rounded-full bg-blue-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="text-center text-xs text-blue-400 mt-0.5">
        Current: ${price.toLocaleString('en-US', {
          minimumFractionDigits: 2,
        })}
      </div>
    </div>
  );
}

export function ListingCard({ deal }: { deal: Deal }) {
  const priceDisplay =
    deal.price != null
      ? `$${deal.price.toLocaleString('en-US', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}`
      : 'Price N/A';

  return (
    <div className="group flex flex-col rounded-xl border border-slate-700/50 bg-slate-800/50 p-4 shadow-sm transition-all hover:border-slate-600 hover:shadow-lg hover:bg-slate-800">
      {/* Image */}
      <div className="mb-3 aspect-video w-full overflow-hidden rounded-lg bg-slate-700/50">
        {deal.image_url ? (
          <img
            src={deal.image_url}
            alt={deal.title}
            className="h-full w-full object-contain"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-slate-500">
            <svg
              className="h-10 w-10"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.41a2.25 2.25 0 013.182 0l2.909 2.91m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
              />
            </svg>
          </div>
        )}
      </div>

      {/* Badges row */}
      <div className="mb-2 flex items-start justify-between gap-2">
        <DealBadge classification={deal.classification} />
        <ScoreBadge score={deal.score} />
      </div>

      {/* Title */}
      <h3 className="mb-2 line-clamp-2 text-sm font-medium text-slate-200 group-hover:text-blue-400">
        {deal.title}
      </h3>

      {/* Price + Condition */}
      <div className="mb-2 flex items-center justify-between">
        <span className="text-lg font-bold text-slate-100">
          {priceDisplay}
        </span>
        <ConditionBadge condition={deal.condition} />
      </div>

      {/* Price range bar */}
      <PriceRangeBar
        priceRange={deal.price_range}
        price={deal.price}
      />

      {/* Category */}
      {deal.category_display && (
        <p className="mt-1 text-xs text-slate-500">
          {deal.category_display}
        </p>
      )}

      {/* Actions */}
      <div className="mt-auto flex items-center justify-between gap-3 pt-3">
        <a
          href={
            deal.view_url ??
            `https://www.ebay.com/itm/${deal.ebay_item_id}`
          }
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-blue-500"
        >
          View on eBay
        </a>
        <Link
          to={`/model/${deal.category_key}`}
          className="text-xs font-medium text-blue-400 transition-colors hover:text-blue-300"
        >
          View trend →
        </Link>
      </div>
    </div>
  );
}
