import { NavLink, useLocation } from 'react-router-dom';
import {
  Activity,
  BarChart3,
  CheckCircle,
  Globe,
  Upload,
  Zap,
} from 'lucide-react';
import { useLocale } from '../../context/LocaleContext';
import SidebarFilters from './SidebarFilters';

const navKeys = [
  { to: '/upload', key: 'upload', icon: Upload },
  { to: '/', key: 'overview', icon: Globe, end: true },
  { to: '/lifecycle', key: 'lifecycle', icon: Activity },
  { to: '/prediction', key: 'prediction', icon: BarChart3 },
  { to: '/decision', key: 'decision', icon: CheckCircle },
];

export default function Sidebar() {
  const location = useLocation();
  const { t } = useLocale();
  const showFilters = location.pathname === '/';

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-full w-64 flex-col border-r border-dash bg-[var(--dash-sidebar)]">
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-dash">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600">
          <Zap className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-dash leading-tight">{t('appName')}</p>
          <p className="text-[10px] text-dash-faint">{t('appSubtitle')}</p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {navKeys.map(({ to, key, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
                isActive
                  ? 'bg-blue-600/20 text-blue-500 border border-blue-500/30'
                  : 'text-dash-muted hover:bg-dash-card hover:text-dash border border-transparent'
              }`
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {t(`nav.${key}`)}
          </NavLink>
        ))}
      </nav>

      {showFilters && <SidebarFilters />}

      <div className="px-4 py-4 border-t border-dash mt-auto">
        <p className="text-[10px] text-dash-faint text-center">{t('common.version')}</p>
      </div>
    </aside>
  );
}
