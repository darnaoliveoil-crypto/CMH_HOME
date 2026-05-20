import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { SENT_VOLUME_MAX, buildFilterOptionsFromMock, fetchFilterOptionsFromApi } from '../utils/filterMetadata';

export const DEFAULT_FILTERS = {
  entity: 'All',
  server: 'All',
  year: 'All',
  month: 'All',
  day: 'All',
  sentVolumeMin: 0,
  sentVolumeMax: SENT_VOLUME_MAX,
};

const FiltersContext = createContext(null);

export function FiltersProvider({ children }) {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [filterOptions, setFilterOptions] = useState({
    entities: ['All'],
    servers: ['All'],
    years: ['All'],
    months: ['All'],
    days: ['All'],
  });
  const [optionsLoading, setOptionsLoading] = useState(true);

  const resetFilters = useCallback(() => setFilters(DEFAULT_FILTERS), []);

  useEffect(() => {
    let cancelled = false;

    async function loadOptions() {
      setOptionsLoading(true);
      try {
        const options = await fetchFilterOptionsFromApi();
        if (!cancelled && options) {
          setFilterOptions(options);
        }
      } catch {
        if (!cancelled) {
          setFilterOptions(buildFilterOptionsFromMock());
        }
      } finally {
        if (!cancelled) setOptionsLoading(false);
      }
    }

    loadOptions();
    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo(
    () => ({ filters, setFilters, resetFilters, filterOptions, optionsLoading }),
    [filters, resetFilters, filterOptions, optionsLoading],
  );

  return <FiltersContext.Provider value={value}>{children}</FiltersContext.Provider>;
}

export function useFilters() {
  const ctx = useContext(FiltersContext);
  if (!ctx) throw new Error('useFilters must be used within FiltersProvider');
  return ctx;
}
