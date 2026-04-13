import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Mail } from "lucide-react";

export default function ForgotPasswordPage() {
  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center p-6">
      <div className="flex flex-col items-center gap-6 text-center max-w-md">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/20">
          <Mail className="h-8 w-8 text-amber-600 dark:text-amber-400" />
        </div>
        <div className="flex flex-col items-center gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Password reset
          </h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            This feature is coming soon. Please contact support if you need to reset your password.
          </p>
        </div>
        <Button
          asChild
          variant="outline"
          className="border-zinc-300 hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800"
        >
          <Link href="/login">Back to login</Link>
        </Button>
      </div>
    </div>
  );
}
