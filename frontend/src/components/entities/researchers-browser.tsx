"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { Route } from "next";
import { FormEvent, startTransition, useMemo, useState } from "react";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Panel } from "@/components/ui/panel";
import { useResearchers } from "@/hooks/use-catalog";

function researcherRoute(id: string): Route {
  return `/entities/researchers/${id}` as Route;
}

export function ResearchersBrowser() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const [name, setName] = useState(searchParams.get("name") ?? "");
  const [orcid, setOrcid] = useState(searchParams.get("orcid") ?? "");

  const filters = useMemo(
    () => ({
      name: searchParams.get("name") ?? undefined,
      orcid: searchParams.get("orcid") ?? undefined,
      primary_organization_id: searchParams.get("primary_organization_id") ?? undefined,
      limit: 50,
    }),
    [searchParams],
  );

  const researchers = useResearchers(filters);
  const activeOrganization = searchParams.get("primary_organization_id");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const params = new URLSearchParams();
    if (name.trim()) params.set("name", name.trim());
    if (orcid.trim()) params.set("orcid", orcid.trim());
    if (activeOrganization) params.set("primary_organization_id", activeOrganization);

    startTransition(() => {
      const query = params.toString();
      router.replace((query ? `${pathname}?${query}` : pathname) as Route);
    });
  }

  function resetFilters() {
    setName("");
    setOrcid("");
    startTransition(() => router.replace(pathname as Route));
  }

  return (
    <div className="space-y-5">
      <Panel
        title="Filters"
        description="Name, ORCID or linked organization."
      >
        <form onSubmit={handleSubmit} className="grid gap-4 xl:grid-cols-3">
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Researcher name"
            className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
          />
          <input
            value={orcid}
            onChange={(event) => setOrcid(event.target.value)}
            placeholder="ORCID"
            className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
          />
          <div className="rounded-[1rem] border border-dashed border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-500">
            {activeOrganization
              ? `Organization filter active: ${activeOrganization}`
              : "Organization filter becomes available from organization detail pages."}
          </div>
          <div className="flex gap-3 xl:col-span-3">
            <button
              type="submit"
              className="rounded-full bg-zinc-900 px-5 py-3 text-sm font-semibold text-white"
            >
              Apply filters
            </button>
            <button
              type="button"
              onClick={resetFilters}
              className="rounded-full border border-[color:var(--border)] bg-white px-5 py-3 text-sm font-semibold text-zinc-700"
            >
              Reset
            </button>
          </div>
        </form>
      </Panel>

      {researchers.isLoading ? (
        <LoadingState label="Loading researchers..." />
      ) : researchers.isError ? (
        <ErrorState message="The researcher list could not be loaded from the backend." />
      ) : (researchers.data ?? []).length === 0 ? (
        <EmptyState
          title="No researchers found"
          message="Adjust the filters or clear them to inspect the canonical researcher catalog."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {researchers.data?.map((researcher) => (
            <Link
              key={researcher.id}
              href={researcherRoute(researcher.id)}
              className="rounded-[1.35rem] border border-[color:var(--border)] bg-white p-5 shadow-panel transition hover:border-zinc-300"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <h2 className="text-xl font-semibold text-ink">
                    {researcher.display_name ?? researcher.full_name}
                  </h2>
                  <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-zinc-900">
                    Open
                  </span>
                </div>
                <div className="flex flex-wrap gap-2 text-sm text-zinc-500">
                  {researcher.orcid ? (
                    <span className="rounded-full bg-zinc-100 px-3 py-1">{researcher.orcid}</span>
                  ) : null}
                  {researcher.email ? (
                    <span className="rounded-full bg-zinc-100 px-3 py-1">{researcher.email}</span>
                  ) : null}
                </div>
                <p className="text-sm leading-7 text-zinc-600">
                  Normalized name: {researcher.normalized_name}
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
