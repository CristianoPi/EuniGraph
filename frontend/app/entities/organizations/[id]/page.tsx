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
        title="Inspect one canonical organization and its immediate catalog context."
        description="This detail view emphasizes hierarchy and directly linked researchers, which are the backend relations available today without graph exploration."
      />
      <OrganizationDetail id={id} />
    </div>
  );
}
