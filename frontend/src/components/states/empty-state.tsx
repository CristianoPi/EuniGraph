type EmptyStateProps = {
  title: string;
  message: string;
};

export function EmptyState({ title, message }: EmptyStateProps) {
  return (
    <div className="rounded-[1.5rem] border border-dashed border-zinc-200 bg-white p-5 text-sm text-zinc-500">
      <p className="font-semibold text-ink">{title}</p>
      <p className="mt-2 leading-6">{message}</p>
    </div>
  );
}
