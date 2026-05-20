import { Database } from 'lucide-react';
import ErrorState from '../components/common/ErrorState';
import { ChartSkeleton, KpiSkeletonRow, TableSkeleton } from '../components/common/LoadingSkeleton';
import KpiRow from '../components/overview/KpiRow';
import DailyVolumeChart from '../components/overview/charts/DailyVolumeChart';
import ErrorHeatmap from '../components/overview/charts/ErrorHeatmap';
import FrequentErrorsChart from '../components/overview/charts/FrequentErrorsChart';
import RiskDistributionChart from '../components/overview/charts/RiskDistributionChart';
import RiskTransitionChart from '../components/overview/charts/RiskTransitionChart';
import LatestIPStatusTable from '../components/overview/tables/LatestIPStatusTable';
import TopDangerousIPsTable from '../components/overview/tables/TopDangerousIPsTable';
import { useFilters } from '../context/FiltersContext';
import { useLocale } from '../context/LocaleContext';
import { useOverviewData } from '../hooks/useOverviewData';

export default function GlobalOverview() {
  const { filters } = useFilters();
  const { t } = useLocale();
  const {
    loading,
    error,
    usingMock,
    kpis,
    riskDistribution,
    dailyVolume,
    errors,
    transitions,
    hourlyHeatmap,
    dayHeatmap,
    dangerousIPs,
    latestIPs,
    retry,
  } = useOverviewData(filters);

  if (error && !kpis) {
    return <ErrorState message={error} onRetry={retry} />;
  }

  return (
    <div className="space-y-6 max-w-[1600px]">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-dash">{t('overview.title')}</h2>
          <p className="text-sm text-dash-faint mt-0.5">{t('overview.subtitle')}</p>
        </div>
        {usingMock && (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30">
            <Database className="w-3 h-3" />
            {t('overview.mockBadge')}
          </span>
        )}
      </div>

      {loading ? (
        <>
          <KpiSkeletonRow />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartSkeleton />
            <ChartSkeleton />
          </div>
          <ChartSkeleton className="col-span-2" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartSkeleton />
            <ChartSkeleton className="col-span-2" />
          </div>
          <TableSkeleton />
          <TableSkeleton />
        </>
      ) : (
        <>
          <KpiRow kpis={kpis} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <RiskDistributionChart data={riskDistribution} />
            <DailyVolumeChart data={dailyVolume} />
          </div>

          <div className="grid grid-cols-1 gap-4">
            <FrequentErrorsChart data={errors} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <RiskTransitionChart data={transitions} />
            <ErrorHeatmap hourlyData={hourlyHeatmap} dayData={dayHeatmap} />
          </div>

          {error && (
            <ErrorState message={t('overview.partialError')} onRetry={retry} />
          )}

          <TopDangerousIPsTable data={dangerousIPs} />
          <LatestIPStatusTable data={latestIPs} />
        </>
      )}
    </div>
  );
}
