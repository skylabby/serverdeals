import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Dot,
} from 'recharts';
import type { PricePoint } from '../types';

interface PriceChartProps {
  data: PricePoint[];
}

export function PriceChart({ data }: PriceChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-slate-700/50 bg-slate-800/50 text-slate-500">
        No price history available yet.
      </div>
    );
  }

  const chartData = data.map((p) => ({
    date: new Date(p.captured_at).toLocaleDateString(
      'en-US',
      { month: 'short', day: 'numeric' },
    ),
    price: p.price,
  }));

  // Compute median and current price
  const prices = data.map((p) => p.price);
  const sorted = [...prices].sort((a, b) => a - b);
  const median =
    sorted.length % 2 === 0
      ? (sorted[sorted.length / 2 - 1] +
          sorted[sorted.length / 2]) /
        2
      : sorted[Math.floor(sorted.length / 2)];

  const current = prices[prices.length - 1];

  // Find the index for the current price marker
  const lastEntry = chartData[chartData.length - 1];

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
      <h3 className="mb-4 text-sm font-semibold text-slate-300">
        60-Day Price History
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#334155"
          />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: '#94a3b8' }}
            tickLine={false}
            axisLine={{ stroke: '#334155' }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: '#94a3b8' }}
            tickLine={false}
            axisLine={{ stroke: '#334155' }}
            tickFormatter={(v: number) => `$${v}`}
            domain={['auto', 'auto']}
          />
          <Tooltip
            formatter={(value: number) => [
              `$${value.toFixed(2)}`,
              'Price',
            ]}
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #475569',
              borderRadius: '8px',
              color: '#e2e8f0',
            }}
            labelStyle={{ color: '#94a3b8' }}
          />

          {/* Median reference line */}
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

          {/* Price line */}
          <Line
            type="monotone"
            dataKey="price"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5, fill: '#3b82f6' }}
          />

          {/* Current price marker on last point */}
          <Line
            type="monotone"
            dataKey="price"
            stroke="transparent"
            dot={({ cx, cy, index }) => {
              if (index === chartData.length - 1) {
                return (
                  <Dot
                    key={`current-${index}`}
                    cx={cx}
                    cy={cy}
                    r={5}
                    fill="#22c55e"
                    stroke="#1e293b"
                    strokeWidth={2}
                  />
                );
              }
              return <></>;
            }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="mt-3 flex items-center justify-center gap-6 text-xs text-slate-400">
        <div className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-green-500" />
          Current: ${current.toFixed(2)}
        </div>
        <div className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-4 bg-amber-500" />
          Median: ${median.toFixed(2)}
        </div>
      </div>
    </div>
  );
}
