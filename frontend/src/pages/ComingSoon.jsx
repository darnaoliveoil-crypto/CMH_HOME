import { Construction } from 'lucide-react';
import { useLocale } from '../context/LocaleContext';

const pageMeta = {
  upload: { titleKey: 'comingSoon.uploadTitle', descKey: 'comingSoon.uploadDesc' },
  prediction: { titleKey: 'comingSoon.predictionTitle', descKey: 'comingSoon.predictionDesc' },
  decision: { titleKey: 'comingSoon.decisionTitle', descKey: 'comingSoon.decisionDesc' },
  lifecycle: { titleKey: 'comingSoon.lifecycleTitle', descKey: 'comingSoon.lifecycleDesc' },
};

export default function ComingSoon({ pageKey = 'upload' }) {
  const { t } = useLocale();
  const meta = pageMeta[pageKey] ?? pageMeta.upload;

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#00c9b1]/15 border border-[#00c9b1]/30 mb-6">
        <Construction className="h-8 w-8 text-[#00c9b1]" />
      </div>
      <h2 className="text-2xl font-bold text-dash mb-2">{t(meta.titleKey)}</h2>
      <p className="text-dash-muted max-w-md text-sm leading-relaxed">{t(meta.descKey)}</p>
      <span className="mt-6 inline-flex items-center px-4 py-1.5 rounded-full text-xs font-medium glass-card text-dash-faint">
        {t('common.comingSoon')}
      </span>
    </div>
  );
}
