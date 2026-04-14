import Link from "next/link";
import { ReactNode } from "react";

import { appConfig } from "@/lib/config";
import { NavLink } from "@/components/layout/nav-link";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-shell-glow">
      <div className="mx-auto grid min-h-screen max-w-[1600px] gap-6 px-4 py-4 lg:grid-cols-[320px_minmax(0,1fr)] lg:px-6 lg:py-6">
        <aside className="rounded-[2rem] border border-[color:var(--border)] bg-[color:var(--panel-strong)] p-6 shadow-panel backdrop-blur">
          <div className="space-y-6">
            <div className="space-y-4">
              <Link href="/" className="block space-y-3">
                <span className="inline-flex rounded-full border border-pine/20 bg-pine/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.3em] text-pine">
                  EUNICE Prototype
                </span>
                <div>
                  <h1 className="text-3xl font-semibold tracking-tight text-ink">
                    {appConfig.name}
                  </h1>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{appConfig.subtitle}</p>
                </div>
              </Link>
              <div className="rounded-[1.5rem] bg-ink p-4 text-sm leading-6 text-white/82">
                The shell is intentionally light: it gives the project a stable navigation and
                data-integration surface before dashboard and graph explorer work starts.
              </div>
            </div>

            <nav className="space-y-3">
              {appConfig.navigation.map((item) => (
                <NavLink key={item.href} {...item} />
              ))}
            </nav>
          </div>
        </aside>

        <div className="space-y-5">
          <header className="rounded-[2rem] border border-[color:var(--border)] bg-[color:var(--panel)] px-6 py-5 shadow-panel backdrop-blur">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
                  Application Shell
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Shared layout, route placeholders, proxy-based API integration and server-state
                  patterns for the next frontend iterations.
                </p>
              </div>
              <div className="rounded-full border border-[color:var(--border)] bg-white/70 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-slate-600">
                Next.js + Tailwind + TanStack Query
              </div>
            </div>
          </header>
          <main>{children}</main>
        </div>
      </div>
    </div>
  );
}
