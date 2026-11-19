"use client";

import { useTranslations } from "next-intl";
import { Link, usePathname } from "@/i18n/navigation";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { Logo } from "./Logo";
import { navItems } from "./nav-items";

/**
 * Top bar.
 * Phone: logo + language switch only (navigation is the bottom bar).
 * md and up: logo, plain centred links, dark call-to-action (as in the landing reference).
 * `overlay` = sits on top of the landing photo instead of the page background.
 */
export function SiteHeader({ overlay = false }: { overlay?: boolean }) {
  const t = useTranslations("Nav");
  const tl = useTranslations("Landing");
  const pathname = usePathname();

  return (
    <header
      className={`z-30 w-full px-5 md:px-10 ${overlay ? "absolute inset-x-0 top-0" : "relative"}`}
      style={{ paddingTop: "calc(env(safe-area-inset-top) + 0.75rem)" }}
    >
      <div className="mx-auto grid max-w-7xl grid-cols-[1fr_auto] items-center gap-4 md:grid-cols-[1fr_auto_1fr] md:pt-3">
        <Logo className={overlay ? "text-white md:text-ink-900" : "text-forest-900"} />

        <nav aria-label={t("label")} className="hidden items-center gap-1 md:flex">
          {navItems.map(({ key, href }) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={key}
                href={href}
                aria-current={active ? "page" : undefined}
                className={`rounded-full px-4 py-1.5 font-display text-lg font-normal leading-8 transition ${
                  active ? "bg-forest-900 text-white" : "text-ink-900 [text-shadow:0_1px_8px_rgb(255_255_255/0.55)] hover:bg-white/60"
                }`}
              >
                {t(key)}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2 md:justify-self-end">
          <LanguageSwitcher
            className={
              overlay
                ? "glass-dark text-white md:border-white/70 md:bg-white/60 md:text-ink-900"
                : "border border-forest-900/10 bg-white/70 text-forest-900 hover:bg-white"
            }
          />
          <Link
            href="/discover"
            className="hidden h-10 items-center rounded-full bg-forest-950 px-5 text-sm font-medium text-white transition hover:bg-forest-800 md:inline-flex"
          >
            {tl("start")}
          </Link>
        </div>
      </div>
    </header>
  );
}
