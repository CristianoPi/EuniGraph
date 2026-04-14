"use client";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { usePublicationsPreview } from "@/hooks/use-overview";

export function PublicationsPreview() {
  const publications = usePublicationsPreview();

  if (publications.isLoading) {
    return <LoadingState label="Loading publication preview..." />;
  }

  if (publications.isError) {
    return <ErrorState message="Publication preview could not be loaded from the backend." />;
  }

  const items = publications.data ?? [];

  if (items.length === 0) {
    return (
      <EmptyState
        title="No publications available"
        message="Seed data has not been loaded yet, or the canonical catalog is still empty."
      />
    );
  }

  return (
    <div className="space-y-3">
      {items.map((publication, index) => (
        <article
          key={publication.id}
          className="rounded-[1.5rem] border border-[color:var(--border)] bg-white/70 p-5"
        >
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                Publication {index + 1}
              </p>
              <h3 className="text-lg font-semibold text-ink">{publication.title}</h3>
              <div className="flex flex-wrap gap-2 text-sm text-slate-600">
                {publication.publication_year ? (
                  <span className="rounded-full bg-slate-100 px-3 py-1">
                    Year {publication.publication_year}
                  </span>
                ) : null}
                {publication.doi ? (
                  <span className="rounded-full bg-slate-100 px-3 py-1">{publication.doi}</span>
                ) : null}
                {publication.openaire_id ? (
                  <span className="rounded-full bg-slate-100 px-3 py-1">
                    {publication.openaire_id}
                  </span>
                ) : null}
              </div>
            </div>
            <span className="rounded-full border border-[color:var(--border)] bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
              Canonical
            </span>
          </div>
        </article>
      ))}
    </div>
  );
}
