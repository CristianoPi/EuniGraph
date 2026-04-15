import { ReactNode } from "react";

import { AdminNav } from "@/components/admin/admin-nav";

type AdminLayoutProps = {
  children: ReactNode;
};

export default function AdminLayout({ children }: AdminLayoutProps) {
  return (
    <div className="space-y-6">
      <AdminNav />
      {children}
    </div>
  );
}
