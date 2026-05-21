import { useMemo } from 'react';
import { ArrowRight } from 'lucide-react';
import { useLocale } from '../../../context/LocaleContext';
import { CHART_COLORS } from '../../../utils/colors';
import ChartCard from './ChartCard';

const STATE_STYLE = {
  Risk: { bg: 'bg-amber-500', border: 'border-amber-400', text: 'text-amber-950' },
  Safe: { bg: 'bg-[#00c9b1]', border: 'border-[#00e5c8]', text: 'text-[#020d0d]' },
  Dangerous: { bg: 'bg-red-500', border: 'border-red-400', text: 'text-red-950' },
};

const FLOW_ORDER = [
  { from: 'Risk', to: 'Safe' },
  { from: 'Risk', to: 'Dangerous' },
  { from: 'Safe', to: 'Risk' },
  { from: 'Safe', to: 'Dangerous' },
  { from: 'Dangerous', to: 'Safe' },
  { from: 'Dangerous', to: 'Risk' },
  { from: 'Dangerous', to: 'Dangerous' },
  { from: 'Risk', to: 'Risk' },
  { from: 'Safe', to: 'Safe' },
];

function StateBox({ label, count, t }) {
  const style = STATE_STYLE[label] ?? STATE_STYLE.Risk;
  const translated = t(`risk.${label}`) || label;
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-xl border-2 px-4 py-3 min-w-[100px] ${style.bg} ${style.border} ${style.text}`}
    >
      <span className="text-sm font-bold">{translated}</span>
      {count != null && (
        <span className="text-[10px] font-medium opacity-80 mt-0.5">
          {count} IPs
        </span>
      )}
    </div>
  );
}

function FlowRow({ from, to, count, total, t }) {
  const pct = total ? ((count / total) * 100).toFixed(1) : 0;
  const fromStyle = STATE_STYLE[from];
  const toStyle = STATE_STYLE[to];

  return (
    <div className="flex items-center gap-2 py-2 px-3 rounded-lg bg-dash-input border border-dash hover:bg-dash-card transition-colors">
      <span className={`text-xs font-bold px-2 py-1 rounded ${fromStyle?.bg} ${fromStyle?.text}`}>
        {t(`risk.${from}`)}
      </span>
      <ArrowRight className="w-4 h-4 text-dash-muted shrink-0" />
      <span className={`text-xs font-bold px-2 py-1 rounded ${toStyle?.bg} ${toStyle?.text}`}>
        {t(`risk.${to}`)}
      </span>
      <div className="flex-1 mx-2 h-2 rounded-full bg-[var(--dash-border)] overflow-hidden">
        <div
          className="h-full rounded-full bg-[#00c9b1] transition-all"
          style={{ width: `${Math.min(100, (count / Math.max(total * 0.3, 1)) * 100)}%` }}
        />
      </div>
      <span className="text-sm font-semibold text-dash tabular-nums w-12 text-right">{count}</span>
      <span className="text-xs text-dash-faint w-10 text-right">{pct}%</span>
    </div>
  );
}

export default function RiskTransitionChart({ data }) {
  const { t } = useLocale();

  const { rows, totalTransitions } = useMemo(() => {
    const grouped = {};
    (data || []).forEach(({ from, to, count }) => {
      if (!from || !to || !count) return;
      const key = `${from}->${to}`;
      grouped[key] = (grouped[key] || 0) + count;
    });

    const parsed = FLOW_ORDER.map(({ from, to }) => {
      const key = `${from}->${to}`;
      const count = grouped[key] || 0;
      return { from, to, count };
    }).filter((r) => r.count > 0);

    const extra = Object.entries(grouped)
      .filter(([key]) => !FLOW_ORDER.some((f) => `${f.from}->${f.to}` === key))
      .map(([key, count]) => {
        const [from, to] = key.split('->');
        return { from, to, count };
      });

    const all = [...parsed, ...extra].sort((a, b) => b.count - a.count);
    const total = all.reduce((s, r) => s + r.count, 0);

    return { rows: all, totalTransitions: total };
  }, [data]);

  return (
    <ChartCard title={t('charts.riskTransition')} subtitle={t('charts.riskTransitionSub')}>
      {/* Simple visual: 3 states */}
      <div className="rounded-xl bg-dash-flow border border-dash p-6 mb-4">
        <div className="flex flex-wrap items-center justify-center gap-6 mb-6">
          <StateBox label="Risk" t={t} />
          <div className="flex flex-col items-center gap-1 text-dash-muted">
            <ArrowRight className="w-6 h-6 rotate-[-30deg]" />
            <span className="text-[10px]">{t('charts.to')} Safe</span>
          </div>
          <StateBox label="Safe" t={t} />
        </div>
        <div className="flex justify-center">
          <div className="flex flex-col items-center gap-1">
            <ArrowRight className="w-6 h-6 rotate-90 text-dash-muted" />
            <StateBox label="Dangerous" t={t} />
          </div>
        </div>
        <p className="text-center text-xs text-dash-faint mt-4">
          {totalTransitions.toLocaleString()} {t('charts.transitions').toLowerCase()} ·{' '}
          <span style={{ color: CHART_COLORS.risk }}>■</span> Risk ·{' '}
          <span style={{ color: CHART_COLORS.safe }}>■</span> Safe ·{' '}
          <span style={{ color: CHART_COLORS.dangerous }}>■</span> Dangerous
        </p>
      </div>

      {/* Readable list */}
      <p className="text-xs font-semibold text-dash-muted mb-2 uppercase tracking-wide">
        {t('charts.flowLegend')}
      </p>
      <div className="space-y-1 max-h-[220px] overflow-y-auto pr-1">
        {rows.length === 0 ? (
          <p className="text-center text-xs text-dash-faint py-4">{t('charts.noTransitions')}</p>
        ) : (
          rows.map((row) => (
            <FlowRow
              key={`${row.from}-${row.to}`}
              from={row.from}
              to={row.to}
              count={row.count}
              total={totalTransitions}
              t={t}
            />
          ))
        )}
      </div>
    </ChartCard>
  );
}
