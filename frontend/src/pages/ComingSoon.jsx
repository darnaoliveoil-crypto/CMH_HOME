import { Construction } from 'lucide-react';
import { useLocale } from '../context/LocaleContext';

const PAGE_KEYS = {
  lifecycle: { title: 'comingSoon.lifecycleTitle', desc: 'comingSoon.lifecycleDesc' },
  upload: { title: 'comingSoon.uploadTitle', desc: 'comingSoon.uploadDesc' },
  prediction: { title: 'comingSoon.predictionTitle', desc: 'comingSoon.predictionDesc' },
  decision: { title: 'comingSoon.decisionTitle', desc: 'comingSoon.decisionDesc' },
};

export default function ComingSoon({ pageKey, title, description }) {
  const { t } = useLocale();
  const keys = PAGE_KEYS[pageKey];
  const pageTitle = keys ? t(keys.title) : title;
  const pageDesc = keys ? t(keys.desc) : description ?? t('comingSoon.defaultDesc');

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-600/15 border border-blue-500/30 mb-6">
        <Construction className="h-8 w-8 text-blue-500" />
      </div>
      <h2 className="text-2xl font-bold text-dash mb-2">{pageTitle}</h2>
      <p className="text-dash-muted max-w-md text-sm">{pageDesc}</p>
      <span className="mt-6 inline-flex items-center px-4 py-1.5 rounded-full text-xs font-medium bg-dash-card border border-dash text-dash-faint">
        {t('common.comingSoon')}
      </span>
    </div>
  );
}
