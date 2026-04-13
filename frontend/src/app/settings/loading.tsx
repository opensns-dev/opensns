import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";

export default function Loading() {
  return (
    <div className="container max-w-3xl py-8 space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-8 w-24" />
        <Skeleton className="h-4 w-72" />
      </div>

      <div className="rounded-lg border bg-card shadow-sm">
        <div className="p-6 space-y-1">
          <div className="flex items-center gap-2">
            <Skeleton className="h-5 w-5" />
            <Skeleton className="h-5 w-40" />
          </div>
          <Skeleton className="h-4 w-64" />
        </div>
        <Separator />
        <div className="p-6">
          <Skeleton className="h-10 w-32" />
        </div>
      </div>

      <div className="rounded-lg border bg-card shadow-sm">
        <div className="p-6 space-y-1">
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-4 w-56" />
        </div>
        <Separator />
        <div className="p-6 space-y-4">
          <Skeleton className="h-4 w-12" />
          <div className="flex gap-2">
            <Skeleton className="h-9 w-24" />
            <Skeleton className="h-9 w-24" />
            <Skeleton className="h-9 w-28" />
          </div>
        </div>
      </div>

      <div className="rounded-lg border bg-card shadow-sm">
        <div className="p-6 space-y-1">
          <Skeleton className="h-5 w-20" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Separator />
        <div className="p-6 space-y-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="space-y-3">
              <div className="flex items-center gap-2">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-5 w-20" />
              </div>
              <div className="flex gap-2">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-20" />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-lg border bg-card shadow-sm">
        <div className="p-6 space-y-1">
          <Skeleton className="h-5 w-28" />
          <Skeleton className="h-4 w-72" />
        </div>
        <Separator />
        <div className="p-6 space-y-4">
          <div className="space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-10 w-full" />
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-10 w-full" />
          </div>
        </div>
      </div>

      <div className="rounded-lg border bg-card shadow-sm">
        <div className="p-6 space-y-1">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Separator />
        <div className="p-6 space-y-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-10 w-full" />
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-lg border bg-card shadow-sm">
        <div className="p-6 space-y-1">
          <Skeleton className="h-5 w-28" />
          <Skeleton className="h-4 w-56" />
        </div>
        <Separator />
        <div className="p-6 space-y-6">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-10 w-full" />
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-4">
        <Skeleton className="h-10 w-32" />
        <Skeleton className="h-10 w-36" />
      </div>
    </div>
  );
}
