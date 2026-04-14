"use client";

type GlobalErrorProps = {
  error: Error;
  reset: () => void;
};

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  return (
    <div className="rounded-[2rem] border border-[color:rgba(181,74,47,0.22)] bg-[color:rgba(181,74,47,0.08)] p-8 shadow-panel">
      <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[color:var(--danger)]">
        Frontend runtime error
      </p>
      <h1 className="mt-3 text-2xl font-semibold text-ink">The shell could not render this view.</h1>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-700">{error.message}</p>
      <button
        type="button"
        onClick={reset}
        className="mt-6 rounded-full bg-ink px-5 py-3 text-sm font-semibold text-white transition hover:bg-pine"
      >
        Try again
      </button>
    </div>
  );
}
