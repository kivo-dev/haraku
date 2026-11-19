import { ArrowRight, MapPin } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import type { CSSProperties } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SlotImage } from "@/components/ui/SlotImage";
import { Link } from "@/i18n/navigation";
import { imageSlots } from "@/lib/images";
import { categoryIcons, pick, samplePlaces } from "@/lib/places";
import { LandingSearch } from "./LandingSearch";

/**
 * First screen, following the two references.
 * Phone: dark foggy photo, text at the bottom-start, a dark pill with a lime "Get started".
 * Desktop: bright sunrise haze on top, centred headline + search pill, dark ground at the bottom.
 */
export function Landing() {
  const t = useTranslations("Landing");
  const locale = useLocale();
  const rise = (i: number) => ({ "--i": i }) as CSSProperties;

  return (
    <div className="relative isolate flex min-h-dvh flex-col overflow-hidden bg-forest-950">
      {/* Phone photo (portrait) and desktop photo (wide): only the visible one is downloaded. */}
      <SlotImage
        src={imageSlots.landingHeroMobile.src}
        alt=""
        tone="fog"
        className="absolute inset-0 -z-20 md:hidden"
      />
      <SlotImage
        src={imageSlots.landingHero.src}
        alt=""
        tone="dawn"
        position="50% 60%"
        className="absolute inset-0 -z-20 hidden md:block"
      />
      <div aria-hidden className="absolute inset-0 -z-10 bg-gradient-to-t from-forest-950/95 via-forest-950/35 to-transparent md:hidden" />
      <div
        aria-hidden
        className="absolute inset-0 -z-10 hidden bg-[linear-gradient(to_bottom,rgb(255_250_243/0.55),rgb(255_246_236/0.2)_38%,rgb(255_246_236/0)_58%,rgb(11_34_29/0.88))] md:block"
      />

      <SiteHeader overlay />

      <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col justify-end px-6 pb-8 pt-28 md:items-center md:justify-center md:pb-12 md:text-center">
        <p
          className="rise glass-dark inline-flex w-fit items-center gap-2 rounded-full px-3.5 py-1.5 text-sm text-white md:border-white/70 md:bg-white/55 md:text-forest-900"
          style={rise(0)}
        >
          <MapPin className="size-4" aria-hidden />
          {t("badge")}
        </p>

        <h1
          className="rise mt-5 font-display text-[2.7rem] font-normal leading-[1.4] text-white [text-shadow:0_2px_3px_rgb(0_0_0/0.3),0_6px_34px_rgb(0_0_0/0.45)] md:text-[4.75rem] md:leading-[1.3]"
          style={rise(1)}
        >
          {t("title1")}
          <br />
          <span>{t("title2")}</span>
        </h1>

        <p className="rise mt-4 max-w-sm text-[0.95rem] leading-7 text-white/90 [text-shadow:0_1px_12px_rgb(0_0_0/0.5)] md:max-w-md md:text-base" style={rise(2)}>
          {t("subtitle")}
        </p>

        <div className="rise mt-7 w-full md:flex md:justify-center" style={rise(3)}>
          <div className="hidden w-full justify-center md:flex">
            <LandingSearch />
          </div>
          {/* Phone: dark pill, arrow at the start, lime button at the end */}
          <Link
            href="/discover"
            className="glass-dark flex h-16 items-center justify-between rounded-full p-2 ps-6 text-white md:hidden"
          >
            <ArrowRight className="size-5 rtl:rotate-180" aria-hidden />
            <span className="flex h-12 items-center rounded-full bg-lime-400 px-7 font-semibold text-forest-950">{t("start")}</span>
          </Link>
        </div>
      </div>

      <div className="rise mx-auto hidden w-full max-w-4xl px-6 pb-9 text-center md:block" style={rise(4)}>
        <p className="text-sm text-white/80">{t("suggested")}</p>
        <ul className="mt-3 flex flex-wrap justify-center gap-2">
          {samplePlaces.map((p) => {
            const Icon = categoryIcons[p.category];
            return (
              <li key={p.id}>
                <Link
                  href={`/discover/${p.id}`}
                  className="glass-dark inline-flex h-10 items-center gap-2 rounded-full px-4 text-sm text-white transition hover:bg-white/25"
                >
                  <Icon className="size-4" aria-hidden />
                  {pick(p.name, locale)}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
