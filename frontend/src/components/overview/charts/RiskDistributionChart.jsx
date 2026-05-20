import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { useLocale } from '../../../context/LocaleContext';
import { formatNumber } from '../../../utils/formatters';
import ChartCard from './ChartCard';

function CustomTooltip({ active, payload, t }) {
  if (!active || !payload?.length) return null;
  const { name, value, payload: item } = payload[0];
  return (
    <div className="rounded-lg border border-dash bg-dash-card px-3 py-2 text-xs shadow-xl">
      <p className="text-dash font-medium">{t(`risk.${name}`) || name}</p>
      <p className="text-dash-muted">{formatNumber(value)} IPs</p>
      <p className="text-dash-faint">{item?.percent ? `${item.percent}%` : ''}</p>
    </div>
  );
}

export default function RiskDistributionChart({ data }) {
  const { t } = useLocale();
  const total = data.reduce((s, d) => s + d.value, 0);
  const enriched = data.map((d) => ({
    ...d,
    percent: total ? ((d.value / total) * 100).toFixed(1) : 0,
  }));

  return (
    <ChartCard title={t('charts.riskDistribution')} subtitle={t('charts.riskDistributionSub')}>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={enriched}
            cx="50%"
            cy="50%"
            innerRadius={65}
            outerRadius={95}
            paddingAngle={3}
            dataKey="value"
            nameKey="name"
          >
            {enriched.map((entry) => (
              <Cell key={entry.name} fill={entry.color} stroke="transparent" />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip t={t} />} />
          <Legend
            verticalAlign="bottom"
            iconType="circle"
            formatter={(value) => (
              <span className="text-dash-muted text-xs">{t(`risk.${value}`) || value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="text-center -mt-2">
        <p className="text-2xl font-bold text-dash">{formatNumber(total)}</p>
        <p className="text-xs text-dash-faint">{t('charts.totalTracked')}</p>
      </div>
    </ChartCard>
  );
}
