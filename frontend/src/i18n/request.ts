import { getRequestConfig } from "next-intl/server";
import { cookies } from "next/headers";
import { locales, defaultLocale } from "./config";
import type { Locale } from "./config";

export default getRequestConfig(async () => {
  let locale: Locale = defaultLocale;

  try {
    const cookieStore = await cookies();
    const cookieLocale = cookieStore.get("locale")?.value;
    if (cookieLocale && locales.includes(cookieLocale as Locale)) {
      locale = cookieLocale as Locale;
    }
  } catch {
    // cookies() unavailable in static export — fallback to default
  }

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
