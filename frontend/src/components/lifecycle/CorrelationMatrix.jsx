import { useLocale } from '../../context/LocaleContext';
import { correlationColor } from '../../utils/lifecycle';
import ChartCard from '../overview/charts/ChartCard';

export default function CorrelationMatrix({ matrix, loading }) {
  const { t } = useLocale();

  if (loading) {
    return (
      <ChartCard title={t('lifecycle.correlationTitle')} subtitle={t('lifecycle.correlationSub')}>
        <div className="h-64 animate-pulse rounded-lg bg-dash-input" />
      </ChartCard>
    );
  }

  if (!matrix?.length) {
    return (
      <ChartCard title={t('lifecycle.correlationTitle')} subtitle={t('lifecycle.correlationSub')}>
        <p className="text-sm text-dash-faint">{t('lifecycle.noData')}</p>
      </ChartCard>
    );
  }

  const labels = matrix[0].cells.map((c) => c.feature);

  return (
    <ChartCard title={t('lifecycle.correlationTitle')} subtitle={t('lifecycle.correlationSub')}>
      <div className="overflow-x-auto">
        <div className="min-w-[560px]">
          <div
            className="grid gap-1 mb-2"
            style={{ gridTemplateColumns: `100px repeat(${labels.length}, 1fr)` }}
          >
            <div />
            {labels.map((label) => (
              <div key={label} className="text-center text-[9px] text-dash-faint font-medium px-0.5">
                {label}
              </div>
            ))}
          </div>

          {matrix.map((row) => (
            <div
              key={row.feature}
              className="grid gap-1 mb-1"
              style={{ gridTemplateColumns: `100px repeat(${labels.length}, 1fr)` }}
            >
              <div className="text-[10px] text-dash-muted flex items-center pr-2">{row.feature}</div>
              {row.cells.map((cell) => (
                <div
                  key={`${row.feature}-${cell.feature}`}
                  title={`${row.feature} × ${cell.feature}: ${cell.value}`}
                  className="h-9 rounded-sm flex items-center justify-center text-[10px] font-semibold"
                  style={{
                    backgroundColor: correlationColor(cell.value),
                    color: Math.abs(cell.value) > 0.45 ? '#fff' : '#1e293b',
                  }}
                >
                  {cell.value.toFixed(2)}
                </div>
              ))}
            </div>
          ))}

          <div className="flex items-center gap-3 mt-4 text-[10px] text-dash-faint">
            <span>-1</span>
            <div className="h-3 flex-1 max-w-xs rounded-full" style={{ background: 'linear-gradient(90deg, #7f1d1d, #fff, #1e3a8a)' }} />
            <span>+1</span>
          </div>
        </div>
      </div>
    </ChartCard>
  );
}
