type PageHeaderProps = {
  eyebrow: string;
  title: string;
  description: string;
};

export function PageHeader({ eyebrow, title, description }: PageHeaderProps) {
  return (
    <div className="space-y-3">
      <p className="text-xs font-semibold uppercase tracking-[0.32em] text-pine">{eyebrow}</p>
      <div className="space-y-2">
        <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
          {title}
        </h1>
        <p className="max-w-3xl text-base leading-7 text-slate-600 sm:text-lg">{description}</p>
      </div>
    </div>
  );
}
