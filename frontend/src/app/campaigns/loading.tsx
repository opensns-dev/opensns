import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <div className="flex flex-col gap-6 p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <Skeleton className="h-9 w-40" />
        <Skeleton className="h-10 w-40" />
      </div>

      <div className="rounded-md border bg-white dark:bg-zinc-950">
        <div className="w-full">
          <div className="border-b">
            <div className="grid grid-cols-4 gap-4 p-4">
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16 ml-auto" />
            </div>
          </div>

          <div className="divide-y">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="grid grid-cols-4 gap-4 p-4 items-center">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-5 w-20" />
                <Skeleton className="h-4 w-24" />
                <div className="flex items-center justify-end gap-2">
                  <Skeleton className="h-8 w-12" />
                  <Skeleton className="h-8 w-8" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-48" />
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-8" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-8 w-8" />
        </div>
      </div>
    </div>
  );
}
