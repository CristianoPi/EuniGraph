import { PageHeader } from "@/components/ui/page-header";
import { DashboardOverview } from "@/components/dashboard/dashboard-overview";
import { QuickSearch } from "@/components/dashboard/quick-search";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Dashboard"
        title="A first dashboard that makes the prototype readable without opening a graph."
        description="The overview combines stable backend endpoints into a pragmatic dashboard: catalog snapshots, workflow presence and quick entry points into publications, researchers and organizations."
      />

      <DashboardOverview />
      <QuickSearch />
    </div>
  );
}
