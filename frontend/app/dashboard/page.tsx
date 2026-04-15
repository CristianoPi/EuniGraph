import { PageHeader } from "@/components/ui/page-header";
import { DashboardOverview } from "@/components/dashboard/dashboard-overview";
import { QuickSearch } from "@/components/dashboard/quick-search";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Dashboard"
        title="System snapshot."
        description="Catalog counts, workflow state and quick lookup in one place."
      />

      <DashboardOverview />
      <QuickSearch />
    </div>
  );
}
