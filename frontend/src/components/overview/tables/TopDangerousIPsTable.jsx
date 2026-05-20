import RiskBadge from '../../common/RiskBadge';
import { useLocale } from '../../../context/LocaleContext';
import { formatDatetime, formatNumber, formatPercent } from '../../../utils/formatters';

const thClass = 'px-4 py-3 text-left text-xs font-semibold text-dash-faint uppercase tracking-wider';
const tdClass = 'px-4 py-3 text-sm text-dash-muted whitespace-nowrap';

export default function TopDangerousIPsTable({ data }) {
  const { t } = useLocale();

  return (
    <div className="rounded-xl border border-dash bg-dash-card overflow-hidden hover:border-[var(--dash-border-hover)] transition-colors">
      <div className="px-5 py-4 border-b border-dash">
        <h3 className="text-sm font-semibold text-dash">{t('tables.topDangerous')}</h3>
        <p className="text-xs text-dash-faint mt-0.5">{t('tables.topDangerousSub')}</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[900px]">
          <thead className="bg-dash/50">
            <tr>
              <th className={thClass}>{t('tables.ip')}</th>
              <th className={thClass}>{t('tables.entity')}</th>
              <th className={thClass}>{t('tables.server')}</th>
              <th className={thClass}>{t('tables.datetime')}</th>
              <th className={thClass}>{t('tables.riskLabel')}</th>
              <th className={thClass}>{t('tables.detectedError')}</th>
              <th className={thClass}>{t('tables.rSent')}</th>
              <th className={thClass}>{t('tables.sentRatio')}</th>
              <th className={thClass}>{t('tables.growthRate')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--dash-border)]">
            {data.map((row) => (
              <tr key={row.ip} className="hover:bg-dash-card-hover transition-colors">
                <td className={`${tdClass} font-mono text-blue-500`}>{row.ip}</td>
                <td className={tdClass}>{row.entity}</td>
                <td className={tdClass}>{row.server}</td>
                <td className={tdClass}>{formatDatetime(row.datetime || row.last_datetime)}</td>
                <td className={tdClass}><RiskBadge label={row.risk_label} /></td>
                <td className={tdClass}>
                  <span className="text-red-500 font-medium">{row.detected_error || row.last_error || '—'}</span>
                </td>
                <td className={tdClass}>{formatNumber(row.r_sent_per_ip ?? row.last_r_sent)}</td>
                <td className={tdClass}>{formatPercent(row.sent_ratio, 1)}</td>
                <td className={tdClass}>
                  <span className={(row.growth_rate ?? 0) >= 0 ? 'text-red-500' : 'text-green-500'}>
                    {(row.growth_rate ?? 0) >= 0 ? '+' : ''}{Number(row.growth_rate ?? 0).toFixed(1)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
