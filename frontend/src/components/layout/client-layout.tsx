"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { useAuth } from "@/contexts/auth-context";

const PUBLIC_ROUTES = ["/", "/login", "/register", "/onboarding", "/auth/verify", "/auth/google/callback"];

export function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  
  const isPublicRoute = PUBLIC_ROUTES.includes(pathname);

  useEffect(() => {
    if (!isLoading && !isAuthenticated && !isPublicRoute) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, isPublicRoute, router]);

  if (isPublicRoute) {
    return (
      <div className="flex min-h-screen w-full flex-col">
        {children}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen w-full items-center justify-center">
        <div className="animate-pulse text-zinc-500 font-medium">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
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
