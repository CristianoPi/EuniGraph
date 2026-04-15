import { OperationsConsole } from "@/components/admin/operations-console";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminOperationsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin Operations"
        title="Run backend workflows from one controlled console."
        description="Seed, normalization, embeddings and graph build operations are grouped here because they change system state or materialized artifacts."
      />

      <OperationsConsole />
    </div>
  );
}
