import { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchAllIps, fetchIpErrors, fetchIpHistory, fetchIpKpis } from '../api/client';
import {
  applyLifecycleFilters,
  buildChartSeries,
  buildCorrelationMatrix,
  buildErrorBarData,
  buildFilterOptions,
  buildLifecycleSummary,
  defaultLifecycleFilters,
  normalizeHistoryRow,
  sortHistory,
} from '../utils/lifecycle';

export function useLifecycleData() {
  const [filters, setFilters] = useState(defaultLifecycleFilters);
  const [ips, setIps] = useState([]);
  const [kpis, setKpis] = useState(null);
  const [errors, setErrors] = useState([]);
  const [history, setHistory] = useState([]);

  const [ipsLoading, setIpsLoading] = useState(true);
  const [kpisLoading, setKpisLoading] = useState(false);
  const [errorsLoading, setErrorsLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);

  const [ipsError, setIpsError] = useState(null);
  const [kpisError, setKpisError] = useState(null);
  const [errorsError, setErrorsError] = useState(null);
  const [historyError, setHistoryError] = useState(null);

  const loadIps = useCallback(async () => {
    setIpsLoading(true);
    setIpsError(null);
    try {
      const data = await fetchAllIps();
      const list = data.ips ?? [];
      setIps(list);
      setFilters((prev) => (prev.ip ? prev : { ...prev, ip: list[0] ?? '' }));
    } catch (err) {
      setIpsError(err.message || 'Failed to load IPs');
    } finally {
      setIpsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadIps();
  }, [loadIps]);

  const loadIpData = useCallback(async (ip) => {
    if (!ip) return;

    setKpisLoading(true);
    setErrorsLoading(true);
    setHistoryLoading(true);
    setKpisError(null);
    setErrorsError(null);
    setHistoryError(null);

    const kpisPromise = fetchIpKpis(ip)
      .then((data) => {
        if (data.error) throw new Error(data.error);
        setKpis(data);
      })
      .catch((err) => setKpisError(err.message || 'Failed to load KPIs'))
      .finally(() => setKpisLoading(false));

    const errorsPromise = fetchIpErrors(ip)
      .then((data) => setErrors(data.errors ?? []))
      .catch((err) => setErrorsError(err.message || 'Failed to load errors'))
      .finally(() => setErrorsLoading(false));

    const historyPromise = fetchIpHistory(ip)
      .then((data) => {
        const rows = sortHistory((data.history ?? []).map(normalizeHistoryRow));
        setHistory(rows);
      })
      .catch((err) => setHistoryError(err.message || 'Failed to load history'))
      .finally(() => setHistoryLoading(false));

    await Promise.all([kpisPromise, errorsPromise, historyPromise]);
  }, []);

  useEffect(() => {
    if (filters.ip) loadIpData(filters.ip);
  }, [filters.ip, loadIpData]);

  const filterOptions = useMemo(() => buildFilterOptions(history), [history]);

  const filteredHistory = useMemo(
    () => applyLifecycleFilters(history, filters),
    [history, filters],
  );

  const filteredErrors = useMemo(() => {
    const from = filters.dateFrom ? new Date(filters.dateFrom).getTime() : null;
    const to = filters.dateTo
      ? new Date(filters.dateTo).setHours(23, 59, 59, 999)
      : null;
    return errors.filter((e) => {
      const ms = new Date(e.datetime).getTime();
      if (from && ms < from) return false;
      if (to && ms > to) return false;
      return true;
    });
  }, [errors, filters.dateFrom, filters.dateTo]);

  const chartSeries = useMemo(() => buildChartSeries(filteredHistory), [filteredHistory]);
  const summary = useMemo(() => buildLifecycleSummary(filteredHistory), [filteredHistory]);
  const errorBarData = useMemo(() => buildErrorBarData(filteredErrors), [filteredErrors]);
  const correlation = useMemo(() => buildCorrelationMatrix(filteredHistory), [filteredHistory]);

  const updateFilter = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters((prev) => ({
      ...defaultLifecycleFilters,
      ip: prev.ip,
    }));
  }, []);

  const retry = useCallback(() => {
    loadIps();
    if (filters.ip) loadIpData(filters.ip);
  }, [loadIps, loadIpData, filters.ip]);

  const anyLoading = ipsLoading || kpisLoading || errorsLoading || historyLoading;
  const fatalError = ipsError && !ips.length;

  return {
    filters,
    updateFilter,
    resetFilters,
    ips,
    kpis,
    errorTimeline: filteredErrors,
    history: filteredHistory,
    filterOptions,
    chartSeries,
    summary,
    errorBarData,
    correlation,
    loading: {
      ips: ipsLoading,
      kpis: kpisLoading,
      errors: errorsLoading,
      history: historyLoading,
      any: anyLoading,
    },
    apiErrors: {
      ips: ipsError,
      kpis: kpisError,
      errors: errorsError,
      history: historyError,
      fatal: fatalError,
      any: ipsError || kpisError || errorsError || historyError,
    },
    retry,
  };
}
