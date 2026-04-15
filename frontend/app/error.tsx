"use client";

type GlobalErrorProps = {
  error: Error;
  reset: () => void;
};

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  return (
    <div className="rounded-[1.5rem] border border-red-200 bg-red-50 p-8 shadow-panel">
      <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[color:var(--danger)]">
        Runtime error
      </p>
      <h1 className="mt-3 text-2xl font-semibold text-ink">This view could not render.</h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-700">{error.message}</p>
      <button
        type="button"
        onClick={reset}
        className="mt-6 rounded-full bg-zinc-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-zinc-800"
      >
        Try again
      </button>
    </div>
  );
}
