import {
  Activity,
  Building2,
  Calendar,
  Gauge,
  Server,
  TrendingDown,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { useLocale } from '../../context/LocaleContext';
import KpiCard from '../overview/KpiCard';
import RiskBadge from '../common/RiskBadge';

function StatusCard({ label, status }) {
  const variant =
    status === 'Safe' ? 'safe' : status === 'Risk' ? 'risk' : status === 'Dangerous' ? 'dangerous' : 'default';

  return (
    <div className="rounded-xl border border-dash bg-dash-card p-4">
      <div className="inline-flex p-2 rounded-lg border mb-3 text-blue-400 bg-blue-600/15 border-blue-500/20">
        <Activity className="w-4 h-4" />
      </div>
      <p className="text-xs text-dash-faint font-medium mb-1">{label}</p>
      <RiskBadge label={status} />
    </div>
  );
}

function TextKpi({ icon: Icon, label, value }) {
  return (
    <div className="rounded-xl border border-dash bg-dash-card p-4">
      <div className="inline-flex p-2 rounded-lg border mb-3 text-blue-400 bg-blue-600/15 border-blue-500/20">
        <Icon className="w-4 h-4" />
      </div>
      <p className="text-xs text-dash-faint font-medium mb-1">{label}</p>
      <p className="text-lg font-bold text-dash truncate">{value ?? '—'}</p>
    </div>
  );
}

export default function LifecycleKpiRow({ kpis, loading }) {
  const { t } = useLocale();

  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="h-28 rounded-xl border border-dash bg-dash-card animate-pulse" />
        ))}
      </div>
    );
  }

  if (!kpis) return null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
      <StatusCard label={t('lifecycle.kpi.status')} status={kpis.lifecycle_status} />
      <TextKpi icon={Building2} label={t('lifecycle.kpi.entity')} value={kpis.entity} />
      <TextKpi icon={Server} label={t('lifecycle.kpi.server')} value={kpis.server} />
      <KpiCard icon={Calendar} label={t('lifecycle.kpi.activeDays')} value={kpis.active_days} />
      <KpiCard icon={Zap} label={t('lifecycle.kpi.totalCumulative')} value={kpis.total_cumulative_r_sent} />
      <KpiCard icon={TrendingUp} label={t('lifecycle.kpi.avgRSent')} value={kpis.avg_r_sent} format="decimal" />
      <KpiCard icon={Gauge} label={t('lifecycle.kpi.avgSentRatio')} value={kpis.avg_sent_ratio} format="percent" />
      <KpiCard icon={TrendingUp} label={t('lifecycle.kpi.avgGrowth')} value={kpis.avg_growth_rate} format="percent" />
      <KpiCard icon={TrendingDown} label={t('lifecycle.kpi.avgDrops')} value={kpis.avg_drops_per_day} format="decimal" />
      <KpiCard icon={TrendingDown} label={t('lifecycle.kpi.maxDrops')} value={kpis.max_drops_per_day} />
    </div>
  );
}
