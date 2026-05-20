import { AlertCircle, RefreshCw } from 'lucide-react';
import { useLocale } from '../../context/LocaleContext';

export default function ErrorState({ message, onRetry }) {
  const { t } = useLocale();
  return (
    <div className="flex flex-col items-center justify-center gap-4 p-8 rounded-xl border border-red-500/30 bg-red-500/5">
      <AlertCircle className="w-10 h-10 text-red-500" />
      <p className="text-dash-muted text-sm text-center max-w-md">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          {t('common.retry')}
        </button>
      )}
    </div>
  );
}
