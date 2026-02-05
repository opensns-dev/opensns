import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";

export default function Loading() {
  return (
    <div className="flex flex-col gap-6 p-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-4">
        <Skeleton className="h-10 w-10 rounded-md" />
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <div className="flex items-center gap-2">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
      </div>

      <Separator />

      <div className="flex flex-col gap-6">
        <div className="flex items-center gap-2 p-1 bg-muted rounded-lg w-fit">
          <Skeleton className="h-9 w-24" />
          <Skeleton className="h-9 w-24" />
          <Skeleton className="h-9 w-24" />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="rounded-lg border bg-card text-card-foreground shadow-sm overflow-hidden">
              <Skeleton className="aspect-square w-full" />
              <div className="p-4 space-y-2">
                <div className="flex justify-between">
                  <Skeleton className="h-5 w-20" />
                  <Skeleton className="h-4 w-12" />
                </div>
                <Skeleton className="h-4 w-3/4 mt-2" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
