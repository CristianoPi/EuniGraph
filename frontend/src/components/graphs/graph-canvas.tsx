import { forwardRef } from "react";

type GraphCanvasProps = {
  hint: string;
};

export const GraphCanvas = forwardRef<HTMLDivElement, GraphCanvasProps>(function GraphCanvas(
  { hint },
  ref,
) {
  return (
    <div className="relative h-[620px] overflow-hidden rounded-[2rem] border border-[color:var(--border)] bg-[radial-gradient(circle_at_top_left,rgba(15,76,92,0.08),transparent_28%),radial-gradient(circle_at_bottom_right,rgba(198,101,61,0.08),transparent_24%),rgba(255,255,255,0.9)] shadow-panel">
      <div ref={ref} className="h-full w-full" />
      <div className="pointer-events-none absolute bottom-4 left-4 rounded-full border border-[color:var(--border)] bg-white/85 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
        {hint}
      </div>
    </div>
  );
});
