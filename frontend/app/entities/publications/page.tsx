import { PublicationsBrowser } from "@/components/entities/publications-browser";
import { PageHeader } from "@/components/ui/page-header";

export default function PublicationsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Publications"
        title="Browse the canonical publication catalog."
        description="Search publications using backend-supported filters and navigate to detail views with authorship, organization links and semantic enrichment context."
      />
      <PublicationsBrowser />
    </div>
  );
}
