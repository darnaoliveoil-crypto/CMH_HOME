import { useLocale } from '../../context/LocaleContext';
import { RISK_BADGE_CLASSES } from '../../utils/colors';

export default function RiskBadge({ label }) {
  const { t } = useLocale();
  const cls = RISK_BADGE_CLASSES[label] ?? 'bg-slate-500/15 text-slate-400 border-slate-500/30';
  const text = label ? (t(`risk.${label}`) || label) : '—';
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {text}
    </span>
  );
}
