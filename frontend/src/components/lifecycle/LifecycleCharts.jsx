import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useLocale } from '../../context/LocaleContext';
import { CHART_COLORS } from '../../utils/colors';
import { formatNumber, formatPercent } from '../../utils/formatters';
import ChartCard from '../overview/charts/ChartCard';
import { axisTick, gridStroke, tooltipStyle } from './chartTheme';

function ChartShell({ title, subtitle, children, height = 280 }) {
  return (
    <ChartCard title={title} subtitle={subtitle}>
      <ResponsiveContainer width="100%" height={height}>
        {children}
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function SentVsRSentChart({ data }) {
  const { t } = useLocale();
  return (
    <ChartShell title={t('lifecycle.charts.sentVsRSent')} subtitle={t('lifecycle.charts.sentVsRSentSub')}>
      <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
        <XAxis dataKey="label" tick={axisTick} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis tick={axisTick} axisLine={false} tickLine={false} tickFormatter={(v) => formatNumber(v)} />
        <Tooltip contentStyle={tooltipStyle} formatter={(v, name) => [formatNumber(v), name]} />
        <Line type="monotone" dataKey="sent" name="Sent" stroke={CHART_COLORS.accent} strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="rSent" name="R_Sent" stroke={CHART_COLORS.secondary} strokeWidth={2} dot={false} />
      </LineChart>
    </ChartShell>
  );
}

export function CumulativeRSentChart({ data }) {
  const { t } = useLocale();
  return (
    <ChartShell title={t('lifecycle.charts.cumulative')} subtitle={t('lifecycle.charts.cumulativeSub')}>
      <AreaChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="cumGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={CHART_COLORS.accent} stopOpacity={0.35} />
            <stop offset="95%" stopColor={CHART_COLORS.accent} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
        <XAxis dataKey="label" tick={axisTick} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis tick={axisTick} axisLine={false} tickLine={false} tickFormatter={(v) => formatNumber(v)} />
        <Tooltip contentStyle={tooltipStyle} formatter={(v) => [formatNumber(v), 'Cumulative R_Sent']} />
        <Area type="monotone" dataKey="cumulativeRSent" stroke={CHART_COLORS.accent} fill="url(#cumGrad)" strokeWidth={2} />
      </AreaChart>
    </ChartShell>
  );
}

export function GrowthRateChart({ data }) {
  const { t } = useLocale();
  return (
    <ChartShell title={t('lifecycle.charts.growth')} subtitle={t('lifecycle.charts.growthSub')}>
      <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
        <XAxis dataKey="label" tick={axisTick} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis tick={axisTick} axisLine={false} tickLine={false} tickFormatter={(v) => formatPercent(v, 0)} />
        <Tooltip contentStyle={tooltipStyle} formatter={(v) => [formatPercent(v, 1), 'Growth Rate']} />
        <ReferenceLine y={0.3} stroke={CHART_COLORS.dangerous} strokeDasharray="4 4" label={{ value: '30% danger', fill: CHART_COLORS.dangerous, fontSize: 10 }} />
        <Line type="monotone" dataKey="growthRate" stroke={CHART_COLORS.risk} strokeWidth={2} dot={false} />
      </LineChart>
    </ChartShell>
  );
}

export function TimeGapChart({ data }) {
  const { t } = useLocale();
  return (
    <ChartShell title={t('lifecycle.charts.timeGap')} subtitle={t('lifecycle.charts.timeGapSub')}>
      <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
        <XAxis dataKey="label" tick={axisTick} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis tick={axisTick} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`${formatNumber(v, 1)} min`, 'Time Gap']} />
        <Line type="monotone" dataKey="timeGap" stroke={CHART_COLORS.accent} strokeWidth={2} dot={false} />
      </LineChart>
    </ChartShell>
  );
}

export function SentRatioChart({ data }) {
  const { t } = useLocale();
  return (
    <ChartShell title={t('lifecycle.charts.sentRatio')} subtitle={t('lifecycle.charts.sentRatioSub')}>
      <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
        <XAxis dataKey="label" tick={axisTick} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis tick={axisTick} axisLine={false} tickLine={false} tickFormatter={(v) => formatPercent(v, 0)} domain={[0, 1]} />
        <Tooltip contentStyle={tooltipStyle} formatter={(v) => [formatPercent(v, 1), 'Sent Ratio']} />
        <ReferenceLine y={0.8} stroke={CHART_COLORS.safe} strokeDasharray="4 4" label={{ value: 'Good 80%', fill: CHART_COLORS.safe, fontSize: 10 }} />
        <ReferenceLine y={0.5} stroke={CHART_COLORS.dangerous} strokeDasharray="4 4" label={{ value: 'Danger 50%', fill: CHART_COLORS.dangerous, fontSize: 10 }} />
        <Line type="monotone" dataKey="sentRatio" stroke={CHART_COLORS.accent} strokeWidth={2} dot={false} />
      </LineChart>
    </ChartShell>
  );
}

export function RiskZoneChart({ data }) {
  const { t } = useLocale();
  return (
    <ChartShell title={t('lifecycle.charts.riskZone')} subtitle={t('lifecycle.charts.riskZoneSub')}>
      <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
        <XAxis dataKey="label" tick={axisTick} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis domain={[0, 2]} ticks={[0, 1, 2]} tick={axisTick} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={tooltipStyle}
          formatter={(v, _n, props) => [props.payload?.riskLabel ?? v, 'Risk']}
        />
        <ReferenceLine y={0.5} stroke={CHART_COLORS.safe} strokeOpacity={0.2} />
        <ReferenceLine y={1.5} stroke={CHART_COLORS.risk} strokeOpacity={0.2} />
        <Line type="stepAfter" dataKey="riskLevel" stroke={CHART_COLORS.dangerous} strokeWidth={2} dot={false} />
      </LineChart>
    </ChartShell>
  );
}

export function FrequentErrorChart({ data }) {
  const { t } = useLocale();
  return (
    <ChartShell title={t('lifecycle.charts.frequentError')} subtitle={t('lifecycle.charts.frequentErrorSub')} height={240}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 12, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} horizontal={false} />
        <XAxis type="number" tick={axisTick} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="type" width={90} tick={axisTick} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} />
        <Bar dataKey="count" fill={CHART_COLORS.risk} radius={[0, 4, 4, 0]} maxBarSize={22} />
      </BarChart>
    </ChartShell>
  );
}
