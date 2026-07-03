import { Link } from 'react-router-dom';
import type { Deal } from '../types';
import { DealBadge } from './DealBadge';

function ScoreBadge({ score }: { score: number | null }) {
  if (score == null) return null;

  const colorClass =
    score >= 40
      ? 'bg-green-900/30 text-green-400 border-green-800'
      : score >= 20
        ? 'bg-yellow-900/30 text-yellow-400 border-yellow-800'
        : 'bg-slate-800/50 text-slate-400 border-slate-700';

  return (
    <span className={`rounded-md border px-2 py-1 text-xs font-bold ${colorClass}`}>
      -{score.toFixed(0)}%
    </span>
  );
}

function ConditionBadge({ condition }: { condition: string | null }) {
  if (!condition) return null;

  const lower = condition.toLowerCase();
  const colorClass = lower.includes('new')
    ? 'bg-green-900/30 text-green-400 border-green-800'
    : lower.includes('refurbished')
      ? 'bg-yellow-900/30 text-yellow-400 border-yellow-800'
      : 'bg-slate-800/50 text-slate-400 border-slate-700';

  return (
    <span className={`rounded-md border px-2 py-1 text-xs font-medium ${colorClass}`}>
      {condition}
    </span>
  );
}

function ListingTypeBadge({ type }: { type: string | null }) {
  if (!type) return null;
  const isFixed = type.toLowerCase().includes('fixed');
  return (
    <span className={`rounded-md border px-2 py-1 text-xs font-medium ${
      isFixed
        ? 'bg-brand-900/20 text-brand-400 border-brand-800'
        : 'bg-purple-900/30 text-purple-300 border-purple-700'
    }`}>
      {isFixed ? 'Buy It Now' : 'Auction'}
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

  const parts = priceRange.split('-').map((s) =>
    parseFloat(s.trim().replace(/[$,]/g, '')),
  );
  if (parts.length < 2 || isNaN(parts[0]) || isNaN(parts[1]))
    return null;

  const [min, max] = parts;
  const range = max - min || 1;
  const pct = Math.max(0, Math.min(100, ((price - min) / range) * 100));

  return (
    <div className="mt-3">
      <div className="flex justify-between text-[10px] text-slate-500 mb-1">
        <span>Low ${min.toLocaleString()}</span>
        <span>High ${max.toLocaleString()}</span>
      </div>
      <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-brand-500 via-yellow-500 to-rose-500 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="mt-1 text-center text-[11px] font-semibold text-brand-400">
        ${price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
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
    <div className="group flex flex-col rounded-xl border border-border bg-surface-raised p-4 shadow-sm transition-all duration-200 hover:border-brand-500/30 hover:shadow-lg hover:shadow-brand-500/5 hover:bg-surface-overlay hover:-translate-y-0.5">
      {/* Image */}
      <div className="mb-3 aspect-video w-full overflow-hidden rounded-lg bg-slate-800/50">
        {deal.image_url ? (
          <img
            src={deal.image_url}
            alt={deal.title}
            className="h-full w-full object-contain transition-transform duration-300 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-slate-600">
            <svg className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.41a2.25 2.25 0 013.182 0l2.909 2.91m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
            </svg>
          </div>
        )}
      </div>

      {/* Badges row */}
      <div className="mb-2 flex flex-wrap items-center gap-1.5">
        <DealBadge classification={deal.classification} />
        <ScoreBadge score={deal.score} />
      </div>

      {/* Title */}
      <h3 className="mb-2 line-clamp-2 text-sm font-medium text-slate-200 group-hover:text-brand-400 transition-colors">
        {deal.title}
      </h3>

      {/* Price */}
      <div className="mb-2">
        <span className="text-xl font-bold text-white tracking-tight">
          {priceDisplay}
        </span>
      </div>

      {/* Metadata badges */}
      <div className="mb-2 flex flex-wrap items-center gap-1.5">
        <ConditionBadge condition={deal.condition} />
        <ListingTypeBadge type={deal.listing_type} />
      </div>

      {/* Price range bar */}
      <PriceRangeBar priceRange={deal.price_range} price={deal.price} />

      {/* Footer actions */}
      <div className="mt-3 flex items-center justify-between gap-3 pt-3 border-t border-border-subtle">
        <a
          href={deal.view_url ?? `https://www.ebay.com/itm/${deal.ebay_item_id}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-3.5 py-2 text-xs font-semibold text-white transition-all hover:bg-brand-500 hover:shadow-md hover:shadow-brand-500/25"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
          View Deal
        </a>
        <Link
          to={`/model/${deal.category_key}`}
          className="text-xs font-medium text-slate-500 transition-colors hover:text-brand-400"
        >
          Price history →
        </Link>
      </div>
    </div>
  );
}
