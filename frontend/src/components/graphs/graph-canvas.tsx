import { forwardRef } from "react";

type GraphCanvasProps = {
  hint: string;
};

export const GraphCanvas = forwardRef<HTMLDivElement, GraphCanvasProps>(function GraphCanvas(
  { hint },
  ref,
) {
  return (
    <div className="relative h-[620px] overflow-hidden rounded-[1.5rem] border border-[color:var(--border)] bg-[radial-gradient(circle_at_top_right,rgba(245,158,11,0.12),transparent_24%),linear-gradient(180deg,#ffffff,#fafafa)] shadow-panel">
      <div ref={ref} className="h-full w-full" />
      <div className="pointer-events-none absolute bottom-4 left-4 rounded-full border border-[color:var(--border)] bg-white/90 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
        {hint}
      </div>
    </div>
  );
});
