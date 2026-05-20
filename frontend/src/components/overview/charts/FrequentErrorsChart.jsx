import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useLocale } from '../../../context/LocaleContext';
import { CHART_COLORS } from '../../../utils/colors';
import { formatNumber } from '../../../utils/formatters';
import ChartCard from './ChartCard';

const tooltipStyle = {
  background: 'var(--dash-card)',
  border: '1px solid var(--dash-border)',
  borderRadius: 8,
  fontSize: 12,
  color: 'var(--dash-text)',
};

function ErrorBarChart({ data, dataKey, color, title }) {
  return (
    <div>
      <p className="text-xs text-dash-faint mb-2 font-medium">{title}</p>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 10, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} horizontal={false} />
          <XAxis type="number" tick={{ fill: CHART_COLORS.text, fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis type="category" dataKey="type" width={88} tick={{ fill: CHART_COLORS.text, fontSize: 10 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={tooltipStyle} formatter={(v) => [formatNumber(v), dataKey === 'count' ? 'Count' : 'Volume']} />
          <Bar dataKey={dataKey} fill={color} radius={[0, 4, 4, 0]} maxBarSize={18} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function FrequentErrorsChart({ data }) {
  const { t } = useLocale();
  return (
    <ChartCard title={t('charts.frequentErrors')} subtitle={t('charts.frequentErrorsSub')} className="col-span-2">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ErrorBarChart data={data} dataKey="count" color={CHART_COLORS.risk} title={t('charts.errorCount')} />
        <ErrorBarChart data={data} dataKey="volume" color={CHART_COLORS.dangerous} title={t('charts.errorVolume')} />
      </div>
    </ChartCard>
  );
}
