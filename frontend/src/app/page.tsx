import type { Metadata } from "next";
import { LandingContent } from "./landing-content";

export const metadata: Metadata = {
  title: "OpenSNS - Open-Source AI Marketing Agent Platform",
  description:
    "Self-hostable AI marketing agent that generates ad creatives from a product URL. Open-source alternative to Zet AI and AdCreative.ai.",
  alternates: {
    canonical: "https://opensns.pages.dev/",
  },
  openGraph: {
    title: "OpenSNS - Open-Source AI Marketing Agent Platform",
    description:
      "Self-hostable AI marketing agent that generates ad creatives from a product URL. 100% open-source.",
    url: "https://opensns.pages.dev/",
    type: "website",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "OpenSNS - Open-Source AI Marketing Agent Platform",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "OpenSNS - Open-Source AI Marketing Agent",
    description:
      "Self-hostable AI marketing agent that generates ad creatives from a product URL.",
    images: ["/og-image.png"],
  },
};

const organizationJsonLd = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "OpenSNS",
  url: "https://opensns.pages.dev",
  logo: "https://opensns.pages.dev/logo-icon.svg",
  sameAs: [
    "https://github.com/opensns-dev/opensns",
    "https://twitter.com/opensns_dev",
  ],
};

const softwareJsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "OpenSNS",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  url: "https://opensns.pages.dev",
  description:
    "Open-source AI marketing agent that generates ad creatives from a product URL.",
  offers: [
    {
      "@type": "Offer",
      name: "Free",
      price: "0",
      priceCurrency: "USD",
      description: "50 credits/month. Try it out.",
    },
    {
      "@type": "Offer",
      name: "Basic",
      price: "9",
      priceCurrency: "USD",
      description: "150 credits/month for indie marketers.",
    },
    {
      "@type": "Offer",
      name: "BYOK",
      price: "15",
      priceCurrency: "USD",
      description: "Unlimited generations with your own API keys.",
    },
    {
      "@type": "Offer",
      name: "Pro",
      price: "29",
      priceCurrency: "USD",
      description: "500 credits/month for growing teams.",
    },
    {
      "@type": "Offer",
      name: "Ultra",
      price: "59",
      priceCurrency: "USD",
      description: "1,200 credits/month for agencies.",
    },
  ],
};

export default function LandingPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareJsonLd) }}
      />
      <LandingContent />
    </>
  );
}
