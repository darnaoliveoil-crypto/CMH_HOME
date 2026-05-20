import { CHART_COLORS } from '../../utils/colors';

export const tooltipStyle = {
  background: 'var(--dash-card)',
  border: '1px solid var(--dash-border)',
  borderRadius: 8,
  fontSize: 12,
  color: 'var(--dash-text)',
};

export const axisTick = { fill: CHART_COLORS.text, fontSize: 10 };
export const gridStroke = CHART_COLORS.grid;
