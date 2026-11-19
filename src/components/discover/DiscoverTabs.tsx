"use client";

import { Compass, TrendingUp } from "lucide-react";
import { useTranslations } from "next-intl";
import { Link, usePathname } from "@/i18n/navigation";

/** Switch between the two Discover pages: places and economic opportunities. */
export function DiscoverTabs() {
  const t = useTranslations("Discover");
  const pathname = usePathname();
  const onOpportunities = pathname.startsWith("/discover/opportunities");
  const tabs = [
    { href: "/discover", label: t("tabs.places"), icon: Compass, active: !onOpportunities },
    { href: "/discover/opportunities", label: t("tabs.opportunities"), icon: TrendingUp, active: onOpportunities },
  ] as const;

  return (
    <nav aria-label={t("tabs.label")} className="mt-5">
      <ul className="inline-flex rounded-full bg-white/85 p-1 shadow-soft">
        {tabs.map(({ href, label, icon: Icon, active }) => (
          <li key={href}>
            <Link
              href={href}
              aria-current={active ? "page" : undefined}
              className={`inline-flex h-10 items-center gap-2 rounded-full px-4 text-sm font-medium transition ${
                active ? "bg-forest-950 text-white" : "text-ink-700 hover:bg-mist-100"
              }`}
            >
              <Icon className="size-4" aria-hidden />
              {label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
