type StatCardProps = {
  label: string;
  value: string;
  hint?: string;
};

export function StatCard({ label, value, hint }: StatCardProps) {
  return (
    <div className="rounded-[1.35rem] border border-[color:var(--border)] bg-white p-5 shadow-panel">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-zinc-500">{label}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-ink">{value}</p>
      {hint ? <p className="mt-2 text-sm leading-6 text-zinc-500">{hint}</p> : null}
    </div>
  );
}
