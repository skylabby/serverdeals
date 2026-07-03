import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { PricePoint } from '../types';

interface PriceChartProps {
  data: PricePoint[];
}

export function PriceChart({ data }: PriceChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-slate-700/50 bg-slate-800/40 text-slate-500">
        No price history available yet.
      </div>
    );
  }

  const chartData = data.map((p) => ({
    date: new Date(p.captured_at).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
    price: p.price,
  }));

  const prices = data.map((p) => p.price);
  const sorted = [...prices].sort((a, b) => a - b);
  const median =
    sorted.length % 2 === 0
      ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
      : sorted[Math.floor(sorted.length / 2)];

  const current = prices[prices.length - 1];
  const min = sorted[0];
  const max = sorted[sorted.length - 1];
  const pctBelow = median > 0 ? ((median - current) / median) * 100 : 0;

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-5">
      {/* Metric cards row */}
      <div className="mb-5 grid grid-cols-4 gap-3">
        <div className="rounded-lg bg-slate-900/50 p-3 text-center">
          <div className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
            Current
          </div>
          <div className="mt-1 text-lg font-bold text-green-400">
            ${current.toFixed(0)}
          </div>
        </div>
        <div className="rounded-lg bg-slate-900/50 p-3 text-center">
          <div className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
            Median
          </div>
          <div className="mt-1 text-lg font-bold text-amber-400">
            ${median.toFixed(0)}
          </div>
        </div>
        <div className="rounded-lg bg-slate-900/50 p-3 text-center">
          <div className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
            Low
          </div>
          <div className="mt-1 text-lg font-bold text-slate-300">
            ${min.toFixed(0)}
          </div>
        </div>
        <div className="rounded-lg bg-slate-900/50 p-3 text-center">
          <div className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
            vs Median
          </div>
          <div className={`mt-1 text-lg font-bold ${pctBelow >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {pctBelow >= 0 ? '-' : '+'}{Math.abs(pctBelow).toFixed(0)}%
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.25} />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: '#64748b' }}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 11, fill: '#64748b' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => `$${v}`}
            domain={['auto', 'auto']}
            width={60}
          />
          <Tooltip
            formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
            contentStyle={{
              backgroundColor: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '10px',
              color: '#e2e8f0',
              fontSize: '13px',
            }}
            labelStyle={{ color: '#94a3b8', marginBottom: '4px' }}
          />
          <ReferenceLine
            y={median}
            stroke="#f59e0b"
            strokeDasharray="6 4"
            strokeWidth={1.5}
            label={{
              value: `Median $${median.toFixed(0)}`,
              position: 'insideTopRight',
              fill: '#f59e0b',
              fontSize: 11,
            }}
          />
          <Area
            type="monotone"
            dataKey="price"
            stroke="#3b82f6"
            strokeWidth={2.5}
            fill="url(#priceGradient)"
            dot={false}
            activeDot={{ r: 5, fill: '#3b82f6', stroke: '#0f172a', strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
