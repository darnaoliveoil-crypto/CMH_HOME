import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 8000,
});

export function buildQueryParams(filters) {
  const params = {};
  if (filters.entity && filters.entity !== 'All') params.entity = filters.entity;
  if (filters.year && filters.year !== 'All') params.year = filters.year;
  if (filters.month && filters.month !== 'All') params.month = filters.month;
  if (filters.day && filters.day !== 'All') params.day = filters.day;
  return params;
}

export async function apiFetch(path, filters = {}, options = {}) {
  const params = buildQueryParams(filters);
  const client = options.timeout ? axios.create({ baseURL: API_BASE, timeout: options.timeout }) : api;
  const { data } = await client.get(path, { params });
  return data;
}

export async function fetchOverviewKpis(filters) {
  return apiFetch('/overview/kpis', filters);
}

export async function fetchAllIps(filters) {
  return apiFetch('/lifecycle/ips', filters);
}

export async function fetchIpKpis(ip, filters) {
  return apiFetch(`/lifecycle/${encodeURIComponent(ip)}/kpis`, filters);
}

export async function fetchIpErrors(ip, filters) {
  return apiFetch(`/lifecycle/${encodeURIComponent(ip)}/errors`, filters);
}

export async function fetchIpHistory(ip, filters) {
  return apiFetch(`/lifecycle/${encodeURIComponent(ip)}/history`, filters);
}
