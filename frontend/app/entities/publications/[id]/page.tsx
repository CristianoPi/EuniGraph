import { PublicationDetail } from "@/components/entities/publication-detail";
import { PageHeader } from "@/components/ui/page-header";

type PublicationDetailPageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function PublicationDetailPage({
  params,
}: PublicationDetailPageProps) {
  const { id } = await params;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Publication Detail"
        title="Publication detail."
        description="Metadata, authors, organizations and embedding status."
      />
      <PublicationDetail id={id} />
    </div>
  );
}
