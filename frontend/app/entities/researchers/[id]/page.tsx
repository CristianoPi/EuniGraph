import { ResearcherDetail } from "@/components/entities/researcher-detail";
import { PageHeader } from "@/components/ui/page-header";

type ResearcherDetailPageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function ResearcherDetailPage({
  params,
}: ResearcherDetailPageProps) {
  const { id } = await params;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Researcher Detail"
        title="Researcher detail."
        description="Profile metadata and affiliation records."
      />
      <ResearcherDetail id={id} />
    </div>
  );
}
