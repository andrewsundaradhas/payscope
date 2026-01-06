"use client";

import { DashboardProvider } from "@/app/dashboard/DashboardProvider";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";

export function DashboardShell({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <DashboardProvider>
      <div className="flex h-screen w-screen overflow-hidden bg-[#FAFAFA]">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <TopBar />
          <main className="min-w-0 flex-1 overflow-auto bg-[#FAFAFA] px-6 py-6">
            {children}
          </main>
        </div>
      </div>
    </DashboardProvider>
  );
}
