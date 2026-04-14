"use client";

import Link from "next/link";
import type { Route } from "next";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { DetailList } from "@/components/ui/detail-list";
import { Panel } from "@/components/ui/panel";
import { useOrganizationsByIds, useResearcher, useResearcherAffiliations } from "@/hooks/use-catalog";

function organizationRoute(id: string): Route {
  return `/entities/organizations/${id}` as Route;
}

export function ResearcherDetail({ id }: { id: string }) {
  const researcher = useResearcher(id);
  const affiliations = useResearcherAffiliations(id);

  const organizationIds = (affiliations.data ?? []).map((item) => item.organization_id);
  const organizationDetails = useOrganizationsByIds(organizationIds);

  if (researcher.isLoading) {
    return <LoadingState label="Loading researcher detail..." />;
  }

  if (researcher.isError) {
    return <ErrorState message="The researcher detail could not be loaded from the backend." />;
  }

  if (!researcher.data) {
    return (
      <EmptyState
        title="Researcher not available"
        message="The requested researcher did not return a usable payload."
      />
    );
  }

  const organizationNameById = new Map(
    organizationDetails
      .filter((result) => result.data)
      .map((result) => [result.data!.id, result.data!.name]),
  );

  return (
    <div className="space-y-5">
      <Panel
        title={researcher.data.display_name ?? researcher.data.full_name}
        description="Canonical researcher detail with current profile metadata and recorded affiliations."
      >
        <DetailList
          items={[
            { label: "Full name", value: researcher.data.full_name },
            { label: "Normalized name", value: researcher.data.normalized_name },
            { label: "Given name", value: researcher.data.given_name ?? "n/a" },
            { label: "Family name", value: researcher.data.family_name ?? "n/a" },
            { label: "ORCID", value: researcher.data.orcid ?? "n/a" },
            { label: "Email", value: researcher.data.email ?? "n/a" },
            {
              label: "Profile",
              value: researcher.data.profile_url ? (
                <a
                  href={researcher.data.profile_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-pine underline underline-offset-4"
                >
                  {researcher.data.profile_url}
                </a>
              ) : (
                "n/a"
              ),
            },
            {
              label: "Primary organization id",
              value: researcher.data.primary_organization_id ?? "n/a",
            },
          ]}
        />
      </Panel>

      <Panel
        title="Affiliations"
        description="Affiliation data is exposed by the canonical researcher-affiliation relation."
      >
        {(affiliations.data ?? []).length > 0 ? (
          <div className="space-y-3">
            {affiliations.data?.map((item) => (
              <Link
                key={item.id}
                href={organizationRoute(item.organization_id)}
                className="block rounded-[1.25rem] border border-[color:var(--border)] bg-white/70 px-4 py-4 text-sm transition hover:border-pine/40"
              >
                <p className="font-semibold text-ink">
                  {organizationNameById.get(item.organization_id) ?? item.organization_id}
                </p>
                <p className="mt-1 text-slate-600">
                  {item.role_title ?? "Role not specified"}
                  {item.is_primary ? " · primary" : ""}
                </p>
                <p className="mt-1 text-slate-500">
                  {item.start_date ?? "Start n/a"} - {item.end_date ?? "Present"}
                </p>
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No affiliations available"
            message="This researcher does not currently expose canonical affiliation records."
          />
        )}
      </Panel>
    </div>
  );
}
