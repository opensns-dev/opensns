import Link from "next/link";
import Image from "next/image";

export function PublicFooter() {
  const sectionTitleClassName =
    "text-xs font-medium uppercase tracking-[0.18em] text-zinc-400 dark:text-zinc-500";
  const footerLinkClassName =
    "text-sm text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-300 transition-colors";

  return (
    <footer className="py-12 px-6 border-t border-zinc-200 dark:border-zinc-800/50">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col gap-10">
          <Link href="/" className="flex items-center gap-2 self-start">
            <Image
              src="/logo-icon.svg"
              alt="OpenSNS"
              width={20}
              height={20}
              className="w-5 h-5"
            />
            <span className="text-sm font-medium text-zinc-900 dark:text-white">
              OpenSNS
            </span>
          </Link>

          <div className="grid grid-cols-1 gap-10 sm:grid-cols-2 md:grid-cols-3">
            <div className="flex flex-col gap-4">
              <h3 className={sectionTitleClassName}>Product</h3>
              <div className="flex flex-col gap-3">
                <Link href="/pricing/" className={footerLinkClassName}>
                  Pricing
                </Link>
                <Link href="/docs/" className={footerLinkClassName}>
                  Docs (Getting Started)
                </Link>
                <Link
                  href="https://github.com/opensns-dev/opensns"
                  target="_blank"
                  className={footerLinkClassName}
                >
                  GitHub
                </Link>
              </div>
            </div>

            <div className="flex flex-col gap-4">
              <h3 className={sectionTitleClassName}>Resources</h3>
              <div className="flex flex-col gap-3">
                <Link href="/docs/blog/" className={footerLinkClassName}>
                  Blog
                </Link>
                <Link
                  href="/docs/compare/ai-ad-generators/"
                  className={footerLinkClassName}
                >
                  Compare Tools
                </Link>
                <Link
                  href="/docs/use-cases/ai-ads-for-agencies/"
                  className={footerLinkClassName}
                >
                  Use Cases
                </Link>
                <Link
                  href="/docs/alternatives/adcreative-ai-alternatives/"
                  className={footerLinkClassName}
                >
                  Alternatives
                </Link>
              </div>
            </div>

            <div className="flex flex-col gap-4">
              <h3 className={sectionTitleClassName}>Company</h3>
              <div className="flex flex-col gap-3">
                <Link href="/terms/" className={footerLinkClassName}>
                  Terms
                </Link>
                <Link href="/privacy/" className={footerLinkClassName}>
                  Privacy
                </Link>
                <Link href="/refund/" className={footerLinkClassName}>
                  Refund
                </Link>
                <Link href="/contact/" className={footerLinkClassName}>
                  Contact
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
