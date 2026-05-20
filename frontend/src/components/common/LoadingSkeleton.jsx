export function SkeletonBox({ className = '' }) {
  return <div className={`skeleton ${className}`} />;
}

export function KpiSkeletonRow() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="rounded-xl border border-dash bg-dash-card p-4 space-y-3">
          <SkeletonBox className="h-8 w-8 rounded-lg" />
          <SkeletonBox className="h-3 w-20" />
          <SkeletonBox className="h-7 w-16" />
          <SkeletonBox className="h-3 w-12" />
        </div>
      ))}
    </div>
  );
}

export function ChartSkeleton({ height = 'h-64' }) {
  return (
    <div className={`rounded-xl border border-dash bg-dash-card p-5 ${height}`}>
      <SkeletonBox className="h-5 w-40 mb-4" />
      <SkeletonBox className="h-full min-h-[200px] w-full" />
    </div>
  );
}

export function TableSkeleton({ rows = 6 }) {
  return (
    <div className="rounded-xl border border-dash bg-dash-card p-5 space-y-3">
      <SkeletonBox className="h-5 w-48" />
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonBox key={i} className="h-10 w-full" />
      ))}
    </div>
  );
}
