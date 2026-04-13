import Link from "next/link";

export default function TermsPage() {
  return (
    <div className="pt-32 pb-24 px-4 sm:px-6 lg:px-8">
      <article className="max-w-3xl mx-auto prose prose-zinc dark:prose-invert">
        <h1>Terms and Conditions</h1>
        <p className="text-sm text-zinc-500">Last updated: February 12, 2026</p>

        <p>
          These Terms and Conditions (&quot;Terms&quot;) govern your use of the OpenSNS platform
          (&quot;Service&quot;), operated by OpenSNS (&quot;Company&quot;, &quot;we&quot;, &quot;us&quot;, or &quot;our&quot;).
          By accessing or using our Service, you agree to be bound by these Terms.
        </p>

        <h2>1. Service Description</h2>
        <p>
          OpenSNS is a marketing automation platform that helps businesses create
          ad creatives, marketing copy, and campaign assets. The Service provides tools
          for product analysis, competitor research, strategy generation, and multi-platform
          ad asset creation.
        </p>

        <h2>2. Account Registration</h2>
        <p>
          To use certain features, you must create an account by providing a valid email
          address and password. You are responsible for maintaining the confidentiality of
          your credentials and for all activities under your account.
        </p>

        <h2>3. Acceptable Use</h2>
        <p>You agree not to:</p>
        <ul>
          <li>Use the Service for any illegal purpose or to violate any laws</li>
          <li>Generate content that is defamatory, obscene, or infringes on third-party rights</li>
          <li>Attempt to reverse engineer, decompile, or disassemble any part of the Service</li>
          <li>Use automated means to access the Service beyond the provided API</li>
          <li>Share your account credentials with unauthorized parties</li>
          <li>Resell or redistribute generated content as a competing service</li>
        </ul>

        <h2>4. Subscription and Billing</h2>
        <p>
          The Service offers subscription plans (Free, Basic, BYOK, Pro, Ultra) and credit packs.
          All payments are processed by Lemon Squeezy, Inc. (&quot;Lemon Squeezy&quot;), our Merchant of
          Record, who handles billing, taxes, and payment compliance on our behalf.
        </p>
        <p>
          Subscription fees are billed monthly in advance. You may upgrade, downgrade, or
          cancel your subscription at any time. Downgrades and cancellations take effect at
          the end of the current billing period.
        </p>

        <h2>5. Credits</h2>
        <p>
          Credits are the currency used to generate marketing assets within the Service.
          Monthly plan credits reset at the start of each billing cycle. Bonus credits
          purchased via credit packs do not expire and carry over between billing periods.
          Credits have no cash value and are non-transferable.
        </p>

        <h2>6. Intellectual Property</h2>
        <p>
          Content generated using the Service belongs to you, subject to the following:
        </p>
        <ul>
          <li>You retain ownership of all input content (product URLs, descriptions, etc.)</li>
          <li>Generated marketing assets are licensed to you for commercial use</li>
          <li>The OpenSNS platform, code, and branding remain our intellectual property</li>
          <li>OpenSNS is open-source software under the MIT License</li>
        </ul>

        <h2>7. Third-Party Services</h2>
        <p>
          The Service integrates with third-party providers for AI processing (such as
          OpenAI, Fal.ai), payment processing (Lemon Squeezy), and other functionality. Your use
          of these integrations is subject to the respective third-party terms of service.
        </p>

        <h2>8. Limitation of Liability</h2>
        <p>
          To the fullest extent permitted by law, the Service is provided &quot;as is&quot; and &quot;as
          available&quot; without warranties of any kind. We shall not be liable for any
          indirect, incidental, special, consequential, or punitive damages arising from
          your use of the Service.
        </p>
        <p>
          Our total liability for any claims arising from these Terms or your use of the
          Service shall not exceed the amount you paid to us in the 12 months preceding the
          claim.
        </p>

        <h2>9. Service Availability</h2>
        <p>
          We strive to maintain high availability but do not guarantee uninterrupted
          access. We may modify, suspend, or discontinue any part of the Service at any
          time with reasonable notice.
        </p>

        <h2>10. Termination</h2>
        <p>
          We may terminate or suspend your account if you violate these Terms. You may
          close your account at any time by contacting us. Upon termination, your right to
          use the Service ceases immediately, but provisions that by their nature should
          survive (such as liability limitations) will remain in effect.
        </p>

        <h2>11. Changes to These Terms</h2>
        <p>
          We may update these Terms from time to time. We will notify you of material
          changes by posting the updated Terms on this page with a new effective date.
          Continued use of the Service after changes constitutes acceptance of the
          modified Terms.
        </p>

        <h2>12. Governing Law</h2>
        <p>
          These Terms are governed by and construed in accordance with applicable law.
          Any disputes shall be resolved through good-faith negotiation, and if necessary,
          through binding arbitration.
        </p>

        <h2>13. Contact</h2>
        <p>
          If you have questions about these Terms, please contact us at{" "}
          <a href="mailto:support@opensns.dev">support@opensns.dev</a> or visit
          our <Link href="/contact/">Contact page</Link>.
        </p>
      </article>
    </div>
  );
}
