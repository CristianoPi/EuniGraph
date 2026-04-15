import { OrganizationDetail } from "@/components/entities/organization-detail";
import { PageHeader } from "@/components/ui/page-header";

type OrganizationDetailPageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function OrganizationDetailPage({
  params,
}: OrganizationDetailPageProps) {
  const { id } = await params;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Organization Detail"
        title="Organization detail."
        description="Hierarchy, identifiers and linked researchers."
      />
      <OrganizationDetail id={id} />
    </div>
  );
}
