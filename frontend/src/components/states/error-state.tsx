type ErrorStateProps = {
  title?: string;
  message: string;
};

export function ErrorState({
  title = "Backend request failed",
  message,
}: ErrorStateProps) {
  return (
    <div className="rounded-[1.5rem] border border-red-200 bg-red-50 p-5 shadow-panel">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--danger)]">
        {title}
      </p>
      <p className="mt-2 text-sm leading-6 text-zinc-700">{message}</p>
    </div>
  );
}
