export const appConfig = {
  name: "EuniGraph",
  subtitle: "Research mapping across the EUNICE network",
  description:
    "Frontend foundation for navigating canonical entities, semantic workflows and graph materializations exposed by the EuniGraph backend.",
  navigation: [
    {
      href: "/",
      label: "Overview",
      eyebrow: "Shell",
      description: "Prototype status and integration health.",
    },
    {
      href: "/dashboard",
      label: "Dashboard",
      eyebrow: "Workflows",
      description: "Operational snapshots from backend pipelines.",
    },
    {
      href: "/entities",
      label: "Entities",
      eyebrow: "Catalog",
      description: "Canonical publications, researchers and organizations.",
    },
    {
      href: "/graphs",
      label: "Graphs",
      eyebrow: "Networks",
      description: "Materialized coauthorship and semantic graph status.",
    },
  ],
} as const;

export function getBrowserApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/backend";
}

export function getBackendBaseUrl(): string {
  const configured = process.env.EUNIGRAPH_BACKEND_URL ?? "http://localhost:8000";
  return configured.replace(/\/$/, "");
}
