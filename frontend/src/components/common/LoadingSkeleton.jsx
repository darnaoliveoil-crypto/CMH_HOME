export function KpiSkeletonRow({ count = 8 }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="glass-card p-4 space-y-3">
          <div className="skeleton h-8 w-8 rounded-lg" />
          <div className="skeleton h-3 w-20" />
          <div className="skeleton h-7 w-16" />
        </div>
      ))}
    </div>
  );
}

export function ChartSkeleton({ className = 'h-[280px]' }) {
  return (
    <div className={`glass-card p-5 ${className}`}>
      <div className="skeleton h-4 w-32 mb-4" />
      <div className="skeleton h-full min-h-[200px] rounded-lg" />
    </div>
  );
}

export function TableSkeleton() {
  return (
    <div className="glass-card p-5 space-y-3">
      <div className="skeleton h-4 w-40" />
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="skeleton h-10 w-full rounded-lg" />
      ))}
    </div>
  );
}
