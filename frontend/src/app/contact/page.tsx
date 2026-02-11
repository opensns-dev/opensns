import Link from "next/link";
import Image from "next/image";
import { Mail, Github, MessageCircle, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-lg border-b border-zinc-200 dark:border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <Image src="/logo-icon.svg" alt="OpenSNS" width={32} height={32} className="w-8 h-8" />
              <span className="text-xl font-bold text-zinc-900 dark:text-white">OpenSNS</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link href="/pricing/" className="text-sm font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors">
                Pricing
              </Link>
              <Link href="/login/">
                <Button variant="ghost" size="sm">Sign In</Button>
              </Link>
              <Link href="/register/">
                <Button size="sm" className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white border-0">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="pt-32 pb-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-4xl font-extrabold text-zinc-900 dark:text-white tracking-tight mb-4">
            Contact Us
          </h1>
          <p className="text-lg text-zinc-600 dark:text-zinc-400 mb-12">
            Have questions, feedback, or need support? We&apos;re here to help.
          </p>

          <div className="space-y-6">
            <div className="p-6 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center shrink-0">
                  <Mail className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <h2 className="font-semibold text-zinc-900 dark:text-white mb-1">Email Support</h2>
                  <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
                    For general inquiries, billing questions, and technical support.
                  </p>
                  <a href="mailto:support@opensns.dev" className="text-amber-600 dark:text-amber-400 font-medium hover:underline">
                    support@opensns.dev
                  </a>
                </div>
              </div>
            </div>

            <div className="p-6 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
                  <Github className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h2 className="font-semibold text-zinc-900 dark:text-white mb-1">GitHub Issues</h2>
                  <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
                    Report bugs, request features, or contribute to the project.
                  </p>
                  <a
                    href="https://github.com/opensns-dev/opensns/issues"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 dark:text-blue-400 font-medium hover:underline"
                  >
                    github.com/opensns-dev/opensns/issues
                  </a>
                </div>
              </div>
            </div>

            <div className="p-6 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center shrink-0">
                  <MessageCircle className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <h2 className="font-semibold text-zinc-900 dark:text-white mb-1">Community</h2>
                  <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
                    Join our community for discussions, tips, and showcase.
                  </p>
                  <a
                    href="https://github.com/opensns-dev/opensns/discussions"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-purple-600 dark:text-purple-400 font-medium hover:underline"
                  >
                    GitHub Discussions
                  </a>
                </div>
              </div>
            </div>

            <div className="p-6 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center shrink-0">
                  <FileText className="h-5 w-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <h2 className="font-semibold text-zinc-900 dark:text-white mb-1">Documentation</h2>
                  <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
                    Comprehensive guides for setup, configuration, and usage.
                  </p>
                  <a
                    href="https://opensns-dev.github.io/opensns/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-green-600 dark:text-green-400 font-medium hover:underline"
                  >
                    opensns-dev.github.io/opensns
                  </a>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-12 p-6 rounded-xl bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800">
            <h3 className="font-semibold text-zinc-900 dark:text-white mb-2">Response Times</h3>
            <ul className="text-sm text-zinc-600 dark:text-zinc-400 space-y-1">
              <li>• Email support: within 24-48 business hours</li>
              <li>• GitHub issues: within 1-3 business days</li>
              <li>• Pro & Ultra plan holders receive priority support</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-zinc-200 dark:border-zinc-800">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <Image src="/logo-icon.svg" alt="OpenSNS" width={32} height={32} className="w-8 h-8" />
              <span className="text-lg font-bold text-zinc-900 dark:text-white">OpenSNS</span>
            </div>
            <div className="flex items-center gap-8 text-sm text-zinc-600 dark:text-zinc-400">
              <Link href="/terms/" className="hover:text-zinc-900 dark:hover:text-white transition-colors">Terms</Link>
              <Link href="/privacy/" className="hover:text-zinc-900 dark:hover:text-white transition-colors">Privacy</Link>
              <Link href="/refund/" className="hover:text-zinc-900 dark:hover:text-white transition-colors">Refund Policy</Link>
              <Link href="/contact/" className="hover:text-zinc-900 dark:hover:text-white transition-colors">Contact</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
