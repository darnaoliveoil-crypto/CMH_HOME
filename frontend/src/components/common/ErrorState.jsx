import { AlertCircle, RefreshCw } from 'lucide-react';
import { useLocale } from '../../context/LocaleContext';

export default function ErrorState({ message, onRetry }) {
  const { t } = useLocale();
  return (
    <div className="flex flex-col items-center justify-center gap-4 p-8 rounded-2xl border border-red-500/30 bg-red-500/10 glass-card">
      <AlertCircle className="w-10 h-10 text-red-500" />
      <p className="text-dash-muted text-sm text-center max-w-md">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="btn-primary flex items-center gap-2 px-4 py-2 text-sm font-medium"
        >
          <RefreshCw className="w-4 h-4" />
          {t('common.retry')}
        </button>
      )}
    </div>
  );
}
