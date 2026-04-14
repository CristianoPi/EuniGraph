"use client";

import Link from "next/link";
import type { Route } from "next";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { DetailList } from "@/components/ui/detail-list";
import { Panel } from "@/components/ui/panel";
import {
  useOrganizationsByIds,
  usePublication,
  usePublicationAuthors,
  usePublicationEmbedding,
  usePublicationOrganizations,
  useResearchersByIds,
} from "@/hooks/use-catalog";

function researcherRoute(id: string): Route {
  return `/entities/researchers/${id}` as Route;
}

function organizationRoute(id: string): Route {
  return `/entities/organizations/${id}` as Route;
}

export function PublicationDetail({ id }: { id: string }) {
  const publication = usePublication(id);
  const authors = usePublicationAuthors(id);
  const organizations = usePublicationOrganizations(id);
  const embedding = usePublicationEmbedding(id);

  const authorIds = (authors.data ?? []).map((author) => author.researcher_id);
  const organizationIds = (organizations.data ?? []).map((item) => item.organization_id);

  const authorDetails = useResearchersByIds(authorIds);
  const organizationDetails = useOrganizationsByIds(organizationIds);

  if (publication.isLoading) {
    return <LoadingState label="Loading publication detail..." />;
  }

  if (publication.isError) {
    return <ErrorState message="The publication detail could not be loaded from the backend." />;
  }

  if (!publication.data) {
    return (
      <EmptyState
        title="Publication not available"
        message="The requested publication did not return a usable payload."
      />
    );
  }

  const authorNameById = new Map(
    authorDetails
      .filter((result) => result.data)
      .map((result) => [result.data!.id, result.data!.display_name ?? result.data!.full_name]),
  );
  const organizationNameById = new Map(
    organizationDetails
      .filter((result) => result.data)
      .map((result) => [result.data!.id, result.data!.name]),
  );

  return (
    <div className="space-y-5">
      <Panel
        title={publication.data.title}
        description="Canonical publication detail with related authors, organizations and embedding metadata when available."
      >
        <DetailList
          items={[
            { label: "Publication year", value: publication.data.publication_year ?? "n/a" },
            { label: "DOI", value: publication.data.doi ?? "n/a" },
            { label: "OpenAIRE id", value: publication.data.openaire_id ?? "n/a" },
            { label: "Type", value: publication.data.publication_type ?? "n/a" },
            { label: "Language", value: publication.data.language_code ?? "n/a" },
            { label: "Journal", value: publication.data.journal_name ?? "n/a" },
            { label: "Venue", value: publication.data.venue_name ?? "n/a" },
            { label: "Publisher", value: publication.data.publisher ?? "n/a" },
          ]}
        />
        {publication.data.abstract ? (
          <div className="mt-5 rounded-[1.5rem] border border-[color:var(--border)] bg-white/70 p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
              Abstract
            </p>
            <p className="mt-3 text-sm leading-7 text-slate-700">{publication.data.abstract}</p>
          </div>
        ) : null}
      </Panel>

      <div className="grid gap-5 xl:grid-cols-2">
        <Panel
          title="Authors"
          description="Authorship links come from the canonical publication-author relation."
        >
          {(authors.data ?? []).length > 0 ? (
            <div className="space-y-3">
              {authors.data?.map((author) => (
                <Link
                  key={author.id}
                  href={researcherRoute(author.researcher_id)}
                  className="flex items-start justify-between rounded-[1.25rem] border border-[color:var(--border)] bg-white/70 px-4 py-4 text-sm transition hover:border-pine/40"
                >
                  <div>
                    <p className="font-semibold text-ink">
                      {author.author_list_name ??
                        authorNameById.get(author.researcher_id) ??
                        author.researcher_id}
                    </p>
                    <p className="mt-1 text-slate-600">
                      Position {author.author_position}
                      {author.is_corresponding ? " · corresponding" : ""}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No author links available"
              message="This publication does not currently expose canonical authors."
            />
          )}
        </Panel>

        <Panel
          title="Organizations"
          description="Organizations linked to the publication through canonical publication-organization relations."
        >
          {(organizations.data ?? []).length > 0 ? (
            <div className="space-y-3">
              {organizations.data?.map((item) => (
                <Link
                  key={item.id}
                  href={organizationRoute(item.organization_id)}
                  className="block rounded-[1.25rem] border border-[color:var(--border)] bg-white/70 px-4 py-4 text-sm transition hover:border-pine/40"
                >
                  <p className="font-semibold text-ink">
                    {organizationNameById.get(item.organization_id) ?? item.organization_id}
                  </p>
                  <p className="mt-1 text-slate-600">{item.relation_type}</p>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No organization links available"
              message="This publication does not currently expose canonical organizations."
            />
          )}
        </Panel>
      </div>

      <Panel
        title="Semantic enrichment"
        description="Embedding metadata is optional and appears only if the publication has already been embedded."
      >
        {embedding.isLoading ? (
          <LoadingState label="Checking publication embedding metadata..." />
        ) : embedding.isError || !embedding.data ? (
          <EmptyState
            title="Embedding not available"
            message="This publication does not currently expose an embedding metadata record."
          />
        ) : (
          <DetailList
            items={[
              { label: "Collection", value: embedding.data.qdrant_collection },
              { label: "Provider", value: embedding.data.embedding_provider },
              { label: "Model", value: embedding.data.embedding_model },
              { label: "Version", value: embedding.data.embedding_version },
              { label: "Point id", value: embedding.data.qdrant_point_id },
            ]}
          />
        )}
      </Panel>
    </div>
  );
}
