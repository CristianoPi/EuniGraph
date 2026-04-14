import { ResearchersBrowser } from "@/components/entities/researchers-browser";
import { PageHeader } from "@/components/ui/page-header";

export default function ResearchersPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Researchers"
        title="Browse canonical researchers."
        description="Search by name or ORCID and inspect the currently available affiliation context provided by the backend."
      />
      <ResearchersBrowser />
    </div>
  );
}
