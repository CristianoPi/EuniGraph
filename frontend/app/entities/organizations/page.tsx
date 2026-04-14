import { OrganizationsBrowser } from "@/components/entities/organizations-browser";
import { PageHeader } from "@/components/ui/page-header";

export default function OrganizationsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Organizations"
        title="Browse canonical organizations."
        description="Inspect universities, departments and related organizational entities through filters already supported by the backend."
      />
      <OrganizationsBrowser />
    </div>
  );
}
