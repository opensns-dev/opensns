import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/dashboard/", "/campaigns/", "/settings/", "/assets/", "/logs/", "/api/"],
      },
    ],
    sitemap: "https://opensns.pages.dev/sitemap.xml",
  };
}
