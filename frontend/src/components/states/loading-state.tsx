type LoadingStateProps = {
  label?: string;
};

export function LoadingState({ label = "Loading data from the backend..." }: LoadingStateProps) {
  return (
    <div className="rounded-3xl border border-[color:var(--border)] bg-[color:var(--panel)] p-6 shadow-panel">
      <div className="flex items-center gap-3 text-sm text-slate-600">
        <span className="inline-flex h-3 w-3 animate-pulse rounded-full bg-ember" />
        <span>{label}</span>
      </div>
    </div>
  );
}
