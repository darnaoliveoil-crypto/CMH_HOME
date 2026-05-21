import { useCallback, useEffect, useState } from 'react';
import {
  fetchAllIps,
  fetchIpErrors,
  fetchIpHistory,
  fetchIpKpis,
  fetchOverviewKpis,
} from '../api/client';
import {
  mockDailyVolume,
  mockDayHeatmap,
  mockErrors,
  mockHourlyHeatmap,
  mockIPs,
  mockKPIs,
  mockRiskDistribution,
  mockTransitions,
} from '../mockData';
import { SENT_VOLUME_MAX } from '../utils/filterMetadata';
import {
  CHART_ERROR_TYPES,
  mapRowErrorType,
  normalizeErrorLabel,
} from '../utils/errors';

const HEATMAP_ERRORS = CHART_ERROR_TYPES;
const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function sentVolumeInRange(row, filters) {
  const min = filters.sentVolumeMin ?? 0;
  const max = filters.sentVolumeMax ?? 20000;
  const sent = Number(row.sent_per_ip ?? row.sent ?? 0);
  return sent >= min && sent <= max;
}

function matchesFilters(row, filters) {
  if (filters.entity && filters.entity !== 'All' && row.entity !== filters.entity) return false;
  if (filters.server && filters.server !== 'All' && row.server !== filters.server) return false;
  if (!sentVolumeInRange(row, filters)) return false;

  if (!row.datetime_gride && !row.last_datetime && !row.datetime) {
    return true;
  }
  const dt = new Date(row.datetime_gride || row.datetime || row.last_datetime);
  if (Number.isNaN(dt.getTime())) return true;
  if (filters.year && filters.year !== 'All' && String(dt.getFullYear()) !== filters.year) return false;
  if (filters.month && filters.month !== 'All' && String(dt.getMonth() + 1).padStart(2, '0') !== filters.month) return false;
  if (filters.day && filters.day !== 'All' && String(dt.getDate()).padStart(2, '0') !== filters.day) return false;
  return true;
}

function filterHistory(history, filters) {
  return (history || []).filter((row) => matchesFilters(row, filters));
}

function chartErrorFromRow(row) {
  const label = normalizeErrorLabel(mapRowErrorType(row));
  return label && CHART_ERROR_TYPES.includes(label) ? label : null;
}

function aggregateFromHistory(allHistory, filters) {
  const dailyMap = {};
  const errorCounts = Object.fromEntries(CHART_ERROR_TYPES.map((t) => [t, 0]));
  const errorVolume = Object.fromEntries(CHART_ERROR_TYPES.map((t) => [t, 0]));
  const hourlyMap = Array.from({ length: 24 }, () => ({}));
  const dayMap = Array.from({ length: 7 }, () => ({}));
  const transitionCounts = {};

  for (const { history } of allHistory) {
    const sorted = filterHistory(history, filters).sort(
      (a, b) => new Date(a.datetime_gride) - new Date(b.datetime_gride),
    );

    for (let i = 1; i < sorted.length; i++) {
      const prev = sorted[i - 1].risk_label;
      const curr = sorted[i].risk_label;
      if (prev && curr && ['Safe', 'Risk', 'Dangerous'].includes(prev) && ['Safe', 'Risk', 'Dangerous'].includes(curr)) {
        const key = `${prev}->${curr}`;
        transitionCounts[key] = transitionCounts[key] || { from: prev, to: curr, count: 0 };
        transitionCounts[key].count += 1;
      }
    }

    for (const row of sorted) {
      const dateKey = row.datetime_gride?.slice(0, 10) ?? 'unknown';
      dailyMap[dateKey] = (dailyMap[dateKey] || 0) + (row.r_sent_per_ip || 0);

      if (row.error_flag === 1) {
        const err = chartErrorFromRow(row);
        if (err) {
          errorCounts[err] = (errorCounts[err] || 0) + 1;
          errorVolume[err] = (errorVolume[err] || 0) + (row.lost_volume || row.r_sent_per_ip || 0);
        }
        const h = row.hour ?? new Date(row.datetime_gride).getHours();
        const d = row.day_of_week ?? new Date(row.datetime_gride).getDay();
        if (err && h >= 0 && h < 24) {
          hourlyMap[h][err] = (hourlyMap[h][err] || 0) + 1;
        }
        if (err && d >= 0 && d < 7) {
          dayMap[d][err] = (dayMap[d][err] || 0) + 1;
        }
      }
    }
  }

  const dailyVolume = Object.entries(dailyMap)
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-14)
    .map(([date, volume]) => ({
      date: date.slice(5),
      volume: Math.round(volume),
    }));

  const errors = CHART_ERROR_TYPES.map((type) => ({
    type,
    count: errorCounts[type] || 0,
    volume: Math.round(errorVolume[type] || 0),
  })).filter((e) => e.count > 0);

  const hourlyHeatmap = Array.from({ length: 24 }, (_, hour) => {
    const row = { hour };
    HEATMAP_ERRORS.forEach((t) => {
      row[t] = hourlyMap[hour][t] || 0;
    });
    return row;
  });

  const dayHeatmap = DAYS.map((day, i) => {
    const row = { day };
    HEATMAP_ERRORS.forEach((t) => {
      row[t] = dayMap[i][t] || 0;
    });
    return row;
  });

  return {
    dailyVolume: dailyVolume.length ? dailyVolume : mockDailyVolume,
    errors: errors.length ? errors : mockErrors,
    transitions: Object.values(transitionCounts).length
      ? Object.values(transitionCounts)
      : mockTransitions,
    hourlyHeatmap,
    dayHeatmap,
  };
}

function buildIpRows(ipList, kpiResults, errorResults, historyResults) {
  return ipList.map((ip, idx) => {
    const kpi = kpiResults[idx];
    const errors = errorResults[idx];
    const history = historyResults[idx]?.history ?? [];
    const latestError = errors?.errors?.[errors.errors.length - 1];
    const rawError = latestError?.error_type;
    const lastError =
      rawError && rawError !== 'No error' ? normalizeErrorLabel(rawError) || rawError : null;

    const maxSent = history.length
      ? Math.max(...history.map((r) => Number(r.sent_per_ip) || 0))
      : 0;

    const latestHistory = history.length
      ? [...history].sort(
          (a, b) => new Date(a.datetime_gride) - new Date(b.datetime_gride),
        ).at(-1)
      : null;

    return {
      ip,
      entity: kpi?.entity ?? latestHistory?.entity ?? '—',
      server: kpi?.server ?? latestHistory?.server ?? '—',
      last_datetime: latestError?.datetime ?? latestHistory?.datetime_gride,
      datetime: latestError?.datetime ?? latestHistory?.datetime_gride,
      datetime_gride: latestHistory?.datetime_gride,
      risk_label: kpi?.lifecycle_status ?? latestHistory?.risk_label ?? 'Safe',
      last_error: lastError,
      detected_error: lastError,
      last_r_sent: kpi?.avg_r_sent ?? 0,
      r_sent_per_ip: kpi?.avg_r_sent ?? 0,
      sent_per_ip: maxSent,
      sent_ratio: (kpi?.avg_sent_ratio ?? 0) * (kpi?.avg_sent_ratio <= 1 ? 100 : 1),
      growth_rate: (kpi?.avg_growth_rate ?? 0) * 100,
    };
  });
}

function recomputeKpisFromRows(rows) {
  const uniqueIps = new Set(rows.map((r) => r.ip));
  const safe = rows.filter((r) => r.risk_label === 'Safe').length;
  const risk = rows.filter((r) => r.risk_label === 'Risk').length;
  const dangerous = rows.filter((r) => r.risk_label === 'Dangerous').length;
  const blocked = rows.filter((r) => r.risk_label === 'Blocked').length;

  const avgR = rows.length
    ? rows.reduce((s, r) => s + (r.last_r_sent || 0), 0) / rows.length
    : 0;
  const avgRatio = rows.length
    ? rows.reduce((s, r) => s + (r.sent_ratio || 0), 0) / rows.length
    : 0;

  return {
    total_ips: uniqueIps.size || rows.length,
    safe_ips: safe,
    risk_ips: risk,
    dangerous_ips: dangerous,
    blocked_ips: blocked,
    avg_r_sent: Math.round(avgR * 100) / 100,
    avg_sent_ratio: avgRatio,
    global_error_rate: Math.max(0, 100 - avgRatio),
    trends: {
      total_ips: 2.4,
      safe_ips: 1.8,
      risk_ips: -3.2,
      dangerous_ips: 5.1,
      blocked_ips: 0.8,
      avg_r_sent: 4.2,
      avg_sent_ratio: -1.1,
      global_error_rate: 0.6,
    },
  };
}

function normalizeKpis(data) {
  if (!data || data.error) return null;
  return {
    total_ips: data.total_ips ?? 0,
    safe_ips: data.safe_ips ?? 0,
    risk_ips: data.risk_ips ?? 0,
    dangerous_ips: data.dangerous_ips ?? 0,
    blocked_ips: data.blocked_ips ?? 0,
    avg_r_sent: data.avg_r_sent ?? 0,
    avg_sent_ratio: (data.avg_sent_ratio ?? 0) * (data.avg_sent_ratio <= 1 ? 100 : 1),
    global_error_rate: (data.global_error_rate ?? 0) * (data.global_error_rate <= 1 ? 100 : 1),
    trends: {
      total_ips: 2.4,
      safe_ips: 1.8,
      risk_ips: -3.2,
      dangerous_ips: 5.1,
      blocked_ips: 0.8,
      avg_r_sent: 4.2,
      avg_sent_ratio: -1.1,
      global_error_rate: 0.6,
    },
  };
}

function filterMockData(filters) {
  const filtered = mockIPs.filter((r) => matchesFilters(r, filters));
  const kpis = recomputeKpisFromRows(filtered.length ? filtered : mockIPs);
  const source = filtered.length ? filtered : mockIPs;

  return {
    kpis,
    dangerousIPs: source
      .filter((r) => r.risk_label === 'Dangerous' || r.risk_label === 'Blocked')
      .sort((a, b) => (b.r_sent_per_ip ?? b.last_r_sent) - (a.r_sent_per_ip ?? a.last_r_sent))
      .slice(0, 10),
    latestIPs: source,
    riskDistribution: [
      { name: 'Safe', value: kpis.safe_ips, color: '#00c9b1' },
      { name: 'Risk', value: kpis.risk_ips, color: '#f59e0b' },
      { name: 'Dangerous', value: kpis.dangerous_ips, color: '#ef4444' },
    ],
  };
}

export function useOverviewData(filters) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [usingMock, setUsingMock] = useState(false);
  const [kpis, setKpis] = useState(null);
  const [riskDistribution, setRiskDistribution] = useState([]);
  const [dailyVolume, setDailyVolume] = useState([]);
  const [errors, setErrors] = useState([]);
  const [transitions, setTransitions] = useState([]);
  const [hourlyHeatmap, setHourlyHeatmap] = useState([]);
  const [dayHeatmap, setDayHeatmap] = useState([]);
  const [dangerousIPs, setDangerousIPs] = useState([]);
  const [latestIPs, setLatestIPs] = useState([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      let kpiData = await fetchOverviewKpis(filters);
      let ipsData = await fetchAllIps(filters);
      let mock = false;

      if (kpiData?.error || !ipsData?.ips?.length) {
        mock = true;
      }

      if (mock) {
        setUsingMock(true);
        const mockResult = filterMockData(filters);
        setKpis(mockResult.kpis);
        setRiskDistribution(mockResult.riskDistribution);
        setDailyVolume(mockDailyVolume);
        setErrors(mockErrors);
        setTransitions(mockTransitions);
        setHourlyHeatmap(mockHourlyHeatmap);
        setDayHeatmap(mockDayHeatmap);
        setDangerousIPs(mockResult.dangerousIPs);
        setLatestIPs(mockResult.latestIPs);
        setLoading(false);
        return;
      }

      setUsingMock(false);
      const ips = ipsData.ips.slice(0, 80);
      const [kpiResults, errorResults, historyResults] = await Promise.all([
        Promise.all(ips.map((ip) => fetchIpKpis(ip, filters).catch(() => null))),
        Promise.all(ips.map((ip) => fetchIpErrors(ip, filters).catch(() => null))),
        Promise.all(ips.map((ip) => fetchIpHistory(ip, filters).catch(() => null))),
      ]);

      const rows = buildIpRows(ips, kpiResults, errorResults, historyResults).filter((r) =>
        matchesFilters(r, filters),
      );

      const aggregated = aggregateFromHistory(
        historyResults
          .map((h, i) => ({ ip: ips[i], history: h?.history ?? [] }))
          .filter((h) => h.history.length),
        filters,
      );

      const hasActiveFilters =
        filters.entity !== 'All' ||
        filters.server !== 'All' ||
        filters.year !== 'All' ||
        filters.month !== 'All' ||
        filters.day !== 'All' ||
        filters.sentVolumeMin > 0 ||
        filters.sentVolumeMax < SENT_VOLUME_MAX;

      const normalized = hasActiveFilters
        ? recomputeKpisFromRows(rows)
        : normalizeKpis(kpiData) ?? recomputeKpisFromRows(rows);

      setKpis(normalized);
      setRiskDistribution([
        { name: 'Safe', value: normalized.safe_ips, color: '#00c9b1' },
        { name: 'Risk', value: normalized.risk_ips, color: '#f59e0b' },
        { name: 'Dangerous', value: normalized.dangerous_ips, color: '#ef4444' },
      ]);
      setDailyVolume(aggregated.dailyVolume);
      setErrors(aggregated.errors);
      setTransitions(aggregated.transitions);
      setHourlyHeatmap(aggregated.hourlyHeatmap);
      setDayHeatmap(aggregated.dayHeatmap);

      const dangerous = rows
        .filter((r) => r.risk_label === 'Dangerous' || r.risk_label === 'Blocked')
        .sort((a, b) => b.r_sent_per_ip - a.r_sent_per_ip)
        .slice(0, 10);
      setDangerousIPs(dangerous.length ? dangerous : mockIPs.slice(0, 10));
      setLatestIPs(rows.length ? rows : mockIPs);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data');
      setUsingMock(true);
      const mockResult = filterMockData(filters);
      setKpis(mockResult.kpis);
      setRiskDistribution(mockResult.riskDistribution);
      setDailyVolume(mockDailyVolume);
      setErrors(mockErrors);
      setTransitions(mockTransitions);
      setHourlyHeatmap(mockHourlyHeatmap);
      setDayHeatmap(mockDayHeatmap);
      setDangerousIPs(mockResult.dangerousIPs);
      setLatestIPs(mockResult.latestIPs);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    load();
  }, [load]);

  return {
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
    retry: load,
  };
}
