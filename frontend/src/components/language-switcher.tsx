"use client";

import { useLocale, useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { locales, type Locale } from "@/i18n/config";

function setLocaleCookie(locale: Locale) {
  document.cookie = `locale=${locale};path=/;max-age=${365 * 24 * 60 * 60};SameSite=Lax`;
  window.dispatchEvent(new Event("locale-change"));
}

const FLAG_MAP: Record<Locale, string> = {
  en: "🇺🇸",
  ko: "🇰🇷",
};

export function LanguageSwitcher() {
  const currentLocale = useLocale() as Locale;
  const t = useTranslations("language");
  const nextLocale = locales.find((l) => l !== currentLocale) ?? locales[0];

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => setLocaleCookie(nextLocale)}
    >
      {FLAG_MAP[nextLocale]} {t(nextLocale)}
    </Button>
  );
}
