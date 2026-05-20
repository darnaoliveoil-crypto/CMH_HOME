/** Error types shown in the Most Frequent Errors chart (prototype-aligned). */
export const CHART_ERROR_TYPES = ['SPF', 'DKIM', 'Rate limit', 'Netblock'];

/** Excluded from the errors chart even if present in data. */
export const EXCLUDED_CHART_ERRORS = [
  'Connection closed',
  'Others',
  'Other',
  'No error',
];

export function normalizeErrorLabel(raw) {
  if (!raw) return null;
  const label = String(raw).trim();
  if (EXCLUDED_CHART_ERRORS.includes(label)) return null;

  const lower = label.toLowerCase();
  if (lower.includes('spf')) return 'SPF';
  if (lower.includes('dkim')) return 'DKIM';
  if (lower.includes('netblock')) return 'Netblock';
  if (lower.includes('rate') || lower.includes('limit')) return 'Rate limit';

  if (CHART_ERROR_TYPES.includes(label)) return label;
  return null;
}

export function mapRowErrorType(row) {
  if (row.spf_error === 1) return 'SPF';
  if (row.dkim_error === 1) return 'DKIM';
  if (row.netblock_error === 1) return 'Netblock';
  if (row.error_flag === 1) return 'Rate limit';
  return null;
}

export function matchesErrorFilter(row, errorTypeFilter) {
  if (!errorTypeFilter || errorTypeFilter === 'All') return true;
  const err = normalizeErrorLabel(row.last_error) || mapRowErrorType(row);
  return err === errorTypeFilter;
}
