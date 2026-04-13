import Link from "next/link";
import Image from "next/image";
import { ThemeToggle } from "@/components/layout/theme-toggle";

export function PublicNav() {
  const navLinkClassName =
    "text-sm text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors";

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-sm dark:bg-transparent">
      <div className="max-w-6xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-6">
            <Link href="/pricing/" className={navLinkClassName}>
              Pricing
            </Link>
            <Link href="/docs/" className={navLinkClassName}>
              Docs
            </Link>
            <Link href="/docs/blog/" className={navLinkClassName}>
              Blog
            </Link>
            <Link
              href="/docs/compare/ai-ad-generators/"
              className={navLinkClassName}
            >
              Compare
            </Link>
          </div>

          <Link href="/" className="flex items-center gap-2">
            <Image
              src="/logo-icon.svg"
              alt="OpenSNS"
              width={22}
              height={22}
              className="w-[22px] h-[22px]"
            />
            <span className="text-sm font-medium text-zinc-900 dark:text-white">
              OpenSNS
            </span>
          </Link>

          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Link
              href="https://github.com/opensns-dev/opensns"
              target="_blank"
              className="flex items-center gap-2 text-sm text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors"
            >
              <svg
                viewBox="0 0 24 24"
                width="16"
                height="16"
                fill="currentColor"
                className="w-4 h-4"
              >
                <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.163 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
              </svg>
              <span>Star</span>
              <span className="text-zinc-400 dark:text-zinc-500">GitHub</span>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
