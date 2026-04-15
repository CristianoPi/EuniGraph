import { PublicationsBrowser } from "@/components/entities/publications-browser";
import { PageHeader } from "@/components/ui/page-header";

export default function PublicationsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Publications"
        title="Publications."
        description="Search records and open authorship, organization and embedding detail."
      />
      <PublicationsBrowser />
    </div>
  );
}
