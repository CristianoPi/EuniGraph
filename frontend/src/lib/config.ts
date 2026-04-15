import type { Route } from "next";

export const appConfig = {
  name: "EuniGraph",
  subtitle: "Research mapping across the EUNICE network",
  description:
    "Demo interface for canonical entities, workflows and materialized graphs.",
  navigation: [
    {
      href: "/",
      label: "Overview",
      eyebrow: "Home",
      description: "Status and entry points.",
    },
    {
      href: "/dashboard",
      label: "Dashboard",
      eyebrow: "Status",
      description: "Catalog and workflow snapshot.",
    },
    {
      href: "/entities",
      label: "Entities",
      eyebrow: "Catalog",
      description: "Publications, researchers, organizations.",
    },
    {
      href: "/graphs",
      label: "Graphs",
      eyebrow: "Networks",
      description: "Coauthorship and semantic layers.",
    },
    {
      href: "/admin" as Route,
      label: "Admin",
      eyebrow: "Console",
      description: "Operations and manual entry.",
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
