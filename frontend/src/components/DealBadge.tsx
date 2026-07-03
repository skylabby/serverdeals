interface DealBadgeProps {
  classification: string | null;
}

export function DealBadge({ classification }: DealBadgeProps) {
  if (!classification) return null;

  const config: Record<
    string,
    { label: string; className: string }
  > = {
    hot: {
      label: 'Hot 🔥',
      className:
        'bg-red-900/50 text-red-300 border-red-700/50',
    },
    good: {
      label: 'Good 👍',
      className:
        'bg-amber-900/50 text-amber-300 border-amber-700/50',
    },
    fair: {
      label: 'Fair',
      className:
        'bg-gray-700/50 text-gray-300 border-gray-600/50',
    },
  };

  const { label, className } =
    config[classification] ?? config.fair;

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${className}`}
    >
      {label}
    </span>
  );
}
