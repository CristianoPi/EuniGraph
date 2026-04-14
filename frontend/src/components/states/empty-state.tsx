type EmptyStateProps = {
  title: string;
  message: string;
};

export function EmptyState({ title, message }: EmptyStateProps) {
  return (
    <div className="rounded-3xl border border-dashed border-[color:var(--border)] bg-white/60 p-6 text-sm text-slate-600">
      <p className="font-semibold text-ink">{title}</p>
      <p className="mt-2 leading-6">{message}</p>
    </div>
  );
}
