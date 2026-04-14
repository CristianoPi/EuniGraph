import { PageHeader } from "@/components/ui/page-header";
import { DashboardOverview } from "@/components/dashboard/dashboard-overview";
import { QuickSearch } from "@/components/dashboard/quick-search";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Dashboard"
        title="A dashboard that makes the dataset readable without opening a graph."
        description="Use the dashboard to orient yourself across catalog size, workflow state and quick entry points into the main sections."
      />

      <DashboardOverview />
      <QuickSearch />
    </div>
  );
}
