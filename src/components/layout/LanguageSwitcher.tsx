"use client";

import { Languages } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { Link, usePathname } from "@/i18n/navigation";

/** Colours come from `className` so it works on light and on photo backgrounds. */
export function LanguageSwitcher({ className = "" }: { className?: string }) {
  const t = useTranslations("Language");
  const locale = useLocale();
  const pathname = usePathname();
  const target = locale === "fa" ? "en" : "fa";

  return (
    <Link
      href={pathname}
      locale={target}
      hrefLang={target}
      aria-label={t("label")}
      className={`inline-flex h-10 items-center gap-2 rounded-full px-4 text-sm font-medium transition ${className}`}
    >
      <Languages className="size-4" aria-hidden />
      {t("switchTo")}
    </Link>
  );
}
