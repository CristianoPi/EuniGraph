import { OperationsConsole } from "@/components/admin/operations-console";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminOperationsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin Operations"
        title="Workflow controls."
        description="Seed, normalize, embed and rebuild graphs from one place."
      />

      <OperationsConsole />
    </div>
  );
}
