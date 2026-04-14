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
          ? "rounded-full border border-pine bg-pine px-4 py-2 text-sm font-semibold text-white"
          : "rounded-full border border-[color:var(--border)] bg-white px-4 py-2 text-sm font-semibold text-slate-700"
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
              className="rounded-[1.2rem] border border-[color:var(--border)] bg-white/80 px-4 py-3 text-sm outline-none focus:border-pine"
            />
            <input
              value={coauthorship.organizationId}
              onChange={(event) => onCoauthorshipChange("organizationId", event.target.value)}
              placeholder="Organization UUID"
              className="rounded-[1.2rem] border border-[color:var(--border)] bg-white/80 px-4 py-3 text-sm outline-none focus:border-pine"
            />
            <input
              value={coauthorship.communityId}
              onChange={(event) => onCoauthorshipChange("communityId", event.target.value)}
              placeholder="Community id"
              className="rounded-[1.2rem] border border-[color:var(--border)] bg-white/80 px-4 py-3 text-sm outline-none focus:border-pine"
            />
          </>
        ) : (
          <>
            <input
              value={semantic.publicationId}
              onChange={(event) => onSemanticChange("publicationId", event.target.value)}
              placeholder="Publication UUID focus"
              className="rounded-[1.2rem] border border-[color:var(--border)] bg-white/80 px-4 py-3 text-sm outline-none focus:border-pine"
            />
            <input
              value={semantic.organizationId}
              onChange={(event) => onSemanticChange("organizationId", event.target.value)}
              placeholder="Organization UUID"
              className="rounded-[1.2rem] border border-[color:var(--border)] bg-white/80 px-4 py-3 text-sm outline-none focus:border-pine"
            />
            <input
              value={semantic.publicationYear}
              onChange={(event) => onSemanticChange("publicationYear", event.target.value)}
              placeholder="Publication year"
              className="rounded-[1.2rem] border border-[color:var(--border)] bg-white/80 px-4 py-3 text-sm outline-none focus:border-pine"
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
          className="rounded-[1.2rem] border border-[color:var(--border)] bg-white/80 px-4 py-3 text-sm outline-none focus:border-pine"
        />
        <input
          value={layer === "coauthorship" ? coauthorship.minEdgeWeight : semantic.minEdgeWeight}
          onChange={(event) =>
            layer === "coauthorship"
              ? onCoauthorshipChange("minEdgeWeight", event.target.value)
              : onSemanticChange("minEdgeWeight", event.target.value)
          }
          placeholder={layer === "coauthorship" ? "Min edge weight" : "Min similarity weight"}
          className="rounded-[1.2rem] border border-[color:var(--border)] bg-white/80 px-4 py-3 text-sm outline-none focus:border-pine"
        />
        <div className="rounded-[1.2rem] border border-dashed border-[color:var(--border)] bg-white/55 px-4 py-3 text-sm leading-6 text-slate-600">
          {layer === "coauthorship"
            ? "Researcher nodes, collaboration edges, weight = shared publications."
            : "Publication nodes, similarity edges, weight = materialized semantic score."}
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onApply}
          className="rounded-full bg-pine px-5 py-3 text-sm font-semibold text-white"
        >
          Apply filters
        </button>
        <button
          type="button"
          onClick={onResetFilters}
          className="rounded-full border border-[color:var(--border)] bg-white px-5 py-3 text-sm font-semibold text-slate-700"
        >
          Reset filters
        </button>
        <button
          type="button"
          onClick={onResetView}
          className="rounded-full border border-[color:var(--border)] bg-white px-5 py-3 text-sm font-semibold text-slate-700"
        >
          Reset view
        </button>
        <button
          type="button"
          onClick={onCenterSelection}
          disabled={!canCenterSelection}
          className="rounded-full border border-[color:var(--border)] bg-white px-5 py-3 text-sm font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Center selection
        </button>
      </div>
    </div>
  );
}
