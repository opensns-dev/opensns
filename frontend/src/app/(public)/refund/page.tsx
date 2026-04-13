import Link from "next/link";

export default function RefundPage() {
  return (
    <div className="pt-32 pb-24 px-4 sm:px-6 lg:px-8">
      <article className="max-w-3xl mx-auto prose prose-zinc dark:prose-invert">
        <h1>Refund Policy</h1>
        <p className="text-sm text-zinc-500">Last updated: February 12, 2026</p>

        <p>
          We want you to be satisfied with the OpenSNS service. This Refund Policy
          outlines the terms under which refunds are available for subscriptions and
          credit pack purchases.
        </p>

        <h2>Subscription Refunds</h2>

        <h3>14-Day Refund Window</h3>
        <p>
          If you are not satisfied with your subscription, you may request a full refund
          within <strong>14 days</strong> of your initial purchase or renewal. The refund
          will be processed to your original payment method.
        </p>

        <h3>After 14 Days</h3>
        <p>
          Refund requests made after 14 days from purchase will be evaluated on a
          case-by-case basis. We may offer a prorated refund or credit toward future
          service depending on the circumstances.
        </p>

        <h3>Cancellation</h3>
        <p>
          You may cancel your subscription at any time. When you cancel, your subscription
          remains active until the end of the current billing period. No partial refunds
          are issued for the remaining days in a billing period when you cancel mid-cycle.
        </p>

        <h2>Credit Pack Refunds</h2>

        <h3>Unused Credits</h3>
        <p>
          Credit packs may be refunded in full if <strong>no credits from the pack have
          been used</strong>. You must request the refund within 14 days of purchase.
        </p>

        <h3>Partially Used Credits</h3>
        <p>
          Credit packs with partially or fully used credits are <strong>not eligible for
          refund</strong>. Once credits have been consumed to generate assets, the
          underlying computing resources have been used and cannot be recovered.
        </p>

        <h2>How to Request a Refund</h2>
        <p>To request a refund:</p>
        <ol>
          <li>
            Email us at{" "}
            <a href="mailto:support@opensns.dev">support@opensns.dev</a> with the
            subject line &quot;Refund Request&quot;
          </li>
          <li>Include your account email address and the reason for the refund</li>
          <li>We will review your request and respond within 3-5 business days</li>
        </ol>

        <h2>Refund Processing</h2>
        <p>
          All payments are processed by Lemon Squeezy, our Merchant of Record.
          Approved refunds are processed through Lemon Squeezy and typically appear on your
          statement within 5-10 business days, depending on your payment provider.
        </p>

        <h2>Exceptions</h2>
        <p>Refunds will not be granted in the following cases:</p>
        <ul>
          <li>Account termination due to violation of our Terms and Conditions</li>
          <li>Chargebacks filed without first contacting our support team</li>
          <li>Requests made more than 60 days after the original purchase</li>
        </ul>

        <h2>Self-Hosted Users</h2>
        <p>
          OpenSNS is open-source software available under the MIT License. Self-hosted
          instances do not involve any payments to OpenSNS, and therefore this Refund
          Policy does not apply.
        </p>

        <h2>Contact</h2>
        <p>
          For refund inquiries, please email{" "}
          <a href="mailto:support@opensns.dev">support@opensns.dev</a> or visit our{" "}
          <Link href="/contact/">Contact page</Link>.
        </p>
      </article>
    </div>
  );
}
