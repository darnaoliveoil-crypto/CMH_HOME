import { useState } from 'react';
import { useLocale } from '../../../context/LocaleContext';
import ChartCard from './ChartCard';

const ERROR_KEYS = ['SPF', 'DKIM', 'Rate limit', 'Netblock'];

function intensityColor(value, max) {
  const ratio = max ? value / max : 0;
  if (ratio > 0.75) return 'bg-red-500';
  if (ratio > 0.5) return 'bg-orange-500';
  if (ratio > 0.25) return 'bg-amber-500';
  if (ratio > 0) return 'bg-blue-600/60';
  return 'bg-dash-card';
}

function HeatmapGrid({ data, xLabels, t }) {
  const maxVal = Math.max(
    ...data.flatMap((row) => ERROR_KEYS.map((k) => row[k] || 0)),
    1,
  );

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[520px]">
        <div className="grid gap-1 mb-2" style={{ gridTemplateColumns: `80px repeat(${xLabels.length}, 1fr)` }}>
          <div />
          {xLabels.map((label) => (
            <div key={label} className="text-center text-[10px] text-dash-faint font-medium">
              {label}
            </div>
          ))}
        </div>

        {ERROR_KEYS.map((errKey) => (
          <div
            key={errKey}
            className="grid gap-1 mb-1"
            style={{ gridTemplateColumns: `80px repeat(${data.length}, 1fr)` }}
          >
            <div className="text-[10px] text-dash-muted flex items-center pr-2">{errKey}</div>
            {data.map((row, i) => {
              const val = row[errKey] || 0;
              return (
                <div
                  key={`${errKey}-${i}`}
                  title={`${row.hour ?? row.day} · ${errKey}: ${val}`}
                  className={`h-7 rounded-sm ${intensityColor(val, maxVal)} hover:ring-1 hover:ring-blue-400 transition-all cursor-default flex items-center justify-center`}
                >
                  {val > 0 && (
                    <span className="text-[9px] text-white/80 font-medium">{val}</span>
                  )}
                </div>
              );
            })}
          </div>
        ))}

        <div className="flex items-center gap-2 mt-4 text-[10px] text-dash-faint">
          <span>{t('charts.low')}</span>
          <div className="flex gap-0.5">
            {['bg-dash-card', 'bg-blue-600/60', 'bg-amber-500', 'bg-orange-500', 'bg-red-500'].map((c) => (
              <div key={c} className={`w-6 h-3 rounded-sm ${c}`} />
            ))}
          </div>
          <span>{t('charts.high')}</span>
        </div>
      </div>
    </div>
  );
}

export default function ErrorHeatmap({ hourlyData, dayData }) {
  const [tab, setTab] = useState('hour');
  const { t } = useLocale();

  const hourlyLabels = hourlyData.map((r) => String(r.hour).padStart(2, '0'));
  const dayLabels = dayData.map((r) => r.day);

  return (
    <ChartCard title={t('charts.heatmap')} subtitle={t('charts.heatmapSub')} className="col-span-2">
      <div className="flex gap-2 mb-4">
        {[
          { id: 'hour', label: t('charts.byHour') },
          { id: 'day', label: t('charts.byDay') },
        ].map(({ id, label }) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              tab === id
                ? 'bg-blue-600 text-white'
                : 'bg-dash-input text-dash-muted hover:text-dash border border-dash'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'hour' ? (
        <HeatmapGrid data={hourlyData} xLabels={hourlyLabels} t={t} />
      ) : (
        <HeatmapGrid data={dayData} xLabels={dayLabels} t={t} />
      )}
    </ChartCard>
  );
}
