export default function ChartCard({ title, subtitle, children, className = '' }) {
  return (
    <div
      className={`glass-card p-5 hover:border-[var(--dash-border-hover)] transition-colors ${className}`}
    >
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-dash">{title}</h3>
        {subtitle && <p className="text-xs text-dash-faint mt-0.5">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}
