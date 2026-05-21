import { useLocale } from '../../context/LocaleContext';
import { formatDatetime, formatNumber, formatPercent } from '../../utils/formatters';
import RiskBadge from '../common/RiskBadge';
import ChartCard from '../overview/charts/ChartCard';

function formatCell(value, format) {
  if (value === '—' || value == null) return '—';
  if (format === 'datetime') return formatDatetime(value);
  if (format === 'number') return formatNumber(value);
  if (format === 'ratio') return formatPercent(value, 1);
  if (format === 'risk') return <RiskBadge label={value} />;
  return String(value);
}

export default function LifecycleSummaryTable({ summary, loading }) {
  const { t } = useLocale();
  const rows = [...(summary?.metrics ?? []), ...(summary?.extras ?? [])];

  return (
    <ChartCard title={t('lifecycle.summaryTitle')} subtitle={t('lifecycle.summarySub')}>
      {loading ? (
        <div className="h-48 animate-pulse rounded-lg glass-card" />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead>
              <tr className="border-b border-dash text-dash-faint text-left">
                <th className="py-2 pr-4 font-medium">{t('lifecycle.metric')}</th>
                <th className="py-2 px-3 font-medium text-center">FIRST</th>
                <th className="py-2 px-3 font-medium text-center">LAST</th>
                <th className="py-2 px-3 font-medium text-center">MIN</th>
                <th className="py-2 px-3 font-medium text-center">MAX</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.key} className="border-b border-dash/60 hover:bg-dash-card-hover">
                  <td className="py-2.5 pr-4 text-dash-muted font-medium">{row.label}</td>
                  <td className="py-2.5 px-3 text-center text-dash">{formatCell(row.first, row.format)}</td>
                  <td className="py-2.5 px-3 text-center text-dash">{formatCell(row.last, row.format)}</td>
                  <td className="py-2.5 px-3 text-center text-dash">{formatCell(row.min, row.format)}</td>
                  <td className="py-2.5 px-3 text-center text-dash">{formatCell(row.max, row.format)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </ChartCard>
  );
}
