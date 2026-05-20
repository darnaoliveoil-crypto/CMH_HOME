import { TrendingDown, TrendingUp } from 'lucide-react';
import { formatNumber, formatPercent } from '../../utils/formatters';

const accentMap = {
  default: 'text-blue-400 bg-blue-600/15 border-blue-500/20',
  safe: 'text-green-400 bg-green-500/15 border-green-500/20',
  risk: 'text-amber-400 bg-amber-500/15 border-amber-500/20',
  dangerous: 'text-red-400 bg-red-500/15 border-red-500/20',
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
    <div className="group rounded-xl border border-dash bg-dash-card p-4 hover:border-blue-500/40 hover:shadow-lg hover:shadow-blue-500/5 transition-all duration-200">
      <div className={`inline-flex p-2 rounded-lg border mb-3 ${accentMap[variant]}`}>
        <Icon className="w-4 h-4" />
      </div>
      <p className="text-xs text-dash-faint font-medium mb-1">{label}</p>
      <p className="text-2xl font-bold text-dash tracking-tight">{display}</p>
      {trend != null && (
        <div className={`flex items-center gap-1 mt-2 text-xs font-medium ${trendPositive ? 'text-green-500' : 'text-red-500'}`}>
          <TrendIcon className="w-3 h-3" />
          <span>{trend.text}</span>
          <span className="text-dash-faint ml-0.5">{vsLabel ?? 'vs last period'}</span>
        </div>
      )}
    </div>
  );
}
