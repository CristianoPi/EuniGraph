type ErrorStateProps = {
  title?: string;
  message: string;
};

export function ErrorState({
  title = "Backend request failed",
  message,
}: ErrorStateProps) {
  return (
    <div className="rounded-3xl border border-[color:rgba(181,74,47,0.22)] bg-[color:rgba(181,74,47,0.08)] p-6 shadow-panel">
      <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[color:var(--danger)]">
        {title}
      </p>
      <p className="mt-2 text-sm leading-6 text-slate-700">{message}</p>
    </div>
  );
}
