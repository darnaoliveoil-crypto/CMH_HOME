import {
  AlertTriangle,
  Ban,
  BarChart2,
  Globe,
  Percent,
  Send,
  Shield,
  ShieldAlert,
} from 'lucide-react';
import { useLocale } from '../../context/LocaleContext';
import { formatTrend } from '../../utils/formatters';
import KpiCard from './KpiCard';

export default function KpiRow({ kpis }) {
  const { t } = useLocale();
  if (!kpis) return null;

  const cards = [
    { icon: Globe, label: t('kpi.totalIps'), value: kpis.total_ips, trend: formatTrend(kpis.trends?.total_ips), variant: 'default' },
    { icon: Shield, label: t('kpi.safeIps'), value: kpis.safe_ips, trend: formatTrend(kpis.trends?.safe_ips), variant: 'safe' },
    { icon: ShieldAlert, label: t('kpi.riskIps'), value: kpis.risk_ips, trend: formatTrend(kpis.trends?.risk_ips), variant: 'risk' },
    { icon: AlertTriangle, label: t('kpi.dangerousIps'), value: kpis.dangerous_ips, trend: formatTrend(kpis.trends?.dangerous_ips), variant: 'dangerous' },
    { icon: Ban, label: t('kpi.blockedIps'), value: kpis.blocked_ips, trend: formatTrend(kpis.trends?.blocked_ips), variant: 'blocked' },
    { icon: Send, label: t('kpi.avgRSent'), value: kpis.avg_r_sent, trend: formatTrend(kpis.trends?.avg_r_sent), variant: 'default' },
    { icon: Percent, label: t('kpi.avgSentRatio'), value: kpis.avg_sent_ratio, trend: formatTrend(kpis.trends?.avg_sent_ratio), format: 'percent', variant: 'default' },
    { icon: BarChart2, label: t('kpi.globalErrorRate'), value: kpis.global_error_rate, trend: formatTrend(kpis.trends?.global_error_rate), format: 'percent', variant: 'dangerous' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-4">
      {cards.map((card) => (
        <KpiCard key={card.label} {...card} vsLabel={t('kpi.vsLastPeriod')} />
      ))}
    </div>
  );
}
