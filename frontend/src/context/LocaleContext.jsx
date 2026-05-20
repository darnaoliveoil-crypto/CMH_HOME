import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { translations } from '../i18n/translations';

const LocaleContext = createContext(null);

function getNested(obj, path) {
  return path.split('.').reduce((acc, key) => acc?.[key], obj);
}

export function LocaleProvider({ children }) {
  const [locale, setLocale] = useState(() => {
    try {
      return localStorage.getItem('cmh-locale') || 'en';
    } catch {
      return 'en';
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('cmh-locale', locale);
    } catch {
      /* ignore */
    }
    document.documentElement.lang = locale;
    document.documentElement.dir = locale === 'ar' ? 'rtl' : 'ltr';
  }, [locale]);

  const t = useCallback(
    (key, vars) => {
      let str = getNested(translations[locale], key) ?? getNested(translations.en, key) ?? key;
      if (vars) {
        Object.entries(vars).forEach(([k, v]) => {
          str = str.replace(`{${k}}`, String(v));
        });
      }
      return str;
    },
    [locale],
  );

  const value = useMemo(() => ({ locale, setLocale, t }), [locale, t]);

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useLocale() {
  const ctx = useContext(LocaleContext);
  if (!ctx) throw new Error('useLocale must be used within LocaleProvider');
  return ctx;
}
