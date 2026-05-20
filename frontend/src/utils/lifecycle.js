const ERROR_PRIORITY = [
  ['spf_error', 'SPF'],
  ['dkim_error', 'DKIM'],
  ['netblock_error', 'Netblock'],
];

export function deriveErrorType(row) {
  for (const [field, label] of ERROR_PRIORITY) {
    if (row[field] === 1) return label;
  }
  return 'No error';
}

export function successRatio(row) {
  const sent = Number(row.sent_per_ip) || 0;
  const rsent = Number(row.r_sent_per_ip) || 0;
  return sent > 0 ? rsent / sent : 0;
}

export function parseDatetime(value) {
  if (!value) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

export function normalizeHistoryRow(row) {
  const dt = parseDatetime(row.datetime_gride);
  return {
    ...row,
    datetime: row.datetime_gride,
    datetimeMs: dt?.getTime() ?? 0,
    errorType: deriveErrorType(row),
    successRatio: successRatio(row),
    riskLevel: row.risk_label_encoded ?? riskLabelToLevel(row.risk_label),
  };
}

export function riskLabelToLevel(label) {
  if (label === 'Safe') return 0;
  if (label === 'Risk') return 1;
  if (label === 'Dangerous') return 2;
  return 0;
}

export function sortHistory(rows) {
  return [...rows].sort((a, b) => a.datetimeMs - b.datetimeMs);
}

export function applyLifecycleFilters(rows, filters) {
  let result = rows;

  if (filters.server && filters.server !== 'All') {
    result = result.filter((r) => r.server === filters.server);
  }
  if (filters.entity && filters.entity !== 'All') {
    result = result.filter((r) => r.entity === filters.entity);
  }
  if (filters.year && filters.year !== 'All') {
    result = result.filter((r) => {
      const d = parseDatetime(r.datetime);
      return d && String(d.getFullYear()) === String(filters.year);
    });
  }
  if (filters.month && filters.month !== 'All') {
    result = result.filter((r) => {
      const d = parseDatetime(r.datetime);
      return d && String(d.getMonth() + 1) === String(filters.month);
    });
  }
  if (filters.day && filters.day !== 'All') {
    result = result.filter((r) => {
      const d = parseDatetime(r.datetime);
      return d && String(d.getDate()) === String(filters.day);
    });
  }
  if (filters.dateFrom) {
    const from = new Date(filters.dateFrom).getTime();
    result = result.filter((r) => r.datetimeMs >= from);
  }
  if (filters.dateTo) {
    const to = new Date(filters.dateTo);
    to.setHours(23, 59, 59, 999);
    result = result.filter((r) => r.datetimeMs <= to.getTime());
  }

  return result;
}

export function uniqueOptions(rows, key) {
  const values = new Set(rows.map((r) => r[key]).filter(Boolean));
  return ['All', ...[...values].sort()];
}

export function buildFilterOptions(history) {
  const years = new Set();
  const months = new Set();
  const days = new Set();

  history.forEach((row) => {
    const d = parseDatetime(row.datetime);
    if (!d) return;
    years.add(String(d.getFullYear()));
    months.add(String(d.getMonth() + 1));
    days.add(String(d.getDate()));
  });

  return {
    servers: uniqueOptions(history, 'server'),
    entities: uniqueOptions(history, 'entity'),
    years: ['All', ...[...years].sort()],
    months: ['All', ...[...months].sort((a, b) => Number(a) - Number(b))],
    days: ['All', ...[...days].sort((a, b) => Number(a) - Number(b))],
  };
}

function statFirst(rows, pick) {
  const vals = rows.map(pick).filter((v) => v != null && v !== '');
  return vals.length ? vals[0] : '—';
}

function statLast(rows, pick) {
  const vals = rows.map(pick).filter((v) => v != null && v !== '');
  return vals.length ? vals[vals.length - 1] : '—';
}

function statMin(rows, pick, numeric = false) {
  const vals = rows.map(pick).filter((v) => v != null && !Number.isNaN(v));
  if (!vals.length) return '—';
  if (numeric) return Math.min(...vals.map(Number));
  return vals.reduce((a, b) => (a < b ? a : b));
}

function statMax(rows, pick, numeric = false) {
  const vals = rows.map(pick).filter((v) => v != null && !Number.isNaN(v));
  if (!vals.length) return '—';
  if (numeric) return Math.max(...vals.map(Number));
  return vals.reduce((a, b) => (a > b ? a : b));
}

export function buildLifecycleSummary(rows) {
  if (!rows.length) return { metrics: [], extras: [] };

  const metrics = [
    {
      key: 'datetime',
      label: 'Datetime',
      first: statFirst(rows, (r) => r.datetime),
      last: statLast(rows, (r) => r.datetime),
      min: statMin(rows, (r) => r.datetime),
      max: statMax(rows, (r) => r.datetime),
      format: 'datetime',
    },
    {
      key: 'sent',
      label: 'Sent',
      first: statFirst(rows, (r) => r.sent_per_ip),
      last: statLast(rows, (r) => r.sent_per_ip),
      min: statMin(rows, (r) => r.sent_per_ip, true),
      max: statMax(rows, (r) => r.sent_per_ip, true),
      format: 'number',
    },
    {
      key: 'rsent',
      label: 'R_Sent',
      first: statFirst(rows, (r) => r.r_sent_per_ip),
      last: statLast(rows, (r) => r.r_sent_per_ip),
      min: statMin(rows, (r) => r.r_sent_per_ip, true),
      max: statMax(rows, (r) => r.r_sent_per_ip, true),
      format: 'number',
    },
    {
      key: 'ratio',
      label: 'Success Ratio',
      first: statFirst(rows, (r) => r.successRatio),
      last: statLast(rows, (r) => r.successRatio),
      min: statMin(rows, (r) => r.successRatio, true),
      max: statMax(rows, (r) => r.successRatio, true),
      format: 'ratio',
    },
    {
      key: 'error',
      label: 'Error Type',
      first: statFirst(rows, (r) => r.errorType),
      last: statLast(rows, (r) => r.errorType),
      min: '—',
      max: '—',
      format: 'text',
    },
    {
      key: 'risk',
      label: 'Risk Label',
      first: statFirst(rows, (r) => r.risk_label),
      last: statLast(rows, (r) => r.risk_label),
      min: '—',
      max: '—',
      format: 'risk',
    },
  ];

  const safeRows = [...rows].reverse().find((r) => r.risk_label === 'Safe');
  const errorRows = [...rows].reverse().filter((r) => r.error_flag === 1);

  const extras = [
    {
      key: 'lastSafe',
      label: 'Last Safe Activity',
      first: safeRows?.datetime ?? '—',
      last: '—',
      min: '—',
      max: '—',
      format: 'datetime',
    },
    {
      key: 'lastError',
      label: 'Last Error Detected',
      first: errorRows[0]?.datetime ?? '—',
      last: errorRows[0]?.errorType ?? '—',
      min: '—',
      max: '—',
      format: 'text',
    },
  ];

  return { metrics, extras };
}

export function buildChartSeries(history) {
  let cumulative = 0;
  return history.map((row) => {
    cumulative += Number(row.r_sent_per_ip) || 0;
    return {
      datetime: row.datetime,
      label: formatChartLabel(row.datetime),
      sent: Number(row.sent_per_ip) || 0,
      rSent: Number(row.r_sent_per_ip) || 0,
      cumulativeRSent: cumulative,
      growthRate: Number(row.growth_rate) || 0,
      timeGap: Number(row.time_gap_min) || 0,
      sentRatio: Number(row.sent_ratio) || 0,
      riskLevel: row.riskLevel,
      riskLabel: row.risk_label,
    };
  });
}

function formatChartLabel(dt) {
  const d = parseDatetime(dt);
  if (!d) return String(dt);
  return d.toLocaleString(undefined, { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

export function buildErrorBarData(errors) {
  const counts = {};
  errors.forEach((e) => {
    const type = e.error_type || 'Unknown';
    if (type === 'No error') return;
    counts[type] = (counts[type] || 0) + 1;
  });
  return Object.entries(counts)
    .map(([type, count]) => ({ type, count }))
    .sort((a, b) => b.count - a.count);
}

function pearson(x, y) {
  const n = x.length;
  if (n < 2) return 0;
  const mx = x.reduce((a, b) => a + b, 0) / n;
  const my = y.reduce((a, b) => a + b, 0) / n;
  let num = 0;
  let dx = 0;
  let dy = 0;
  for (let i = 0; i < n; i += 1) {
    const vx = x[i] - mx;
    const vy = y[i] - my;
    num += vx * vy;
    dx += vx * vx;
    dy += vy * vy;
  }
  const den = Math.sqrt(dx * dy);
  return den === 0 ? 0 : num / den;
}

const CORRELATION_FEATURES = [
  { key: 'sent', label: 'Sent', pick: (r) => Number(r.sent_per_ip) || 0 },
  { key: 'rsent', label: 'R_Sent', pick: (r) => Number(r.r_sent_per_ip) || 0 },
  { key: 'ratio', label: 'Sent Ratio', pick: (r) => Number(r.sent_ratio) || 0 },
  { key: 'growth', label: 'Growth Rate', pick: (r) => Number(r.growth_rate) || 0 },
  { key: 'drops', label: 'Drops/Day', pick: (r) => Number(r.drops_per_day) || 0 },
  { key: 'error', label: 'Error Type', pick: (r) => encodeError(r) },
  { key: 'risk', label: 'Risk Label', pick: (r) => Number(r.risk_label_encoded) || 0 },
];

function encodeError(row) {
  if (row.netblock_error === 1) return 3;
  if (row.dkim_error === 1) return 2;
  if (row.spf_error === 1) return 1;
  return 0;
}

export function buildCorrelationMatrix(history) {
  const features = CORRELATION_FEATURES;
  const vectors = features.map((f) => history.map(f.pick));

  return features.map((rowF, i) => ({
    feature: rowF.label,
    cells: features.map((colF, j) => {
      const value = i === j ? 1 : pearson(vectors[i], vectors[j]);
      return { feature: colF.label, value: Number(value.toFixed(2)) };
    }),
  }));
}

export function correlationColor(value) {
  if (value >= 0.01) {
    const t = Math.min(1, value);
    const r = Math.round(255 - t * 155);
    const g = Math.round(255 - t * 155);
    const b = 255;
    return `rgb(${r}, ${g}, ${b})`;
  }
  if (value <= -0.01) {
    const t = Math.min(1, Math.abs(value));
    const r = 255;
    const g = Math.round(255 - t * 155);
    const b = Math.round(255 - t * 155);
    return `rgb(${r}, ${g}, ${b})`;
  }
  return '#ffffff';
}

export const defaultLifecycleFilters = {
  ip: '',
  server: 'All',
  entity: 'All',
  year: 'All',
  month: 'All',
  day: 'All',
  dateFrom: '',
  dateTo: '',
};
