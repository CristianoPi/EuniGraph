"use client";

import Link from "next/link";
import type { Route } from "next";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { DetailList } from "@/components/ui/detail-list";
import { Panel } from "@/components/ui/panel";
import { useOrganization, useOrganizations, useResearchers } from "@/hooks/use-catalog";

function researcherRoute(id: string): Route {
  return `/entities/researchers/${id}` as Route;
}

function organizationRoute(id: string): Route {
  return `/entities/organizations/${id}` as Route;
}

function researchersForOrganizationRoute(id: string): Route {
  return `/entities/researchers?primary_organization_id=${id}` as Route;
}

function childOrganizationsRoute(id: string): Route {
  return `/entities/organizations?parent_organization_id=${id}` as Route;
}

export function OrganizationDetail({ id }: { id: string }) {
  const organization = useOrganization(id);
  const primaryResearchers = useResearchers({
    primary_organization_id: id,
    limit: 20,
  });
  const children = useOrganizations({
    parent_organization_id: id,
    limit: 20,
  });

  if (organization.isLoading) {
    return <LoadingState label="Loading organization detail..." />;
  }

  if (organization.isError) {
    return <ErrorState message="The organization detail could not be loaded from the backend." />;
  }

  if (!organization.data) {
    return (
      <EmptyState
        title="Organization not available"
        message="The requested organization did not return a usable payload."
      />
    );
  }

  return (
    <div className="space-y-5">
      <Panel
        title={organization.data.name}
        description="Identifiers, hierarchy and linked people."
      >
        <DetailList
          items={[
            { label: "Type", value: organization.data.organization_type ?? "n/a" },
            { label: "Country", value: organization.data.country_code ?? "n/a" },
            { label: "City", value: organization.data.city ?? "n/a" },
            {
              label: "Website",
              value: organization.data.website ? (
                <a
                  href={organization.data.website}
                  target="_blank"
                  rel="noreferrer"
                  className="text-ink underline decoration-amber-400 underline-offset-4"
                >
                  {organization.data.website}
                </a>
              ) : (
                "n/a"
              ),
            },
            { label: "ROR id", value: organization.data.ror_id ?? "n/a" },
            { label: "OpenAIRE id", value: organization.data.openaire_id ?? "n/a" },
            { label: "Normalized name", value: organization.data.normalized_name },
            {
              label: "Parent organization id",
              value: organization.data.parent_organization_id ?? "n/a",
            },
          ]}
        />
      </Panel>

      <div className="grid gap-5 xl:grid-cols-2">
        <Panel
          title="Primary researchers"
          description="Researchers linked as primary."
        >
          {(primaryResearchers.data ?? []).length > 0 ? (
            <div className="space-y-3">
              {primaryResearchers.data?.map((item) => (
                <Link
                  key={item.id}
                  href={researcherRoute(item.id)}
                  className="block rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-4 text-sm transition hover:border-zinc-300 hover:shadow-panel"
                >
                  <p className="font-semibold text-ink">{item.display_name ?? item.full_name}</p>
                  <p className="mt-1 text-zinc-500">{item.orcid ?? "ORCID n/a"}</p>
                </Link>
              ))}
            </div>
          ) : primaryResearchers.isLoading ? (
            <LoadingState label="Loading linked researchers..." />
          ) : primaryResearchers.isError ? (
            <ErrorState message="Primary researchers could not be loaded." />
          ) : (
            <EmptyState
              title="No primary researchers"
              message="No researcher currently uses this organization as primary organization."
            />
          )}
          <Link
            href={researchersForOrganizationRoute(id)}
            className="mt-4 inline-flex rounded-full border border-[color:var(--border)] bg-white px-4 py-2 text-sm font-semibold text-zinc-700 hover:border-zinc-300"
          >
            Open filtered researchers
          </Link>
        </Panel>

        <Panel
          title="Child organizations"
          description="Direct hierarchy children."
        >
          {(children.data ?? []).length > 0 ? (
            <div className="space-y-3">
              {children.data?.map((item) => (
                <Link
                  key={item.id}
                  href={organizationRoute(item.id)}
                  className="block rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-4 text-sm transition hover:border-zinc-300 hover:shadow-panel"
                >
                  <p className="font-semibold text-ink">{item.name}</p>
                  <p className="mt-1 text-zinc-500">{item.organization_type ?? "Type n/a"}</p>
                </Link>
              ))}
            </div>
          ) : children.isLoading ? (
            <LoadingState label="Loading child organizations..." />
          ) : children.isError ? (
            <ErrorState message="Child organizations could not be loaded." />
          ) : (
            <EmptyState
              title="No child organizations"
              message="This organization does not currently expose child organizations."
            />
          )}
          <Link
            href={childOrganizationsRoute(id)}
            className="mt-4 inline-flex rounded-full border border-[color:var(--border)] bg-white px-4 py-2 text-sm font-semibold text-zinc-700 hover:border-zinc-300"
          >
            Open filtered organizations
          </Link>
        </Panel>
      </div>
    </div>
  );
}
