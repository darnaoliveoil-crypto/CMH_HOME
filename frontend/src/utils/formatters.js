export function formatNumber(value, decimals = 0) {
  if (value == null || Number.isNaN(value)) return '—';
  return Number(value).toLocaleString(undefined, {
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals,
  });
}

export function formatPercent(value, decimals = 1) {
  if (value == null || Number.isNaN(value)) return '—';
  const pct = value <= 1 ? value * 100 : value;
  return `${pct.toFixed(decimals)}%`;
}

export function formatTrend(value) {
  if (value == null) return { text: '—', positive: null };
  const positive = value >= 0;
  return {
    text: `${positive ? '+' : ''}${value.toFixed(1)}%`,
    positive,
  };
}

export function formatDatetime(dt) {
  if (!dt) return '—';
  try {
    return new Date(dt).toLocaleString(undefined, {
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return String(dt);
  }
}
