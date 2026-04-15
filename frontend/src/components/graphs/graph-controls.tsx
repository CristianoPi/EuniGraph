"use client";

import type { GraphLayer } from "@/lib/graphs/types";

type CoauthorshipControlState = {
  researcherId: string;
  organizationId: string;
  communityId: string;
  maxNodes: string;
  minEdgeWeight: string;
};

type SemanticControlState = {
  publicationId: string;
  organizationId: string;
  publicationYear: string;
  communityId: string;
  maxNodes: string;
  minEdgeWeight: string;
};

type GraphControlsProps = {
  layer: GraphLayer;
  onLayerChange: (layer: GraphLayer) => void;
  coauthorship: CoauthorshipControlState;
  semantic: SemanticControlState;
  onCoauthorshipChange: (key: keyof CoauthorshipControlState, value: string) => void;
  onSemanticChange: (key: keyof SemanticControlState, value: string) => void;
  onApply: () => void;
  onResetFilters: () => void;
  onResetView: () => void;
  onCenterSelection: () => void;
  canCenterSelection: boolean;
};

function LayerButton({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        active
          ? "rounded-full border border-zinc-900 bg-zinc-900 px-4 py-2 text-sm font-semibold text-white"
          : "rounded-full border border-[color:var(--border)] bg-white px-4 py-2 text-sm font-semibold text-zinc-700 hover:border-zinc-300"
      }
    >
      {label}
    </button>
  );
}

export function GraphControls({
  layer,
  onLayerChange,
  coauthorship,
  semantic,
  onCoauthorshipChange,
  onSemanticChange,
  onApply,
  onResetFilters,
  onResetView,
  onCenterSelection,
  canCenterSelection,
}: GraphControlsProps) {
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-3">
        <LayerButton
          active={layer === "coauthorship"}
          label="Coauthorship"
          onClick={() => onLayerChange("coauthorship")}
        />
        <LayerButton
          active={layer === "semantic"}
          label="Semantic"
          onClick={() => onLayerChange("semantic")}
        />
      </div>

      <div className="grid gap-3 xl:grid-cols-3">
        {layer === "coauthorship" ? (
          <>
            <input
              value={coauthorship.researcherId}
              onChange={(event) => onCoauthorshipChange("researcherId", event.target.value)}
              placeholder="Researcher UUID focus"
              className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
            />
            <input
              value={coauthorship.organizationId}
              onChange={(event) => onCoauthorshipChange("organizationId", event.target.value)}
              placeholder="Organization UUID"
              className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
            />
            <input
              value={coauthorship.communityId}
              onChange={(event) => onCoauthorshipChange("communityId", event.target.value)}
              placeholder="Community id"
              className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
            />
          </>
        ) : (
          <>
            <input
              value={semantic.publicationId}
              onChange={(event) => onSemanticChange("publicationId", event.target.value)}
              placeholder="Publication UUID focus"
              className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
            />
            <input
              value={semantic.organizationId}
              onChange={(event) => onSemanticChange("organizationId", event.target.value)}
              placeholder="Organization UUID"
              className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
            />
            <input
              value={semantic.publicationYear}
              onChange={(event) => onSemanticChange("publicationYear", event.target.value)}
              placeholder="Publication year"
              className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
            />
          </>
        )}

        <input
          value={layer === "coauthorship" ? coauthorship.maxNodes : semantic.maxNodes}
          onChange={(event) =>
            layer === "coauthorship"
              ? onCoauthorshipChange("maxNodes", event.target.value)
              : onSemanticChange("maxNodes", event.target.value)
          }
          placeholder="Max nodes"
          className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
        />
        <input
          value={layer === "coauthorship" ? coauthorship.minEdgeWeight : semantic.minEdgeWeight}
          onChange={(event) =>
            layer === "coauthorship"
              ? onCoauthorshipChange("minEdgeWeight", event.target.value)
              : onSemanticChange("minEdgeWeight", event.target.value)
          }
          placeholder={layer === "coauthorship" ? "Min edge weight" : "Min similarity weight"}
          className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-zinc-900"
        />
        <div className="rounded-[1rem] border border-dashed border-zinc-200 bg-white px-4 py-3 text-sm leading-6 text-zinc-500">
          {layer === "coauthorship"
            ? "Researchers linked by shared publications."
            : "Publications linked by semantic score."}
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onApply}
          className="rounded-full bg-zinc-900 px-5 py-3 text-sm font-semibold text-white"
        >
          Apply filters
        </button>
        <button
          type="button"
          onClick={onResetFilters}
          className="rounded-full border border-[color:var(--border)] bg-white px-5 py-3 text-sm font-semibold text-zinc-700 hover:border-zinc-300"
        >
          Reset filters
        </button>
        <button
          type="button"
          onClick={onResetView}
          className="rounded-full border border-[color:var(--border)] bg-white px-5 py-3 text-sm font-semibold text-zinc-700 hover:border-zinc-300"
        >
          Reset view
        </button>
        <button
          type="button"
          onClick={onCenterSelection}
          disabled={!canCenterSelection}
          className="rounded-full border border-[color:var(--border)] bg-white px-5 py-3 text-sm font-semibold text-zinc-700 hover:border-zinc-300 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Center selection
        </button>
      </div>
    </div>
  );
}
