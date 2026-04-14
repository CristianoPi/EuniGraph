"use client";

import { useQueries } from "@tanstack/react-query";
import { useMemo } from "react";

import { listOrganizations, listPublications, listResearchers } from "@/lib/api/catalog";
import { queryKeys } from "@/lib/api/query-keys";

const DASHBOARD_COUNT_LIMIT = 500;

export function useDashboardCounts() {
  const results = useQueries({
    queries: [
      {
        queryKey: queryKeys.publications({ limit: DASHBOARD_COUNT_LIMIT }),
        queryFn: () => listPublications({ limit: DASHBOARD_COUNT_LIMIT }),
      },
      {
        queryKey: queryKeys.researchers({ limit: DASHBOARD_COUNT_LIMIT }),
        queryFn: () => listResearchers({ limit: DASHBOARD_COUNT_LIMIT }),
      },
      {
        queryKey: queryKeys.organizations({ limit: DASHBOARD_COUNT_LIMIT }),
        queryFn: () => listOrganizations({ limit: DASHBOARD_COUNT_LIMIT }),
      },
    ],
  });

  const [publications, researchers, organizations] = results;

  return useMemo(
    () => ({
      isLoading: results.some((result) => result.isLoading),
      isError: results.some((result) => result.isError),
      data:
        publications.data && researchers.data && organizations.data
          ? {
              publications: publications.data.length,
              researchers: researchers.data.length,
              organizations: organizations.data.length,
              limit: DASHBOARD_COUNT_LIMIT,
            }
          : undefined,
    }),
    [organizations.data, publications.data, researchers.data, results],
  );
}

export function useQuickSearch(query: string) {
  const normalizedQuery = query.trim();
  const enabled = normalizedQuery.length >= 2;

  return useQueries({
    queries: [
      {
        queryKey: queryKeys.quickSearch(`publications:${normalizedQuery}`),
        queryFn: () => listPublications({ title: normalizedQuery, limit: 5 }),
        enabled,
      },
      {
        queryKey: queryKeys.quickSearch(`researchers:${normalizedQuery}`),
        queryFn: () => listResearchers({ name: normalizedQuery, limit: 5 }),
        enabled,
      },
      {
        queryKey: queryKeys.quickSearch(`organizations:${normalizedQuery}`),
        queryFn: () => listOrganizations({ name: normalizedQuery, limit: 5 }),
        enabled,
      },
    ],
  });
}
