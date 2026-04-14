import { ReactNode } from "react";

type DetailListProps = {
  items: Array<{
    label: string;
    value: ReactNode;
  }>;
};

export function DetailList({ items }: DetailListProps) {
  return (
    <dl className="grid gap-4 sm:grid-cols-2">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-[1.25rem] border border-[color:var(--border)] bg-white/70 p-4"
        >
          <dt className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            {item.label}
          </dt>
          <dd className="mt-2 text-sm leading-7 text-ink">{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}
