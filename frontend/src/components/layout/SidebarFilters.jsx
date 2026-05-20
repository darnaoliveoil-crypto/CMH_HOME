import { RotateCcw, SlidersHorizontal } from 'lucide-react';
import { useFilters } from '../../context/FiltersContext';
import { useLocale } from '../../context/LocaleContext';
import { SENT_VOLUME_MAX } from '../../utils/filterMetadata';
import { formatNumber } from '../../utils/formatters';

export default function SidebarFilters() {
  const { filters, setFilters, resetFilters, filterOptions, optionsLoading } = useFilters();
  const { t } = useLocale();

  const selectClass =
    'w-full bg-dash-input border border-dash text-dash text-xs rounded-lg px-2.5 py-2 focus:outline-none focus:border-blue-500 transition-colors cursor-pointer disabled:opacity-50';

  const update = (key, value) => setFilters({ ...filters, [key]: value });

  const handleSelect = (key) => (e) => update(key, e.target.value);

  const minVol = Number(filters.sentVolumeMin ?? 0);
  const maxVol = Number(filters.sentVolumeMax ?? SENT_VOLUME_MAX);

  function handleMinVolume(e) {
    const next = Math.min(Number(e.target.value), maxVol);
    update('sentVolumeMin', next);
  }

  function handleMaxVolume(e) {
    const next = Math.max(Number(e.target.value), minVol);
    update('sentVolumeMax', next);
  }

  return (
    <div className="px-3 pb-4 border-t border-dash pt-4">
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-dash-muted uppercase tracking-wider">
          <SlidersHorizontal className="w-3.5 h-3.5" />
          {t('globalFilters')}
        </div>
        <button
          type="button"
          onClick={resetFilters}
          title={t('resetFilters')}
          className="p-1 rounded text-dash-faint hover:text-dash hover:bg-dash-card transition-colors"
        >
          <RotateCcw className="w-3 h-3" />
        </button>
      </div>

      <div className="space-y-3">
        <div>
          <label className="block text-[10px] text-dash-faint mb-1 font-medium">{t('entity')}</label>
          <select
            className={selectClass}
            value={filters.entity}
            onChange={handleSelect('entity')}
            disabled={optionsLoading}
          >
            {filterOptions.entities.map((e) => (
              <option key={e} value={e}>
                {e === 'All' ? t('common.all') : e}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[10px] text-dash-faint mb-1 font-medium">{t('tables.server')}</label>
          <select
            className={selectClass}
            value={filters.server}
            onChange={handleSelect('server')}
            disabled={optionsLoading}
          >
            {filterOptions.servers.map((s) => (
              <option key={s} value={s}>
                {s === 'All' ? t('common.all') : s}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[10px] text-dash-faint mb-1 font-medium">{t('year')}</label>
          <select
            className={selectClass}
            value={filters.year}
            onChange={handleSelect('year')}
            disabled={optionsLoading}
          >
            {filterOptions.years.map((y) => (
              <option key={y} value={y}>
                {y === 'All' ? t('yearAll') : y}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[10px] text-dash-faint mb-1 font-medium">{t('month')}</label>
          <select
            className={selectClass}
            value={filters.month}
            onChange={handleSelect('month')}
            disabled={optionsLoading}
          >
            {filterOptions.months.map((m) => (
              <option key={m} value={m}>
                {m === 'All' ? t('monthAll') : m}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[10px] text-dash-faint mb-1 font-medium">{t('day')}</label>
          <select
            className={selectClass}
            value={filters.day}
            onChange={handleSelect('day')}
            disabled={optionsLoading}
          >
            {filterOptions.days.map((d) => (
              <option key={d} value={d}>
                {d === 'All' ? t('dayAll') : d}
              </option>
            ))}
          </select>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-[10px] text-dash-faint font-medium">{t('filters.sentVolumeRange')}</label>
            <span className="text-[10px] text-dash-muted font-mono">
              {formatNumber(minVol)} – {formatNumber(maxVol)}
            </span>
          </div>

          <div className="space-y-2 rounded-lg border border-dash bg-dash-input px-2.5 py-2.5">
            <div>
              <div className="flex justify-between text-[9px] text-dash-faint mb-0.5">
                <span>{t('filters.min')}</span>
                <span>{formatNumber(minVol)}</span>
              </div>
              <input
                type="range"
                min={0}
                max={SENT_VOLUME_MAX}
                step={100}
                value={minVol}
                onChange={handleMinVolume}
                className="w-full h-1.5 accent-blue-500 cursor-pointer"
                aria-label={t('filters.sentVolumeMin')}
              />
            </div>
            <div>
              <div className="flex justify-between text-[9px] text-dash-faint mb-0.5">
                <span>{t('filters.max')}</span>
                <span>{formatNumber(maxVol)}</span>
              </div>
              <input
                type="range"
                min={0}
                max={SENT_VOLUME_MAX}
                step={100}
                value={maxVol}
                onChange={handleMaxVolume}
                className="w-full h-1.5 accent-blue-500 cursor-pointer"
                aria-label={t('filters.sentVolumeMax')}
              />
            </div>
            <div className="flex justify-between text-[9px] text-dash-faint pt-0.5">
              <span>0</span>
              <span>{formatNumber(SENT_VOLUME_MAX)}</span>
            </div>
          </div>
        </div>
      </div>

      {optionsLoading && (
        <p className="text-[10px] text-dash-faint text-center mt-3 animate-pulse">{t('filters.loadingOptions')}</p>
      )}
    </div>
  );
}
