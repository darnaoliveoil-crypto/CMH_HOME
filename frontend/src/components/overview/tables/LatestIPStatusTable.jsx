import { useMemo, useState } from 'react';
import { ArrowDown, ArrowUp, ArrowUpDown, Search } from 'lucide-react';
import RiskBadge from '../../common/RiskBadge';
import { useLocale } from '../../../context/LocaleContext';
import { formatDatetime, formatNumber, formatPercent } from '../../../utils/formatters';

const COLUMN_KEYS = [
  { key: 'ip', labelKey: 'tables.ip' },
  { key: 'entity', labelKey: 'tables.entity' },
  { key: 'server', labelKey: 'tables.server' },
  { key: 'last_datetime', labelKey: 'tables.lastDatetime' },
  { key: 'risk_label', labelKey: 'tables.riskLabel' },
  { key: 'last_error', labelKey: 'tables.lastError' },
  { key: 'last_r_sent', labelKey: 'tables.lastRSent' },
  { key: 'sent_ratio', labelKey: 'tables.sentRatio' },
];

const thClass = 'px-4 py-3 text-left text-xs font-semibold text-dash-faint uppercase tracking-wider cursor-pointer select-none hover:text-dash-muted';
const tdClass = 'px-4 py-3 text-sm text-dash-muted whitespace-nowrap';

export default function LatestIPStatusTable({ data }) {
  const { t } = useLocale();
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState('last_datetime');
  const [sortDir, setSortDir] = useState('desc');

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim();
    let rows = [...data];
    if (q) {
      rows = rows.filter(
        (r) =>
          r.ip?.toLowerCase().includes(q) ||
          r.entity?.toLowerCase().includes(q) ||
          r.server?.toLowerCase().includes(q) ||
          r.risk_label?.toLowerCase().includes(q),
      );
    }
    rows.sort((a, b) => {
      let av = a[sortKey];
      let bv = b[sortKey];
      if (sortKey === 'last_datetime') {
        av = new Date(av).getTime() || 0;
        bv = new Date(bv).getTime() || 0;
      } else if (typeof av === 'string') {
        av = av?.toLowerCase() ?? '';
        bv = bv?.toLowerCase() ?? '';
      }
      if (av < bv) return sortDir === 'asc' ? -1 : 1;
      if (av > bv) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return rows;
  }, [data, search, sortKey, sortDir]);

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const SortIcon = ({ col }) => {
    if (sortKey !== col) return <ArrowUpDown className="w-3 h-3 inline ml-1 opacity-40" />;
    return sortDir === 'asc'
      ? <ArrowUp className="w-3 h-3 inline ml-1 text-blue-500" />
      : <ArrowDown className="w-3 h-3 inline ml-1 text-blue-500" />;
  };

  return (
    <div className="rounded-xl border border-dash bg-dash-card overflow-hidden hover:border-[var(--dash-border-hover)] transition-colors">
      <div className="px-5 py-4 border-b border-dash flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-dash">{t('tables.latestStatus')}</h3>
          <p className="text-xs text-dash-faint mt-0.5">{t('tables.latestStatusSub')}</p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dash-faint" />
          <input
            type="text"
            placeholder={t('tables.searchPlaceholder')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 pr-4 py-2 rounded-lg bg-dash-input border border-dash text-sm text-dash placeholder:text-dash-faint focus:outline-none focus:border-blue-500 w-64"
          />
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[900px]">
          <thead className="bg-dash/50">
            <tr>
              {COLUMN_KEYS.map((col) => (
                <th key={col.key} className={thClass} onClick={() => toggleSort(col.key)}>
                  {t(col.labelKey)}
                  <SortIcon col={col.key} />
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--dash-border)]">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-dash-faint text-sm">
                  {t('tables.noResults')}
                </td>
              </tr>
            ) : (
              filtered.map((row) => (
                <tr key={row.ip} className="hover:bg-dash-card-hover transition-colors">
                  <td className={`${tdClass} font-mono text-blue-500`}>{row.ip}</td>
                  <td className={tdClass}>{row.entity}</td>
                  <td className={tdClass}>{row.server}</td>
                  <td className={tdClass}>{formatDatetime(row.last_datetime)}</td>
                  <td className={tdClass}><RiskBadge label={row.risk_label} /></td>
                  <td className={tdClass}>
                    {row.last_error ? (
                      <span className="text-amber-500">{row.last_error}</span>
                    ) : (
                      <span className="text-dash-faint">—</span>
                    )}
                  </td>
                  <td className={tdClass}>{formatNumber(row.last_r_sent)}</td>
                  <td className={tdClass}>{formatPercent(row.sent_ratio, 1)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="px-5 py-2 border-t border-dash text-xs text-dash-faint">
        {t('tables.showing', { n: filtered.length, total: data.length })}
      </div>
    </div>
  );
}
