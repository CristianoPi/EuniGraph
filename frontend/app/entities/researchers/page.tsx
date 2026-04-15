import { ResearchersBrowser } from "@/components/entities/researchers-browser";
import { PageHeader } from "@/components/ui/page-header";

export default function ResearchersPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Researchers"
        title="Researchers."
        description="Search people and inspect affiliation context."
      />
      <ResearchersBrowser />
    </div>
  );
}
