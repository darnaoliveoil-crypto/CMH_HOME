import { useLocale } from '../../context/LocaleContext';
import { formatDatetime, formatNumber, formatPercent } from '../../utils/formatters';
import RiskBadge from '../common/RiskBadge';
import ChartCard from '../overview/charts/ChartCard';

function DataTable({ columns, rows, emptyMessage }) {
  if (!rows.length) {
    return <p className="text-sm text-dash-faint py-4">{emptyMessage}</p>;
  }

  return (
    <div className="overflow-x-auto max-h-[360px] overflow-y-auto">
      <table className="w-full text-sm min-w-[720px]">
        <thead className="sticky top-0 bg-dash-card z-10">
          <tr className="border-b border-dash text-dash-faint text-left">
            {columns.map((col) => (
              <th key={col.key} className="py-2 px-3 font-medium whitespace-nowrap">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx} className="border-b border-dash/50 hover:bg-dash-card-hover">
              {columns.map((col) => (
                <td key={col.key} className="py-2 px-3 text-dash whitespace-nowrap">
                  {col.render ? col.render(row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ErrorTimelineTable({ errors, loading }) {
  const { t } = useLocale();
  const columns = [
    { key: 'datetime', label: t('tables.datetime'), render: (r) => formatDatetime(r.datetime) },
    { key: 'error_type', label: t('lifecycle.errorType') },
    { key: 'sent_per_ip', label: t('lifecycle.sentPerIp'), render: (r) => formatNumber(r.sent_per_ip) },
    { key: 'r_sent_per_ip', label: t('tables.rSent'), render: (r) => formatNumber(r.r_sent_per_ip) },
  ];

  return (
    <ChartCard title={t('lifecycle.errorTimeline')} subtitle={t('lifecycle.errorTimelineSub')}>
      {loading ? (
        <div className="h-40 animate-pulse rounded-lg bg-dash-input" />
      ) : (
        <DataTable columns={columns} rows={errors} emptyMessage={t('lifecycle.noErrors')} />
      )}
    </ChartCard>
  );
}

export function HistoryActivityTable({ history, loading }) {
  const { t } = useLocale();
  const columns = [
    { key: 'datetime', label: t('tables.datetime'), render: (r) => formatDatetime(r.datetime) },
    { key: 'sent_per_ip', label: t('lifecycle.sentPerIp'), render: (r) => formatNumber(r.sent_per_ip) },
    { key: 'r_sent_per_ip', label: t('tables.rSent'), render: (r) => formatNumber(r.r_sent_per_ip) },
    { key: 'sent_ratio', label: t('tables.sentRatio'), render: (r) => formatPercent(r.sent_ratio, 1) },
    { key: 'growth_rate', label: t('tables.growthRate'), render: (r) => formatPercent(r.growth_rate, 1) },
    { key: 'drops_per_day', label: t('lifecycle.dropsPerDay'), render: (r) => formatNumber(r.drops_per_day) },
    { key: 'errorType', label: t('lifecycle.errorType'), render: (r) => r.errorType },
    { key: 'risk_label', label: t('tables.riskLabel'), render: (r) => <RiskBadge label={r.risk_label} /> },
  ];

  return (
    <ChartCard title={t('lifecycle.historyTable')} subtitle={t('lifecycle.historyTableSub')}>
      {loading ? (
        <div className="h-40 animate-pulse rounded-lg bg-dash-input" />
      ) : (
        <DataTable columns={columns} rows={history} emptyMessage={t('lifecycle.noData')} />
      )}
    </ChartCard>
  );
}
