"use client";

import { usePathname } from "next/navigation";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/app-sidebar";

export function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isOnboarding = pathname === "/onboarding";

  if (isOnboarding) {
    return (
      <div className="flex min-h-screen w-full flex-col">
        {children}
      </div>
    );
  }

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full">
        <AppSidebar />
        <main className="flex-1 overflow-auto bg-zinc-50 dark:bg-zinc-900">
          <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4 bg-white dark:bg-zinc-950">
            <SidebarTrigger className="-ml-1" />
          </header>
          <div className="flex flex-col">{children}</div>
        </main>
      </div>
    </SidebarProvider>
  );
}
