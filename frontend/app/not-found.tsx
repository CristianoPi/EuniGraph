import Link from "next/link";

export default function NotFound() {
  return (
    <div className="rounded-[1.5rem] border border-[color:var(--border)] bg-white p-8 shadow-panel">
      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-600">
        Not found
      </p>
      <h1 className="mt-3 text-3xl font-semibold text-ink">This view is unavailable.</h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-600">
        Use the navigation to return to an existing section.
      </p>
      <Link
        href="/"
        className="mt-6 inline-flex rounded-full bg-zinc-900 px-5 py-3 text-sm font-semibold text-white"
      >
        Back to overview
      </Link>
    </div>
  );
}
