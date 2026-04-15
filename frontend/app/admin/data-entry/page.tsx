import { ManualDataEntry } from "@/components/admin/manual-data-entry";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminDataEntryPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Manual Data Entry"
        title="Create canonical entities without direct API calls."
        description="These forms call the existing manual entity management APIs and preserve backend provenance through the manual_api_entry source."
      />

      <ManualDataEntry />
    </div>
  );
}
