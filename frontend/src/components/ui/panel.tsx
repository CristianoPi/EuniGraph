import { ReactNode } from "react";

import { cn } from "@/lib/utils";

type PanelProps = {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
};

export function Panel({ title, description, children, className }: PanelProps) {
  return (
    <section
      className={cn(
        "rounded-[2rem] border border-[color:var(--border)] bg-[color:var(--panel)] p-6 shadow-panel backdrop-blur",
        className,
      )}
    >
      <header className="mb-5 space-y-1">
        <h2 className="text-lg font-semibold text-ink">{title}</h2>
        {description ? <p className="text-sm leading-6 text-slate-600">{description}</p> : null}
      </header>
      {children}
    </section>
  );
}
