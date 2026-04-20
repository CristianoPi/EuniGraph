"use client";

import { useQueries } from "@tanstack/react-query";
import { useMemo } from "react";

import {
  countOrganizations,
  countPublications,
  countResearchers,
  listOrganizations,
  listPublications,
  listResearchers,
} from "@/lib/api/catalog";
import { queryKeys } from "@/lib/api/query-keys";

export function useDashboardCounts() {
  const results = useQueries({
    queries: [
      {
        queryKey: queryKeys.dashboardCounts,
        queryFn: () => countPublications(),
      },
      {
        queryKey: [...queryKeys.dashboardCounts, "researchers"],
        queryFn: () => countResearchers(),
      },
      {
        queryKey: [...queryKeys.dashboardCounts, "organizations"],
        queryFn: () => countOrganizations(),
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
              publications: publications.data.count,
              researchers: researchers.data.count,
              organizations: organizations.data.count,
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
