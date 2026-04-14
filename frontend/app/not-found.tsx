import Link from "next/link";

export default function NotFound() {
  return (
    <div className="rounded-[2rem] border border-[color:var(--border)] bg-[color:var(--panel)] p-8 shadow-panel">
      <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
        Route not found
      </p>
      <h1 className="mt-3 text-3xl font-semibold text-ink">This view does not exist yet.</h1>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-700">
        The frontend route map is intentionally small in this first iteration. Use the navigation
        shell to return to an existing section.
      </p>
      <Link
        href="/"
        className="mt-6 inline-flex rounded-full bg-pine px-5 py-3 text-sm font-semibold text-white"
      >
        Back to overview
      </Link>
    </div>
  );
}
