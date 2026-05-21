import { AlertTriangle, Loader2 } from 'lucide-react';
import ErrorState from '../components/common/ErrorState';
import CorrelationMatrix from '../components/lifecycle/CorrelationMatrix';
import LifecycleFilters from '../components/lifecycle/LifecycleFilters';
import LifecycleKpiRow from '../components/lifecycle/LifecycleKpiRow';
import LifecycleSummaryTable from '../components/lifecycle/LifecycleSummaryTable';
import {
  CumulativeRSentChart,
  FrequentErrorChart,
  GrowthRateChart,
  RiskZoneChart,
  SentRatioChart,
  SentVsRSentChart,
  TimeGapChart,
} from '../components/lifecycle/LifecycleCharts';
import { ErrorTimelineTable, HistoryActivityTable } from '../components/lifecycle/LifecycleTables';
import { useLocale } from '../context/LocaleContext';
import { useLifecycleData } from '../hooks/useLifecycleData';

function SectionNotice({ message }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-400">
      <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
      {message}
    </div>
  );
}

export default function IPLifecycle() {
  const { t } = useLocale();
  const {
    filters,
    updateFilter,
    resetFilters,
    ips,
    kpis,
    errorTimeline,
    history,
    filterOptions,
    chartSeries,
    summary,
    errorBarData,
    correlation,
    loading,
    apiErrors,
    retry,
  } = useLifecycleData();

  if (apiErrors.fatal) {
    return (
      <div className="max-w-[1600px]">
        <ErrorState
          message={t('lifecycle.apiUnreachable', { detail: apiErrors.ips })}
          onRetry={retry}
        />
      </div>
    );
  }

  const chartsReady = chartSeries.length > 0;

  return (
    <div className="space-y-6 max-w-[1600px]">
      <div>
        <h2 className="text-xl font-bold text-dash">{t('lifecycle.title')}</h2>
        <p className="text-sm text-dash-faint mt-0.5">{t('lifecycle.subtitle')}</p>
      </div>

      <LifecycleFilters
        filters={filters}
        ips={ips}
        filterOptions={filterOptions}
        onChange={updateFilter}
        onReset={resetFilters}
        disabled={loading.ips}
      />

      {(apiErrors.kpis || apiErrors.errors || apiErrors.history) && (
        <SectionNotice message={t('lifecycle.partialError')} />
      )}

      <LifecycleKpiRow kpis={kpis} loading={loading.kpis} />

      <LifecycleSummaryTable summary={summary} loading={loading.history} />

      {loading.history && !chartsReady ? (
        <div className="flex items-center justify-center gap-2 py-16 text-dash-muted">
          <Loader2 className="w-5 h-5 animate-spin text-[#00c9b1]" />
          <span className="text-sm">{t('lifecycle.loadingCharts')}</span>
        </div>
      ) : chartsReady ? (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <SentVsRSentChart data={chartSeries} />
            <CumulativeRSentChart data={chartSeries} />
            <GrowthRateChart data={chartSeries} />
            <TimeGapChart data={chartSeries} />
            <SentRatioChart data={chartSeries} />
            <RiskZoneChart data={chartSeries} />
          </div>

          <FrequentErrorChart data={errorBarData} />

          <div className="grid grid-cols-1 gap-4">
            <ErrorTimelineTable errors={errorTimeline} loading={loading.errors} />
            <HistoryActivityTable history={history} loading={loading.history} />
          </div>

          <CorrelationMatrix matrix={correlation} loading={loading.history} />
        </>
      ) : (
        <p className="text-sm text-dash-faint text-center py-8">{t('lifecycle.noData')}</p>
      )}
    </div>
  );
}
