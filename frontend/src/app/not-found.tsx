import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center p-6">
      <div className="flex flex-col items-center gap-6 text-center">
        <div className="flex flex-col items-center gap-2">
          <span className="text-8xl font-bold tracking-tight text-amber-500 dark:text-amber-400">
            404
          </span>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Page not found
          </h1>
        </div>
        <p className="max-w-md text-zinc-600 dark:text-zinc-400">
          The page you are looking for does not exist or has been moved.
        </p>
        <Button
          asChild
          className="bg-amber-500 hover:bg-orange-600 text-white dark:bg-amber-500 dark:hover:bg-orange-600"
        >
          <Link href="/">Go Home</Link>
        </Button>
      </div>
    </div>
  );
}
