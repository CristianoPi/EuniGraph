type LoadingStateProps = {
  label?: string;
};

export function LoadingState({ label = "Loading data from the backend..." }: LoadingStateProps) {
  return (
    <div className="rounded-[1.5rem] border border-[color:var(--border)] bg-white p-5 shadow-panel">
      <div className="flex items-center gap-3 text-sm text-zinc-500">
        <span className="inline-flex h-2.5 w-2.5 animate-pulse rounded-full bg-amber-400" />
        <span>{label}</span>
      </div>
    </div>
  );
}
