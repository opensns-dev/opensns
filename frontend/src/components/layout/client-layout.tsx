"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { ErrorBoundary } from "@/components/error-boundary";
import { useAuth } from "@/contexts/auth-context";

const PUBLIC_ROUTES = ["/", "/login", "/register", "/onboarding", "/auth/verify", "/auth/google/callback", "/pricing", "/terms", "/privacy", "/refund", "/contact"];

function isPublicPath(pathname: string): boolean {
  const normalized = pathname.endsWith("/") && pathname !== "/" ? pathname.slice(0, -1) : pathname;
  return PUBLIC_ROUTES.some(
    (route) => normalized === route || pathname.startsWith(route + "/")
  );
}

export function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  
  const isPublicRoute = isPublicPath(pathname);

  useEffect(() => {
    if (!isLoading && !isAuthenticated && !isPublicRoute) {
      router.replace("/login/");
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
      <div className="flex min-h-screen w-full items-center justify-center bg-zinc-50 dark:bg-zinc-900">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-zinc-200 border-t-amber-500 dark:border-zinc-700 dark:border-t-amber-500" />
          <span className="text-sm text-muted-foreground">Loading...</span>
        </div>
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
          <div className="flex flex-col">
            <ErrorBoundary>{children}</ErrorBoundary>
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}
