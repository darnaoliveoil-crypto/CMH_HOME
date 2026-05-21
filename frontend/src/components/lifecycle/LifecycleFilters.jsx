import { Filter, RotateCcw } from 'lucide-react';
import { useLocale } from '../../context/LocaleContext';

function SelectField({ label, value, onChange, options, disabled }) {
  return (
    <label className="flex flex-col gap-1 min-w-[120px] flex-1">
      <span className="text-[10px] font-medium text-dash-faint uppercase tracking-wide">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="rounded-lg dash-input px-3 py-2 text-sm dash-input-focus disabled:opacity-50"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </label>
  );
}

export default function LifecycleFilters({
  filters,
  ips,
  filterOptions,
  onChange,
  onReset,
  disabled,
}) {
  const { t } = useLocale();

  return (
    <div className="glass-card p-4">
      <div className="flex items-center gap-2 mb-4">
        <Filter className="w-4 h-4 text-[#00c9b1]" />
        <h3 className="text-sm font-semibold text-dash">{t('lifecycle.filtersTitle')}</h3>
      </div>

      <div className="flex flex-wrap gap-3">
        <label className="flex flex-col gap-1 min-w-[200px] flex-[2]">
          <span className="text-[10px] font-medium text-dash-faint uppercase tracking-wide">
            {t('tables.ip')}
          </span>
          <select
            value={filters.ip}
            onChange={(e) => onChange('ip', e.target.value)}
            disabled={disabled || !ips.length}
            className="rounded-lg dash-input px-3 py-2 text-sm font-mono dash-input-focus"
          >
            {ips.map((ip) => (
              <option key={ip} value={ip}>
                {ip}
              </option>
            ))}
          </select>
        </label>

        <SelectField
          label={t('tables.server')}
          value={filters.server}
          onChange={(v) => onChange('server', v)}
          options={filterOptions.servers}
          disabled={disabled}
        />
        <SelectField
          label={t('tables.entity')}
          value={filters.entity}
          onChange={(v) => onChange('entity', v)}
          options={filterOptions.entities}
          disabled={disabled}
        />
        <SelectField
          label={t('year')}
          value={filters.year}
          onChange={(v) => onChange('year', v)}
          options={filterOptions.years}
          disabled={disabled}
        />
        <SelectField
          label={t('month')}
          value={filters.month}
          onChange={(v) => onChange('month', v)}
          options={filterOptions.months}
          disabled={disabled}
        />
        <SelectField
          label={t('day')}
          value={filters.day}
          onChange={(v) => onChange('day', v)}
          options={filterOptions.days}
          disabled={disabled}
        />

        <label className="flex flex-col gap-1 min-w-[140px]">
          <span className="text-[10px] font-medium text-dash-faint uppercase tracking-wide">
            {t('lifecycle.dateFrom')}
          </span>
          <input
            type="date"
            value={filters.dateFrom}
            onChange={(e) => onChange('dateFrom', e.target.value)}
            disabled={disabled}
            className="rounded-lg dash-input px-3 py-2 text-sm dash-input-focus"
          />
        </label>
        <label className="flex flex-col gap-1 min-w-[140px]">
          <span className="text-[10px] font-medium text-dash-faint uppercase tracking-wide">
            {t('lifecycle.dateTo')}
          </span>
          <input
            type="date"
            value={filters.dateTo}
            onChange={(e) => onChange('dateTo', e.target.value)}
            disabled={disabled}
            className="rounded-lg dash-input px-3 py-2 text-sm dash-input-focus"
          />
        </label>

        <div className="flex items-end">
          <button
            type="button"
            onClick={onReset}
            disabled={disabled}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-dash text-dash-muted hover:text-dash hover:bg-dash-card text-sm transition-colors disabled:opacity-50"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            {t('resetFilters')}
          </button>
        </div>
      </div>
    </div>
  );
}
