import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-9 w-40" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-10 w-36" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="rounded-lg border bg-card shadow-sm p-6">
            <div className="flex items-center justify-between pb-2">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-8 w-8 rounded-lg" />
            </div>
            <Skeleton className="h-8 w-12 mb-1" />
            <Skeleton className="h-3 w-32" />
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border bg-card shadow-sm">
          <div className="flex flex-row items-center justify-between p-6">
            <div className="space-y-1">
              <Skeleton className="h-5 w-36" />
              <Skeleton className="h-4 w-48" />
            </div>
            <Skeleton className="h-8 w-20" />
          </div>
          <div className="p-6 pt-0 space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-lg border">
                <div className="flex-1 min-w-0 space-y-2">
                  <div className="flex items-center gap-2">
                    <Skeleton className="h-4 w-40" />
                    <Skeleton className="h-5 w-20" />
                  </div>
                  <Skeleton className="h-3 w-48" />
                </div>
                <Skeleton className="h-3 w-16 ml-4 shrink-0" />
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border bg-card shadow-sm">
          <div className="p-6 space-y-1">
            <Skeleton className="h-5 w-28" />
            <Skeleton className="h-4 w-40" />
          </div>
          <div className="p-6 pt-0 grid gap-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-center gap-4 p-4 rounded-lg border">
                <Skeleton className="h-10 w-10 rounded-lg shrink-0" />
                <div className="space-y-1">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-48" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-lg border bg-card shadow-sm lg:col-span-2">
        <div className="p-6 space-y-1">
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-4 w-56" />
        </div>
        <div className="p-6 pt-0">
          <div className="grid gap-4 md:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-start gap-3 p-4 rounded-lg bg-muted">
                <Skeleton className="h-10 w-10 rounded-lg shrink-0" />
                <div className="space-y-1">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-3 w-full" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
