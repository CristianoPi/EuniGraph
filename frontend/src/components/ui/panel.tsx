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
        "rounded-[1.5rem] border border-[color:var(--border)] bg-[color:var(--panel)] p-5 shadow-panel backdrop-blur",
        className,
      )}
    >
      <header className="mb-5 space-y-1">
        <h2 className="text-base font-semibold text-ink">{title}</h2>
        {description ? <p className="max-w-3xl text-sm leading-6 text-zinc-500">{description}</p> : null}
      </header>
      {children}
    </section>
  );
}
