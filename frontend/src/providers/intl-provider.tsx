"use client";

import { NextIntlClientProvider } from "next-intl";
import { useState, useEffect, useCallback, type ReactNode } from "react";
import { defaultLocale, locales, type Locale } from "@/i18n/config";
import enMessages from "@/messages/en.json";
import koMessages from "@/messages/ko.json";

const messagesMap: Record<Locale, typeof enMessages> = {
  en: enMessages,
  ko: koMessages,
};

function getStoredLocale(): Locale {
  if (typeof window === "undefined") return defaultLocale;
  const stored = document.cookie
    .split("; ")
    .find((row) => row.startsWith("locale="))
    ?.split("=")[1];
  if (stored && locales.includes(stored as Locale)) {
    return stored as Locale;
  }
  return defaultLocale;
}

export function IntlProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(defaultLocale);

  useEffect(() => {
    setLocale(getStoredLocale());
  }, []);

  useEffect(() => {
    const handleLocaleChange = () => setLocale(getStoredLocale());
    window.addEventListener("locale-change", handleLocaleChange);
    return () => window.removeEventListener("locale-change", handleLocaleChange);
  }, []);

  return (
    <NextIntlClientProvider locale={locale} messages={messagesMap[locale]}>
      {children}
    </NextIntlClientProvider>
  );
}
