import Link from "next/link";
import { Mail, Github, MessageCircle, FileText } from "lucide-react";

export default function ContactPage() {
  return (
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
  );
}
