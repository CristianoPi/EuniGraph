"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { Route } from "next";
import { FormEvent, startTransition, useMemo, useState } from "react";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Panel } from "@/components/ui/panel";
import { useOrganizations } from "@/hooks/use-catalog";

function organizationRoute(id: string): Route {
  return `/entities/organizations/${id}` as Route;
}

export function OrganizationsBrowser() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const [name, setName] = useState(searchParams.get("name") ?? "");
  const [organizationType, setOrganizationType] = useState(
    searchParams.get("organization_type") ?? "",
  );

  const filters = useMemo(
    () => ({
      name: searchParams.get("name") ?? undefined,
      organization_type: searchParams.get("organization_type") ?? undefined,
      parent_organization_id: searchParams.get("parent_organization_id") ?? undefined,
      limit: 50,
    }),
    [searchParams],
  );

  const organizations = useOrganizations(filters);
  const activeParent = searchParams.get("parent_organization_id");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const params = new URLSearchParams();
    if (name.trim()) params.set("name", name.trim());
    if (organizationType.trim()) params.set("organization_type", organizationType.trim());
    if (activeParent) params.set("parent_organization_id", activeParent);

    startTransition(() => {
      const query = params.toString();
      router.replace((query ? `${pathname}?${query}` : pathname) as Route);
    });
  }

  function resetFilters() {
    setName("");
    setOrganizationType("");
    startTransition(() => router.replace(pathname as Route));
  }

  return (
    <div className="space-y-5">
      <Panel
        title="Filters"
        description="Name, type or parent organization."
      >
        <form onSubmit={handleSubmit} className="grid gap-4 xl:grid-cols-3">
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Organization name"
            className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
          />
          <input
            value={organizationType}
            onChange={(event) => setOrganizationType(event.target.value)}
            placeholder="Organization type"
            className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
          />
          <div className="rounded-[1rem] border border-dashed border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-500">
            {activeParent
              ? `Parent filter active: ${activeParent}`
              : "Parent organization filtering becomes available from detail views."}
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

      {organizations.isLoading ? (
        <LoadingState label="Loading organizations..." />
      ) : organizations.isError ? (
        <ErrorState message="The organization list could not be loaded from the backend." />
      ) : (organizations.data ?? []).length === 0 ? (
        <EmptyState
          title="No organizations found"
          message="Adjust the filters or clear them to inspect the canonical organization catalog."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {organizations.data?.map((organization) => (
            <Link
              key={organization.id}
              href={organizationRoute(organization.id)}
              className="rounded-[1.35rem] border border-[color:var(--border)] bg-white p-5 shadow-panel transition hover:border-zinc-300"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <h2 className="text-xl font-semibold text-ink">{organization.name}</h2>
                  <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-zinc-900">
                    Open
                  </span>
                </div>
                <div className="flex flex-wrap gap-2 text-sm text-zinc-500">
                  {organization.organization_type ? (
                    <span className="rounded-full bg-zinc-100 px-3 py-1">
                      {organization.organization_type}
                    </span>
                  ) : null}
                  {organization.country_code ? (
                    <span className="rounded-full bg-zinc-100 px-3 py-1">
                      {organization.country_code}
                    </span>
                  ) : null}
                  {organization.city ? (
                    <span className="rounded-full bg-zinc-100 px-3 py-1">{organization.city}</span>
                  ) : null}
                </div>
                <p className="text-sm leading-7 text-zinc-600">
                  Normalized name: {organization.normalized_name}
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
