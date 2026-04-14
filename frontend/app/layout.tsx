import type { Metadata } from "next";
import { ReactNode } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { appConfig } from "@/lib/config";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: {
    default: appConfig.name,
    template: `%s · ${appConfig.name}`,
  },
  description: appConfig.description,
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
