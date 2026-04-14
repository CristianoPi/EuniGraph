import { ReactNode } from "react";

import { EntitiesNav } from "@/components/entities/entities-nav";

type EntitiesLayoutProps = {
  children: ReactNode;
};

export default function EntitiesLayout({ children }: EntitiesLayoutProps) {
  return (
    <div className="space-y-6">
      <EntitiesNav />
      {children}
    </div>
  );
}
