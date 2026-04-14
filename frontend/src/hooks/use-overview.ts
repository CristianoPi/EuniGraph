"use client";

import { useQuery } from "@tanstack/react-query";

import { apiRequest } from "@/lib/api/client";
import type {
  EmbeddingsStatus,
  GraphBuildStatus,
  HealthResponse,
  Publication,
} from "@/lib/api/types";

export function useBackendHealth() {
  return useQuery({
    queryKey: ["backend-health"],
    queryFn: () => apiRequest<HealthResponse>("/api/v1/health"),
  });
}

export function useEmbeddingsStatus() {
  return useQuery({
    queryKey: ["embeddings-status"],
    queryFn: () => apiRequest<EmbeddingsStatus>("/api/v1/embeddings/status"),
  });
}

export function useCoauthorshipStatus() {
  return useQuery({
    queryKey: ["coauthorship-status"],
    queryFn: () => apiRequest<GraphBuildStatus>("/api/v1/coauthorship-graph/status"),
  });
}

export function useSemanticGraphStatus() {
  return useQuery({
    queryKey: ["semantic-graph-status"],
    queryFn: () => apiRequest<GraphBuildStatus>("/api/v1/semantic-graph/status"),
  });
}

export function usePublicationsPreview() {
  return useQuery({
    queryKey: ["publications-preview"],
    queryFn: () => apiRequest<Publication[]>("/api/v1/publications"),
    select: (publications) => publications.slice(0, 5),
  });
}
