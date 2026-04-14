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
        title="Inspect one canonical researcher and the current affiliation context."
        description="The view stays close to the backend contract: profile fields and affiliation records are shown directly without hidden client-side inference."
      />
      <ResearcherDetail id={id} />
    </div>
  );
}
