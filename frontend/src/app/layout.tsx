import type { Metadata } from "next";
import { Geist, Geist_Mono, Instrument_Serif, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/providers/query-provider";
import { ThemeProvider } from "@/providers/theme-provider";
import { IntlProvider } from "@/providers/intl-provider";
import { AuthProvider } from "@/contexts/auth-context";
import { ClientLayout } from "@/components/layout/client-layout";
import { Toaster } from "sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const instrumentSerif = Instrument_Serif({
  variable: "--font-serif",
  subsets: ["latin"],
  weight: "400",
  style: ["normal", "italic"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono-jb",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "OpenSNS - Open-Source AI Marketing Agent Platform",
    template: "%s | OpenSNS",
  },
  description:
    "Self-hostable AI marketing agent that generates ad creatives from a product URL. Open-source alternative to Zet AI and AdCreative.ai.",
  keywords: [
    "AI ad generator",
    "AI marketing agent",
    "open source ad creative",
    "self-hosted marketing AI",
    "AdCreative.ai alternative",
    "Zet AI alternative",
    "AI UGC video",
    "Naver ad automation",
  ],
  metadataBase: new URL("https://opensns.pages.dev"),
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://opensns.pages.dev",
    siteName: "OpenSNS",
    title: "OpenSNS - Open-Source AI Marketing Agent Platform",
    description:
      "Self-hostable AI marketing agent that generates ad creatives from a product URL. 100% open-source.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "OpenSNS - Open-Source AI Marketing Agent",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "OpenSNS - Open-Source AI Marketing Agent",
    description:
      "Self-hostable AI marketing agent that generates ad creatives from a product URL.",
    images: ["/og-image.png"],
    creator: "@opensns_dev",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${instrumentSerif.variable} ${inter.variable} ${jetbrainsMono.variable} antialiased`}
      >
        <ThemeProvider>
          <IntlProvider>
            <QueryProvider>
              <AuthProvider>
                <ClientLayout>{children}</ClientLayout>
              </AuthProvider>
            </QueryProvider>
          </IntlProvider>
          <Toaster richColors position="top-right" />
        </ThemeProvider>
      </body>
    </html>
  );
}
