interface EmptyStateProps {
  title?: string;
  message?: string;
  icon?: 'search' | 'box' | 'tag';
}

export function EmptyState({
  title = 'Nothing here yet',
  message = 'No items to display.',
  icon = 'box',
}: EmptyStateProps) {
  const icons = {
    search: (
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
      />
    ),
    box: (
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m6 4.125l2.25-1.5 2.25 1.5m-9-3.75L12 4.5l6.75 3m-13.5 0L12 10.5l6.75-3m-13.5 0V18a.75.75 0 00.75.75h13.5a.75.75 0 00.75-.75V7.5"
      />
    ),
    tag: (
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z"
      />
    ),
  };

  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <svg
        className="mb-4 h-16 w-16 text-slate-700"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        {icons[icon]}
      </svg>
      <h3 className="mb-1 text-lg font-semibold text-slate-400">
        {title}
      </h3>
      <p className="text-slate-500">{message}</p>
    </div>
  );
}
