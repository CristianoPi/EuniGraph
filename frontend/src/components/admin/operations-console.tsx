"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";

import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Panel } from "@/components/ui/panel";
import { ApiError } from "@/lib/api/client";
import type { GraphBuildStatus, NormalizationFinding } from "@/lib/api/admin";
import {
  useAdminCoauthorshipStatus,
  useAdminEmbeddingsProvider,
  useAdminEmbeddingsStatus,
  useAdminNormalizationFindings,
  useAdminNormalizationStatus,
  useAdminSeedStatus,
  useAdminSemanticGraphStatus,
  useBuildCoauthorshipGraphMutation,
  useBuildEmbeddingsMutation,
  useBuildSemanticGraphMutation,
  useLoadAllEmbeddingsMutation,
  useLoadSeedMutation,
  useResetEmbeddingsMutation,
  useResetSeedMutation,
  useRunNormalizationMutation,
} from "@/hooks/use-admin";

const inputClass =
  "rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900";
const textareaClass = `${inputClass} min-h-28 resize-y`;
const buttonClass = "rounded-full bg-zinc-900 px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50";
const secondaryButtonClass =
  "rounded-full border border-[color:var(--border)] bg-white px-5 py-3 text-sm font-semibold text-zinc-700 hover:border-zinc-300 disabled:cursor-not-allowed disabled:opacity-50";
const dangerButtonClass =
  "rounded-full bg-[color:var(--danger)] px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50";

type SeedLoadForm = {
  limit_per_file: string;
};

type NormalizationForm = {
  notes: string;
};

type EmbeddingsBuildForm = {
  publication_ids: string;
  limit: string;
  force: boolean;
};

type CoauthorshipBuildForm = {
  triggered_by: string;
  include_isolated_nodes: boolean;
};

type SemanticBuildForm = {
  triggered_by: string;
  top_k: string;
  score_threshold: string;
  edge_symmetry_policy: string;
  mutual_knn: boolean;
  include_isolated_nodes: boolean;
  publication_type: string;
  language_code: string;
  year_from: string;
  year_to: string;
};

function optionalText(value: string): string | null {
  const normalized = value.trim();
  return normalized || null;
}

function optionalNumber(value: string): number | null {
  const normalized = value.trim();
  return normalized ? Number(normalized) : null;
}

function publicationIds(value: string): string[] | null {
  const ids = value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);

  return ids.length > 0 ? ids : null;
}

function formatDate(value?: string | null): string {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatError(error: unknown): string {
  if (error instanceof ApiError) {
    if (typeof error.detail === "string") {
      return error.detail;
    }

    return JSON.stringify(error.detail);
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unexpected error while calling the backend.";
}

function StatusGrid({ items }: { items: Array<{ label: string; value: string | number }> }) {
  return (
    <dl className="grid gap-3 sm:grid-cols-2">
      {items.map((item) => (
        <div key={item.label} className="rounded-[1rem] border border-[color:var(--border)] bg-white p-4">
          <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
            {item.label}
          </dt>
          <dd className="mt-2 break-words text-sm font-semibold text-ink">{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}

function MutationFeedback({
  isPending,
  isSuccess,
  isError,
  error,
  success,
}: {
  isPending: boolean;
  isSuccess: boolean;
  isError: boolean;
  error: unknown;
  success: string;
}) {
  if (isPending) {
    return <LoadingState label="Backend operation in progress..." />;
  }

  if (isError) {
    return <ErrorState title="Operation failed" message={formatError(error)} />;
  }

  if (isSuccess) {
    return (
      <div className="rounded-[1.5rem] border border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-zinc-700">
        <p className="font-semibold text-zinc-900">{success}</p>
      </div>
    );
  }

  return null;
}

function JsonPreview({ value }: { value: unknown }) {
  return (
    <pre className="max-h-72 overflow-auto rounded-[1rem] border border-zinc-200 bg-zinc-950 p-4 text-xs leading-6 text-white/90">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

function GraphStatusSummary({ status }: { status: GraphBuildStatus }) {
  return (
    <StatusGrid
      items={[
        { label: "Status", value: status.status },
        { label: "Active", value: status.is_active ? "yes" : "no" },
        { label: "Nodes", value: status.node_count ?? 0 },
        { label: "Edges", value: status.edge_count ?? 0 },
        { label: "Completed", value: formatDate(status.completed_at) },
        { label: "Version", value: status.graph_version ?? "Not available" },
      ]}
    />
  );
}

function SeedOperations() {
  const seedStatus = useAdminSeedStatus();
  const loadMutation = useLoadSeedMutation();
  const resetMutation = useResetSeedMutation();
  const [resetConfirmed, setResetConfirmed] = useState(false);
  const { handleSubmit, register } = useForm<SeedLoadForm>({
    defaultValues: { limit_per_file: "" },
  });

  return (
    <Panel
      title="OpenAIRE seed"
      description="Status, load and reset."
    >
      <div className="space-y-5">
        {seedStatus.isLoading ? (
          <LoadingState label="Loading seed status..." />
        ) : seedStatus.isError ? (
          <ErrorState message="Seed status could not be loaded." />
        ) : seedStatus.data ? (
          <div className="space-y-4">
            <StatusGrid
              items={[
                { label: "Dataset path", value: seedStatus.data.dataset_path },
                {
                  label: "Dataset available",
                  value: seedStatus.data.dataset_path_exists ? "yes" : "no",
                },
                {
                  label: "Latest run",
                  value: seedStatus.data.latest_ingestion_status ?? "Not available",
                },
              ]}
            />
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-[1rem] border border-[color:var(--border)] bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
                  Required files
                </p>
                <ul className="mt-3 space-y-2 text-sm text-zinc-600">
                  {Object.entries(seedStatus.data.required_files).map(([file, exists]) => (
                    <li key={file} className="flex items-center justify-between gap-3">
                      <span>{file}</span>
                      <span className={exists ? "font-semibold text-zinc-900" : "font-semibold text-[color:var(--danger)]"}>
                        {exists ? "available" : "missing"}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="rounded-[1rem] border border-[color:var(--border)] bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
                  Table counts
                </p>
                <ul className="mt-3 grid gap-2 text-sm text-zinc-600">
                  {Object.entries(seedStatus.data.table_counts).map(([table, count]) => (
                    <li key={table} className="flex items-center justify-between gap-3">
                      <span>{table}</span>
                      <span className="font-semibold text-ink">{count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ) : null}

        <form
          onSubmit={handleSubmit((values) =>
            loadMutation.mutate({
              limit_per_file: optionalNumber(values.limit_per_file),
            }),
          )}
          className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto]"
        >
          <input
            {...register("limit_per_file")}
            className={inputClass}
            inputMode="numeric"
            placeholder="Optional limit per archive file"
          />
          <button type="submit" disabled={loadMutation.isPending} className={buttonClass}>
            Load seed
          </button>
        </form>

        <div className="rounded-[1.25rem] border border-red-200 bg-red-50 p-4">
          <label className="flex items-start gap-3 text-sm leading-6 text-zinc-700">
            <input
              type="checkbox"
              checked={resetConfirmed}
              onChange={(event) => setResetConfirmed(event.target.checked)}
              className="mt-1"
            />
            Confirm reset of seed-created records and provenance rows.
          </label>
          <button
            type="button"
            disabled={!resetConfirmed || resetMutation.isPending}
            onClick={() => resetMutation.mutate()}
            className={`${dangerButtonClass} mt-4`}
          >
            Reset seed data
          </button>
        </div>

        <MutationFeedback
          isPending={loadMutation.isPending || resetMutation.isPending}
          isSuccess={loadMutation.isSuccess || resetMutation.isSuccess}
          isError={loadMutation.isError || resetMutation.isError}
          error={loadMutation.error ?? resetMutation.error}
          success="Seed operation completed and related frontend caches were refreshed."
        />
      </div>
    </Panel>
  );
}

function NormalizationOperations() {
  const status = useAdminNormalizationStatus();
  const findings = useAdminNormalizationFindings();
  const mutation = useRunNormalizationMutation();
  const { handleSubmit, register, reset } = useForm<NormalizationForm>({
    defaultValues: { notes: "" },
  });

  return (
    <Panel
      title="Normalization"
      description="Run deterministic cleanup."
    >
      <div className="space-y-5">
        {status.isLoading ? (
          <LoadingState label="Loading normalization status..." />
        ) : status.isError ? (
          <ErrorState message="Normalization status could not be loaded." />
        ) : status.data ? (
          <StatusGrid
            items={[
              { label: "Status", value: status.data.status },
              { label: "Findings", value: status.data.findings_count },
              { label: "Publications", value: status.data.normalized_publications },
              { label: "Researchers", value: status.data.normalized_researchers },
              { label: "Organizations", value: status.data.normalized_organizations },
              { label: "Completed", value: formatDate(status.data.completed_at) },
            ]}
          />
        ) : (
          <div className="rounded-[1.5rem] border border-dashed border-zinc-200 bg-white p-5 text-sm text-zinc-500">
            No normalization run has been recorded yet.
          </div>
        )}

        <form
          onSubmit={handleSubmit((values) => {
            mutation.mutate({ notes: optionalText(values.notes) });
            reset();
          })}
          className="space-y-3"
        >
          <textarea
            {...register("notes")}
            className={textareaClass}
            placeholder="Optional notes for this normalization run"
          />
          <button type="submit" disabled={mutation.isPending} className={buttonClass}>
            Run normalization
          </button>
        </form>

        {findings.data && findings.data.length > 0 ? (
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
              Latest findings
            </p>
            {findings.data.map((finding: NormalizationFinding) => (
              <div
                key={finding.id}
                className="rounded-[1rem] border border-[color:var(--border)] bg-white p-4"
              >
                <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                  <span>{finding.entity_type}</span>
                  <span>{finding.confidence}</span>
                  <span>{finding.finding_type}</span>
                </div>
                <p className="mt-2 text-sm leading-6 text-zinc-600">{finding.message}</p>
              </div>
            ))}
          </div>
        ) : null}

        <MutationFeedback
          isPending={mutation.isPending}
          isSuccess={mutation.isSuccess}
          isError={mutation.isError}
          error={mutation.error}
          success="Normalization run completed and catalog caches were refreshed."
        />
      </div>
    </Panel>
  );
}

function EmbeddingsOperations() {
  const provider = useAdminEmbeddingsProvider();
  const status = useAdminEmbeddingsStatus();
  const buildMutation = useBuildEmbeddingsMutation();
  const loadAllMutation = useLoadAllEmbeddingsMutation();
  const resetMutation = useResetEmbeddingsMutation();
  const [loadAllForce, setLoadAllForce] = useState(false);
  const [resetConfirmed, setResetConfirmed] = useState(false);
  const { handleSubmit, register } = useForm<EmbeddingsBuildForm>({
    defaultValues: {
      publication_ids: "",
      limit: "",
      force: false,
    },
  });

  return (
    <Panel
      title="Embeddings"
      description="Provider status, build and reset."
    >
      <div className="space-y-5">
        {provider.isLoading || status.isLoading ? (
          <LoadingState label="Loading embeddings configuration and status..." />
        ) : provider.isError || status.isError ? (
          <ErrorState message="Embeddings provider or status could not be loaded." />
        ) : provider.data && status.data ? (
          <StatusGrid
            items={[
              { label: "Enabled", value: status.data.enabled ? "yes" : "no" },
              { label: "Provider", value: provider.data.provider },
              { label: "Model", value: provider.data.model },
              { label: "Collection", value: status.data.qdrant_collection },
              { label: "Qdrant points", value: status.data.qdrant_points_count },
              { label: "Active metadata", value: status.data.active_embeddings_count },
              { label: "Total publications", value: status.data.total_publications },
              { label: "Gemini key", value: provider.data.gemini_api_key_configured ? "configured" : "missing" },
            ]}
          />
        ) : null}

        <form
          onSubmit={handleSubmit((values) =>
            buildMutation.mutate({
              publication_ids: publicationIds(values.publication_ids),
              limit: optionalNumber(values.limit),
              force: values.force,
            }),
          )}
          className="space-y-3"
        >
          <textarea
            {...register("publication_ids")}
            className={textareaClass}
            placeholder="Optional publication UUIDs, one per line or comma-separated"
          />
          <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto]">
            <input
              {...register("limit")}
              className={inputClass}
              inputMode="numeric"
              placeholder="Optional batch limit"
            />
            <label className="flex items-center gap-2 rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm text-zinc-700">
              <input type="checkbox" {...register("force")} />
              Force regeneration
            </label>
          </div>
          <button type="submit" disabled={buildMutation.isPending} className={buttonClass}>
            Build selected batch
          </button>
        </form>

        <div className="flex flex-col gap-3 rounded-[1.25rem] border border-[color:var(--border)] bg-white p-4 md:flex-row md:items-center md:justify-between">
          <label className="flex items-center gap-2 text-sm text-zinc-700">
            <input
              type="checkbox"
              checked={loadAllForce}
              onChange={(event) => setLoadAllForce(event.target.checked)}
            />
            Force regeneration while loading all publications
          </label>
          <button
            type="button"
            disabled={loadAllMutation.isPending}
            onClick={() => loadAllMutation.mutate({ force: loadAllForce })}
            className={secondaryButtonClass}
          >
            Load all embeddings
          </button>
        </div>

        <div className="rounded-[1.25rem] border border-red-200 bg-red-50 p-4">
          <label className="flex items-start gap-3 text-sm leading-6 text-zinc-700">
            <input
              type="checkbox"
              checked={resetConfirmed}
              onChange={(event) => setResetConfirmed(event.target.checked)}
              className="mt-1"
            />
            Confirm reset of the active Qdrant collection and aligned metadata.
          </label>
          <button
            type="button"
            disabled={!resetConfirmed || resetMutation.isPending}
            onClick={() => resetMutation.mutate()}
            className={`${dangerButtonClass} mt-4`}
          >
            Reset embeddings
          </button>
        </div>

        <MutationFeedback
          isPending={buildMutation.isPending || loadAllMutation.isPending || resetMutation.isPending}
          isSuccess={buildMutation.isSuccess || loadAllMutation.isSuccess || resetMutation.isSuccess}
          isError={buildMutation.isError || loadAllMutation.isError || resetMutation.isError}
          error={buildMutation.error ?? loadAllMutation.error ?? resetMutation.error}
          success="Embedding operation completed and status caches were refreshed."
        />

        {buildMutation.data ?? loadAllMutation.data ?? resetMutation.data ? (
          <JsonPreview value={buildMutation.data ?? loadAllMutation.data ?? resetMutation.data} />
        ) : null}
      </div>
    </Panel>
  );
}

function GraphOperations() {
  const coauthorshipStatus = useAdminCoauthorshipStatus();
  const semanticStatus = useAdminSemanticGraphStatus();
  const coauthorshipMutation = useBuildCoauthorshipGraphMutation();
  const semanticMutation = useBuildSemanticGraphMutation();
  const coauthorshipForm = useForm<CoauthorshipBuildForm>({
    defaultValues: {
      triggered_by: "admin-console",
      include_isolated_nodes: true,
    },
  });
  const semanticForm = useForm<SemanticBuildForm>({
    defaultValues: {
      triggered_by: "admin-console",
      top_k: "5",
      score_threshold: "0.75",
      edge_symmetry_policy: "max_score_union",
      mutual_knn: false,
      include_isolated_nodes: false,
      publication_type: "",
      language_code: "",
      year_from: "",
      year_to: "",
    },
  });

  return (
    <Panel
      title="Graph builds"
      description="Coauthorship and semantic materialization."
    >
      <div className="grid gap-6 xl:grid-cols-2">
        <div className="space-y-4">
          <h3 className="text-base font-semibold text-ink">Coauthorship graph</h3>
          {coauthorshipStatus.isLoading ? (
            <LoadingState label="Loading coauthorship status..." />
          ) : coauthorshipStatus.isError ? (
            <ErrorState message="Coauthorship graph status could not be loaded." />
          ) : coauthorshipStatus.data ? (
            <GraphStatusSummary status={coauthorshipStatus.data} />
          ) : null}

          <form
            onSubmit={coauthorshipForm.handleSubmit((values) =>
              coauthorshipMutation.mutate({
                triggered_by: optionalText(values.triggered_by),
                include_isolated_nodes: values.include_isolated_nodes,
              }),
            )}
            className="space-y-3"
          >
            <input
              {...coauthorshipForm.register("triggered_by")}
              className={inputClass}
              placeholder="Triggered by"
            />
            <label className="flex items-center gap-2 rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm text-zinc-700">
              <input type="checkbox" {...coauthorshipForm.register("include_isolated_nodes")} />
              Include isolated nodes
            </label>
            <button
              type="submit"
              disabled={coauthorshipMutation.isPending}
              className={buttonClass}
            >
              Build coauthorship graph
            </button>
          </form>
          <MutationFeedback
            isPending={coauthorshipMutation.isPending}
            isSuccess={coauthorshipMutation.isSuccess}
            isError={coauthorshipMutation.isError}
            error={coauthorshipMutation.error}
            success="Coauthorship graph build completed and graph caches were refreshed."
          />
        </div>

        <div className="space-y-4">
          <h3 className="text-base font-semibold text-ink">Semantic graph</h3>
          {semanticStatus.isLoading ? (
            <LoadingState label="Loading semantic graph status..." />
          ) : semanticStatus.isError ? (
            <ErrorState message="Semantic graph status could not be loaded." />
          ) : semanticStatus.data ? (
            <GraphStatusSummary status={semanticStatus.data} />
          ) : null}

          <form
            onSubmit={semanticForm.handleSubmit((values) =>
              semanticMutation.mutate({
                triggered_by: optionalText(values.triggered_by),
                top_k: Number(values.top_k),
                score_threshold: optionalNumber(values.score_threshold),
                edge_symmetry_policy: values.edge_symmetry_policy.trim() || "max_score_union",
                mutual_knn: values.mutual_knn,
                include_isolated_nodes: values.include_isolated_nodes,
                publication_type: optionalText(values.publication_type),
                language_code: optionalText(values.language_code),
                year_from: optionalNumber(values.year_from),
                year_to: optionalNumber(values.year_to),
              }),
            )}
            className="space-y-3"
          >
            <div className="grid gap-3 md:grid-cols-2">
              <input
                {...semanticForm.register("triggered_by")}
                className={inputClass}
                placeholder="Triggered by"
              />
              <input
                {...semanticForm.register("edge_symmetry_policy")}
                className={inputClass}
                placeholder="Edge symmetry policy"
              />
              <input
                {...semanticForm.register("top_k", { required: true })}
                className={inputClass}
                inputMode="numeric"
                placeholder="top_k"
              />
              <input
                {...semanticForm.register("score_threshold")}
                className={inputClass}
                inputMode="decimal"
                placeholder="Score threshold"
              />
              <input
                {...semanticForm.register("publication_type")}
                className={inputClass}
                placeholder="Optional publication type"
              />
              <input
                {...semanticForm.register("language_code")}
                className={inputClass}
                placeholder="Optional language code"
              />
              <input
                {...semanticForm.register("year_from")}
                className={inputClass}
                inputMode="numeric"
                placeholder="Optional year from"
              />
              <input
                {...semanticForm.register("year_to")}
                className={inputClass}
                inputMode="numeric"
                placeholder="Optional year to"
              />
            </div>
            <div className="flex flex-wrap gap-3">
              <label className="flex items-center gap-2 rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm text-zinc-700">
                <input type="checkbox" {...semanticForm.register("mutual_knn")} />
                Mutual KNN only
              </label>
              <label className="flex items-center gap-2 rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm text-zinc-700">
                <input type="checkbox" {...semanticForm.register("include_isolated_nodes")} />
                Include isolated nodes
              </label>
            </div>
            <button type="submit" disabled={semanticMutation.isPending} className={buttonClass}>
              Build semantic graph
            </button>
          </form>
          <MutationFeedback
            isPending={semanticMutation.isPending}
            isSuccess={semanticMutation.isSuccess}
            isError={semanticMutation.isError}
            error={semanticMutation.error}
            success="Semantic graph build completed and graph caches were refreshed."
          />
        </div>
      </div>
    </Panel>
  );
}

export function OperationsConsole() {
  return (
    <div className="space-y-6">
      <SeedOperations />
      <NormalizationOperations />
      <EmbeddingsOperations />
      <GraphOperations />
    </div>
  );
}
