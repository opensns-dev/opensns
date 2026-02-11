import Link from "next/link";
import Image from "next/image";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-lg border-b border-zinc-200 dark:border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <Image src="/logo-icon.svg" alt="OpenSNS" width={32} height={32} className="w-8 h-8" />
              <span className="text-xl font-bold text-zinc-900 dark:text-white">OpenSNS</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link href="/pricing/" className="text-sm font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors">Pricing</Link>
              <Link href="/login/"><span className="text-sm font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors">Sign In</span></Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="pt-32 pb-24 px-4 sm:px-6 lg:px-8">
        <article className="max-w-3xl mx-auto prose prose-zinc dark:prose-invert">
          <h1>Privacy Policy</h1>
          <p className="text-sm text-zinc-500">Last updated: February 12, 2026</p>

          <p>
            OpenSNS (&quot;Company&quot;, &quot;we&quot;, &quot;us&quot;, or &quot;our&quot;) is committed to protecting your
            privacy. This Privacy Policy describes how we collect, use, and share your
            personal information when you use the OpenSNS platform (&quot;Service&quot;).
          </p>

          <h2>1. Information We Collect</h2>

          <h3>Account Information</h3>
          <ul>
            <li>Email address (required for account creation)</li>
            <li>Password (stored securely using bcrypt hashing)</li>
            <li>Name (if provided)</li>
          </ul>

          <h3>Usage Data</h3>
          <ul>
            <li>Campaign data (product URLs, generated content, settings)</li>
            <li>Credit usage and billing history</li>
            <li>Feature usage patterns and preferences</li>
            <li>Log data (IP address, browser type, access times)</li>
          </ul>

          <h3>Payment Information</h3>
          <p>
            Payment processing is handled entirely by Paddle.com Market Ltd, our Merchant
            of Record. We do not store credit card numbers, bank details, or other payment
            credentials. Paddle collects and processes payment information in accordance
            with their own{" "}
            <a href="https://www.paddle.com/legal/privacy" target="_blank" rel="noopener noreferrer">
              Privacy Policy
            </a>.
          </p>

          <h2>2. How We Use Your Information</h2>
          <ul>
            <li>To provide and maintain the Service</li>
            <li>To process your campaigns and generate marketing assets</li>
            <li>To manage your account and subscription</li>
            <li>To communicate with you about service updates and support</li>
            <li>To improve the Service and develop new features</li>
            <li>To detect and prevent fraud or abuse</li>
          </ul>

          <h2>3. Third-Party Services</h2>
          <p>We use the following third-party services to operate the platform:</p>
          <ul>
            <li><strong>Paddle</strong> — Payment processing and billing (Merchant of Record)</li>
            <li><strong>OpenAI</strong> — Text generation for marketing copy and strategy</li>
            <li><strong>Fal.ai</strong> — Image and video generation</li>
            <li><strong>Google OAuth</strong> — Optional social login (if you choose to sign in with Google)</li>
          </ul>
          <p>
            Each third-party service processes data in accordance with their respective
            privacy policies. We only share the minimum data necessary for each service
            to function.
          </p>

          <h2>4. Data Storage and Security</h2>
          <ul>
            <li>Your data is stored on secure servers with encryption at rest</li>
            <li>API keys you provide for AI services are encrypted using AES encryption</li>
            <li>We use HTTPS for all data transmission</li>
            <li>Access to production data is restricted to authorized personnel</li>
          </ul>

          <h2>5. Data Retention</h2>
          <p>
            We retain your account data for as long as your account is active. Campaign
            data and generated assets are retained until you delete them or close your
            account. Upon account deletion, we remove your personal data within 30 days,
            except where retention is required by law.
          </p>

          <h2>6. Your Rights</h2>
          <p>Depending on your jurisdiction, you may have the right to:</p>
          <ul>
            <li><strong>Access</strong> — Request a copy of the personal data we hold about you</li>
            <li><strong>Correction</strong> — Request correction of inaccurate data</li>
            <li><strong>Deletion</strong> — Request deletion of your personal data</li>
            <li><strong>Portability</strong> — Request your data in a machine-readable format</li>
            <li><strong>Restriction</strong> — Request restriction of processing</li>
            <li><strong>Objection</strong> — Object to processing based on legitimate interests</li>
          </ul>
          <p>
            To exercise any of these rights, contact us at{" "}
            <a href="mailto:support@opensns.dev">support@opensns.dev</a>.
          </p>

          <h2>7. Cookies</h2>
          <p>
            We use essential cookies for authentication and session management. These are
            necessary for the Service to function and cannot be disabled. We do not use
            advertising or tracking cookies.
          </p>

          <h2>8. International Data Transfers</h2>
          <p>
            Your data may be processed in countries other than your own. We ensure
            appropriate safeguards are in place for international data transfers in
            compliance with applicable data protection laws.
          </p>

          <h2>9. Children&apos;s Privacy</h2>
          <p>
            The Service is not directed to individuals under 16 years of age. We do not
            knowingly collect personal data from children. If we learn that we have
            collected data from a child, we will delete it promptly.
          </p>

          <h2>10. Changes to This Policy</h2>
          <p>
            We may update this Privacy Policy from time to time. We will notify you of
            material changes by posting the updated policy on this page with a new
            effective date.
          </p>

          <h2>11. Contact</h2>
          <p>
            For questions about this Privacy Policy or your personal data, contact us at{" "}
            <a href="mailto:support@opensns.dev">support@opensns.dev</a> or visit our{" "}
            <Link href="/contact/">Contact page</Link>.
          </p>
        </article>
      </div>

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
