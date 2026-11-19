"use client";

import { useTranslations } from "next-intl";
import { Link, usePathname } from "@/i18n/navigation";
import { navItems as items } from "./nav-items";

/** Floating dark pill, phones only. The active section is a lime capsule with its label. */
export function BottomNav() {
  const t = useTranslations("Nav");
  const pathname = usePathname();

  return (
    <nav
      aria-label={t("label")}
      className="fixed inset-x-4 z-40 mx-auto max-w-sm md:hidden"
      style={{ bottom: "calc(env(safe-area-inset-bottom) + 0.75rem)" }}
    >
      <ul className="flex items-center justify-between rounded-full bg-forest-950/95 p-1.5 shadow-float backdrop-blur">
        {items.map(({ key, href, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <li key={key}>
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                aria-label={t(key)}
                className={`flex h-12 items-center justify-center gap-2 rounded-full text-sm font-medium transition-all ${
                  active ? "bg-lime-400 px-5 text-forest-950" : "w-12 text-forest-100 hover:bg-white/10"
                }`}
              >
                <Icon className="size-5 shrink-0" aria-hidden />
                {active && <span>{t(key)}</span>}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
