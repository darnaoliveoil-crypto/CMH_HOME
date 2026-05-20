import {
  Area,
  AreaChart,
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

export default function DailyVolumeChart({ data }) {
  const { t } = useLocale();
  return (
    <ChartCard title={t('charts.dailyVolume')} subtitle={t('charts.dailyVolumeSub')}>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="volumeGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={CHART_COLORS.accent} stopOpacity={0.4} />
              <stop offset="95%" stopColor={CHART_COLORS.accent} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} vertical={false} />
          <XAxis dataKey="date" tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
          <Tooltip
            contentStyle={{ background: '#1a1d2e', border: '1px solid #2a2f45', borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: '#e2e8f0' }}
            formatter={(v) => [formatNumber(v), 'R_Sent Volume']}
          />
          <Area type="monotone" dataKey="volume" stroke={CHART_COLORS.accent} fill="url(#volumeGrad)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
