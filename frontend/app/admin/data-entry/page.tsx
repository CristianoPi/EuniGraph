import { ManualDataEntry } from "@/components/admin/manual-data-entry";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminDataEntryPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Manual Data Entry"
        title="Manual data entry."
        description="Create canonical records through the existing backend APIs."
      />

      <ManualDataEntry />
    </div>
  );
}
