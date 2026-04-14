import type { ElementDefinition } from "cytoscape";

import type {
  CoauthorshipEdge,
  CoauthorshipNode,
  GraphLayer,
  SemanticEdge,
  SemanticNode,
} from "@/lib/graphs/types";

export type ExplorerNodeData = {
  id: string;
  label: string;
  layer: GraphLayer;
  degree: number;
  strength: number;
  subtitle: string;
};

export type ExplorerEdgeData = {
  id: string;
  source: string;
  target: string;
  layer: GraphLayer;
  weight: number;
  label: string;
};

function coauthorshipNodeToElement(node: CoauthorshipNode): ElementDefinition {
  return {
    data: {
      id: node.id,
      label: node.label,
      layer: "coauthorship",
      degree: node.degree,
      strength: node.strength,
      subtitle: node.primary_organization_name ?? "Researcher node",
      size: Math.max(22, Math.min(54, 18 + node.degree * 1.8)),
    } satisfies ExplorerNodeData & { size: number },
  };
}

function semanticNodeToElement(node: SemanticNode): ElementDefinition {
  return {
    data: {
      id: node.id,
      label: node.label,
      layer: "semantic",
      degree: node.degree,
      strength: node.strength,
      subtitle: node.authors.slice(0, 2).join(", ") || "Publication node",
      size: Math.max(20, Math.min(50, 18 + node.degree * 1.6)),
    } satisfies ExplorerNodeData & { size: number },
  };
}

function coauthorshipEdgeToElement(edge: CoauthorshipEdge): ElementDefinition {
  return {
    data: {
      id: `${edge.source}__${edge.target}`,
      source: edge.source,
      target: edge.target,
      layer: "coauthorship",
      weight: edge.weight,
      label: `${edge.shared_publication_count} shared publications`,
      lineWidth: Math.max(1.5, Math.min(8, edge.weight)),
    } satisfies ExplorerEdgeData & { lineWidth: number },
  };
}

function semanticEdgeToElement(edge: SemanticEdge): ElementDefinition {
  return {
    data: {
      id: `${edge.source}__${edge.target}`,
      source: edge.source,
      target: edge.target,
      layer: "semantic",
      weight: edge.weight,
      label: `Similarity ${edge.similarity_score.toFixed(3)}`,
      lineWidth: Math.max(1.2, Math.min(7, edge.weight * 4)),
    } satisfies ExplorerEdgeData & { lineWidth: number },
  };
}

export function mapCoauthorshipElements(
  nodes: CoauthorshipNode[],
  edges: CoauthorshipEdge[],
): ElementDefinition[] {
  return [...nodes.map(coauthorshipNodeToElement), ...edges.map(coauthorshipEdgeToElement)];
}

export function mapSemanticElements(
  nodes: SemanticNode[],
  edges: SemanticEdge[],
): ElementDefinition[] {
  return [...nodes.map(semanticNodeToElement), ...edges.map(semanticEdgeToElement)];
}
