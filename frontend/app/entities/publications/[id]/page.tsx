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
        title="Inspect one canonical publication and its current linked context."
        description="This view focuses on readable metadata and directly available relations, leaving advanced graph exploration to later slices."
      />
      <PublicationDetail id={id} />
    </div>
  );
}
