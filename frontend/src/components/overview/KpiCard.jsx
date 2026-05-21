import { TrendingDown, TrendingUp } from 'lucide-react';
import { formatNumber, formatPercent } from '../../utils/formatters';

const accentMap = {
  default: 'text-[#00c9b1] bg-[#00c9b1]/15 border-[#00c9b1]/25',
  safe: 'text-[#00c9b1] bg-[#00c9b1]/15 border-[#00c9b1]/25',
  risk: 'text-amber-400 bg-amber-500/15 border-amber-500/30',
  dangerous: 'text-red-400 bg-red-500/15 border-red-500/30',
  blocked: 'text-red-300 bg-red-900/30 border-red-900/40',
};

export default function KpiCard({ icon: Icon, label, value, trend, format = 'number', variant = 'default', vsLabel }) {
  const display =
    format === 'percent'
      ? formatPercent(value, 1)
      : formatNumber(value, format === 'decimal' ? 1 : 0);

  const trendPositive = trend?.positive;
  const TrendIcon = trendPositive ? TrendingUp : TrendingDown;

  return (
    <div className="group glass-card p-4 hover:border-[var(--dash-border-hover)] hover:shadow-[0_0_20px_var(--dash-accent-glow)] transition-all duration-200">
      <div className={`inline-flex p-2 rounded-lg border mb-3 ${accentMap[variant]}`}>
        <Icon className="w-4 h-4" />
      </div>
      <p className="text-xs text-dash-faint font-medium mb-1">{label}</p>
      <p className="text-2xl font-bold text-dash tracking-tight">{display}</p>
      {trend != null && (
        <div className={`flex items-center gap-1 mt-2 text-xs font-medium ${trendPositive ? 'text-[#00c9b1]' : 'text-red-500'}`}>
          <TrendIcon className="w-3 h-3" />
          <span>{trend.text}</span>
          <span className="text-dash-faint ml-0.5">{vsLabel ?? 'vs last period'}</span>
        </div>
      )}
    </div>
  );
}
