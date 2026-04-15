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
      <div className="mx-auto grid min-h-screen max-w-[1520px] gap-5 px-4 py-4 lg:grid-cols-[260px_minmax(0,1fr)] lg:px-6 lg:py-6">
        <aside className="rounded-[1.5rem] border border-[color:var(--border)] bg-[color:var(--panel-strong)] p-4 shadow-panel backdrop-blur">
          <div className="space-y-5">
            <div className="space-y-3 border-b border-zinc-100 pb-5">
              <Link href="/" className="block space-y-3">
                <div>
                  <h1 className="text-2xl font-semibold tracking-tight text-ink">
                    {appConfig.name}
                  </h1>
                  <p className="mt-1 text-xs leading-5 text-zinc-500">{appConfig.subtitle}</p>
                </div>
              </Link>
            </div>

            <nav className="space-y-2">
              {appConfig.navigation.map((item) => (
                <NavLink key={item.href} {...item} />
              ))}
            </nav>
          </div>
        </aside>

        <div className="space-y-5 lg:space-y-6">
          <header className="flex items-center justify-between rounded-[1.5rem] border border-[color:var(--border)] bg-[color:var(--panel)] px-5 py-3 shadow-panel backdrop-blur">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-zinc-500">
              EUNICE research map
            </p>
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-zinc-900">
              Demo
            </span>
          </header>
          <main>{children}</main>
        </div>
      </div>
    </div>
  );
}
