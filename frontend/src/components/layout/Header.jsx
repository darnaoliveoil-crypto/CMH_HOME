import { Bell, LogOut, Moon, Sun, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { LOCALES } from '../../i18n/translations';
import { useAuth } from '../../context/AuthContext';
import { useLocale } from '../../context/LocaleContext';
import { useTheme } from '../../context/ThemeContext';

export default function Header() {
  const { locale, setLocale, t } = useLocale();
  const { theme, setTheme, isDark } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <header className="relative z-20 flex h-14 shrink-0 items-center justify-between border-b border-dash bg-[var(--dash-bg-elevated)]/95 backdrop-blur-sm px-6">
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-semibold text-dash tracking-tight">{t('appName')}</h1>
        <span className="hidden sm:inline text-xs text-dash-faint border-l border-dash pl-3">
          {t('appTagline')}
        </span>
      </div>

      <div className="flex items-center gap-3">
        {/* Language */}
        <div className="flex items-center gap-1.5 rounded-lg border border-dash bg-dash-card px-2 py-1">
          <span className="hidden md:inline text-[10px] text-dash-faint font-medium uppercase">
            {t('header.language')}
          </span>
          <select
            value={locale}
            onChange={(e) => setLocale(e.target.value)}
            className="bg-transparent text-xs text-dash font-medium focus:outline-none cursor-pointer pr-1"
            aria-label={t('header.language')}
          >
            {LOCALES.map(({ code, label, flag }) => (
              <option key={code} value={code}>
                {flag} {label}
              </option>
            ))}
          </select>
        </div>

        {/* Theme */}
        <div
          className="flex items-center rounded-lg border border-dash bg-dash-card p-0.5"
          role="group"
          aria-label={t('header.theme')}
        >
          <button
            type="button"
            onClick={() => setTheme('light')}
            className={`flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
              !isDark ? 'btn-primary text-white' : 'text-dash-muted hover:text-dash'
            }`}
            title={t('header.themeLight')}
          >
            <Sun className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{t('header.themeLight')}</span>
          </button>
          <button
            type="button"
            onClick={() => setTheme('dark')}
            className={`flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
              isDark ? 'btn-primary text-white' : 'text-dash-muted hover:text-dash'
            }`}
            title={t('header.themeDark')}
          >
            <Moon className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{t('header.themeDark')}</span>
          </button>
        </div>

        <button
          type="button"
          className="relative p-2 rounded-lg text-dash-muted hover:text-dash hover:bg-dash-card transition-colors"
          aria-label={t('header.notifications')}
        >
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-red-500" />
        </button>

        <div className="flex items-center gap-3 pl-3 border-l border-dash">
          <div className="hidden sm:block text-right">
            <p className="text-sm font-medium text-dash">{user?.name ?? t('header.userName')}</p>
            <p className="text-xs text-dash-faint">{user?.email ?? t('header.userEmail')}</p>
          </div>
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#00c9b1]/20 border border-[#00c9b1]/40">
            <User className="h-4 w-4 text-[#00c9b1]" />
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="p-2 rounded-lg text-dash-muted hover:text-dash hover:bg-dash-card transition-colors"
            title={t('auth.signOut')}
            aria-label={t('auth.signOut')}
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
