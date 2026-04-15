import { OrganizationsBrowser } from "@/components/entities/organizations-browser";
import { PageHeader } from "@/components/ui/page-header";

export default function OrganizationsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Organizations"
        title="Organizations."
        description="Browse units, hierarchy and linked researchers."
      />
      <OrganizationsBrowser />
    </div>
  );
}
