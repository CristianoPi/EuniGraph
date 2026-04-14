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
                <div>
                  <h1 className="text-3xl font-semibold tracking-tight text-ink">
                    {appConfig.name}
                  </h1>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{appConfig.subtitle}</p>
                </div>
              </Link>
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
            <p className="text-sm leading-6 text-slate-600">
              Explore canonical entities, workflow status, coauthorship links and semantic
              relationships from one interface.
            </p>
          </header>
          <main>{children}</main>
        </div>
      </div>
    </div>
  );
}
