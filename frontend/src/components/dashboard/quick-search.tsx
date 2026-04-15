"use client";

import Link from "next/link";
import { useDeferredValue, useState } from "react";
import type { Route } from "next";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Panel } from "@/components/ui/panel";
import { useQuickSearch } from "@/hooks/use-dashboard";

function routeForPublication(id: string): Route {
  return `/entities/publications/${id}` as Route;
}

function routeForResearcher(id: string): Route {
  return `/entities/researchers/${id}` as Route;
}

function routeForOrganization(id: string): Route {
  return `/entities/organizations/${id}` as Route;
}

export function QuickSearch() {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const [publications, researchers, organizations] = useQuickSearch(deferredQuery);

  const enabled = deferredQuery.trim().length >= 2;
  const isLoading = publications.isLoading || researchers.isLoading || organizations.isLoading;
  const isError = publications.isError || researchers.isError || organizations.isError;

  return (
    <Panel
      title="Quick search"
      description="One query across the catalog."
    >
      <div className="space-y-5">
        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-[0.22em] text-zinc-500">
            Query
          </span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Title, researcher or organization"
            className="mt-3 w-full rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-zinc-900"
          />
        </label>

        {!enabled ? (
          <EmptyState
            title="Type at least two characters"
            message="Results appear across publications, researchers and organizations."
          />
        ) : isLoading ? (
          <LoadingState label="Searching publications, researchers and organizations..." />
        ) : isError ? (
          <ErrorState message="The quick-search request failed for at least one entity family." />
        ) : (
          <div className="grid gap-5 xl:grid-cols-3">
            <div className="space-y-3">
              <p className="text-sm font-semibold text-ink">Publications</p>
              {(publications.data ?? []).length > 0 ? (
                publications.data?.map((item) => (
                  <Link
                    key={item.id}
                    href={routeForPublication(item.id)}
                    className="block rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm text-zinc-700 transition hover:border-zinc-300 hover:shadow-panel"
                  >
                    <p className="font-semibold text-ink">{item.title}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.18em] text-zinc-500">
                      {item.publication_year ?? "Year n/a"}
                    </p>
                  </Link>
                ))
              ) : (
                <EmptyState
                  title="No publication matches"
                  message="No matches for this query."
                />
              )}
            </div>

            <div className="space-y-3">
              <p className="text-sm font-semibold text-ink">Researchers</p>
              {(researchers.data ?? []).length > 0 ? (
                researchers.data?.map((item) => (
                  <Link
                    key={item.id}
                    href={routeForResearcher(item.id)}
                    className="block rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm text-zinc-700 transition hover:border-zinc-300 hover:shadow-panel"
                  >
                    <p className="font-semibold text-ink">{item.display_name ?? item.full_name}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.18em] text-zinc-500">
                      {item.orcid ?? "ORCID n/a"}
                    </p>
                  </Link>
                ))
              ) : (
                <EmptyState
                  title="No researcher matches"
                  message="No matches for this query."
                />
              )}
            </div>

            <div className="space-y-3">
              <p className="text-sm font-semibold text-ink">Organizations</p>
              {(organizations.data ?? []).length > 0 ? (
                organizations.data?.map((item) => (
                  <Link
                    key={item.id}
                    href={routeForOrganization(item.id)}
                    className="block rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm text-zinc-700 transition hover:border-zinc-300 hover:shadow-panel"
                  >
                    <p className="font-semibold text-ink">{item.name}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.18em] text-zinc-500">
                      {item.organization_type ?? "Type n/a"}
                    </p>
                  </Link>
                ))
              ) : (
                <EmptyState
                  title="No organization matches"
                  message="No matches for this query."
                />
              )}
            </div>
          </div>
        )}
      </div>
    </Panel>
  );
}
