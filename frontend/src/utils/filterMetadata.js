import { fetchAllIps, fetchIpHistory, fetchIpKpis } from '../api/client';
import { mockIPs } from '../mockData';

export const SENT_VOLUME_MAX = 20000;

export const EMPTY_FILTER_OPTIONS = {
  entities: ['All'],
  servers: ['All'],
  years: ['All'],
  months: ['All'],
  days: ['All'],
};

function collectFromRows(rows, entities, servers, years, months, days) {
  rows.forEach((row) => {
    if (row.entity) entities.add(row.entity);
    if (row.server) servers.add(row.server);

    const dt = new Date(row.datetime_gride || row.datetime || row.last_datetime);
    if (!Number.isNaN(dt.getTime())) {
      years.add(String(dt.getFullYear()));
      months.add(String(dt.getMonth() + 1).padStart(2, '0'));
      days.add(String(dt.getDate()).padStart(2, '0'));
    }
  });
}

function sortOptions(set, numeric = false) {
  const items = [...set].filter((v) => v !== 'All');
  if (numeric) {
    return ['All', ...items.sort((a, b) => Number(a) - Number(b))];
  }
  return ['All', ...items.sort()];
}

export function buildFilterOptionsFromSets(entities, servers, years, months, days) {
  return {
    entities: sortOptions(entities),
    servers: sortOptions(servers),
    years: sortOptions(years),
    months: sortOptions(months, true),
    days: sortOptions(days, true),
  };
}

export function buildFilterOptionsFromMock() {
  const entities = new Set(['All']);
  const servers = new Set(['All']);
  const years = new Set(['All']);
  const months = new Set(['All']);
  const days = new Set(['All']);

  collectFromRows(mockIPs, entities, servers, years, months, days);
  return buildFilterOptionsFromSets(entities, servers, years, months, days);
}

const BATCH_SIZE = 25;

export async function fetchFilterOptionsFromApi() {
  const ipsData = await fetchAllIps();
  const ips = ipsData?.ips ?? [];
  if (!ips.length) return null;

  const entities = new Set(['All']);
  const servers = new Set(['All']);
  const years = new Set(['All']);
  const months = new Set(['All']);
  const days = new Set(['All']);

  for (let i = 0; i < ips.length; i += BATCH_SIZE) {
    const batch = ips.slice(i, i + BATCH_SIZE);
    const [kpiResults, historyResults] = await Promise.all([
      Promise.all(batch.map((ip) => fetchIpKpis(ip).catch(() => null))),
      Promise.all(batch.map((ip) => fetchIpHistory(ip).catch(() => null))),
    ]);

    kpiResults.forEach((kpi) => {
      if (kpi?.entity) entities.add(kpi.entity);
      if (kpi?.server) servers.add(kpi.server);
    });

    historyResults.forEach((result) => {
      collectFromRows(result?.history ?? [], entities, servers, years, months, days);
    });
  }

  return buildFilterOptionsFromSets(entities, servers, years, months, days);
}
