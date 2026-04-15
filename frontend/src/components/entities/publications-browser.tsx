"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { Route } from "next";
import { FormEvent, startTransition, useMemo, useState } from "react";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Panel } from "@/components/ui/panel";
import { usePublications } from "@/hooks/use-catalog";

function publicationRoute(id: string): Route {
  return `/entities/publications/${id}` as Route;
}

export function PublicationsBrowser() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const [title, setTitle] = useState(searchParams.get("title") ?? "");
  const [doi, setDoi] = useState(searchParams.get("doi") ?? "");
  const [openaireId, setOpenaireId] = useState(searchParams.get("openaire_id") ?? "");
  const [year, setYear] = useState(searchParams.get("publication_year") ?? "");

  const filters = useMemo(
    () => ({
      title: searchParams.get("title") ?? undefined,
      doi: searchParams.get("doi") ?? undefined,
      openaire_id: searchParams.get("openaire_id") ?? undefined,
      publication_year: searchParams.get("publication_year")
        ? Number(searchParams.get("publication_year"))
        : undefined,
      limit: 50,
    }),
    [searchParams],
  );

  const publications = usePublications(filters);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const params = new URLSearchParams();
    if (title.trim()) params.set("title", title.trim());
    if (doi.trim()) params.set("doi", doi.trim());
    if (openaireId.trim()) params.set("openaire_id", openaireId.trim());
    if (year.trim()) params.set("publication_year", year.trim());

    startTransition(() => {
      const query = params.toString();
      router.replace((query ? `${pathname}?${query}` : pathname) as Route);
    });
  }

  function resetFilters() {
    setTitle("");
    setDoi("");
    setOpenaireId("");
    setYear("");
    startTransition(() => router.replace(pathname as Route));
  }

  return (
    <div className="space-y-5">
      <Panel
        title="Filters"
        description="Title, DOI, OpenAIRE id or year."
      >
        <form onSubmit={handleSubmit} className="grid gap-4 xl:grid-cols-4">
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Title fragment"
            className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
          />
          <input
            value={doi}
            onChange={(event) => setDoi(event.target.value)}
            placeholder="DOI"
            className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
          />
          <input
            value={openaireId}
            onChange={(event) => setOpenaireId(event.target.value)}
            placeholder="OpenAIRE id"
            className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
          />
          <input
            value={year}
            onChange={(event) => setYear(event.target.value)}
            placeholder="Publication year"
            inputMode="numeric"
            className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
          />
          <div className="flex gap-3 xl:col-span-4">
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

      {publications.isLoading ? (
        <LoadingState label="Loading publications..." />
      ) : publications.isError ? (
        <ErrorState message="The publication list could not be loaded from the backend." />
      ) : (publications.data ?? []).length === 0 ? (
        <EmptyState
          title="No publications found"
          message="Adjust the filters or clear them to inspect the canonical publication catalog."
        />
      ) : (
        <div className="grid gap-4">
          {publications.data?.map((publication) => (
            <Link
              key={publication.id}
              href={publicationRoute(publication.id)}
              className="rounded-[1.35rem] border border-[color:var(--border)] bg-white p-5 shadow-panel transition hover:border-zinc-300"
            >
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-3">
                  <h2 className="text-xl font-semibold text-ink">{publication.title}</h2>
                  <div className="flex flex-wrap gap-2 text-sm text-zinc-500">
                    {publication.publication_year ? (
                      <span className="rounded-full bg-zinc-100 px-3 py-1">
                        {publication.publication_year}
                      </span>
                    ) : null}
                    {publication.doi ? (
                      <span className="rounded-full bg-zinc-100 px-3 py-1">{publication.doi}</span>
                    ) : null}
                    {publication.journal_name ? (
                      <span className="rounded-full bg-zinc-100 px-3 py-1">
                        {publication.journal_name}
                      </span>
                    ) : null}
                  </div>
                  {publication.abstract ? (
                    <p className="max-w-4xl text-sm leading-7 text-zinc-600 line-clamp-3">
                      {publication.abstract}
                    </p>
                  ) : null}
                </div>
                <div className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-zinc-900">
                  Open
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
