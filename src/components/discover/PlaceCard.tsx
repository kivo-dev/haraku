import { ArrowRight, MapPin, Star } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { SlotImage } from "@/components/ui/SlotImage";
import { Link } from "@/i18n/navigation";
import { placeImageSrc } from "@/lib/images";
import { categoryArt, categoryIcons, pick, type Place } from "@/lib/places";
import { FavoriteButton } from "./FavoriteButton";

/**
 * Two card shapes, both photo-first (see the second reference):
 *  - "wide": big card in the horizontal carousel, with a round lime arrow
 *  - "tile": the equal-size card of the grid, with a star to save the place
 * The whole card opens the place through the title link (stretched with ::after);
 * the star sits above it, so links and buttons stay valid.
 */
export function PlaceCard({ place, variant = "tile", priority = false }: { place: Place; variant?: "wide" | "tile"; priority?: boolean }) {
  const locale = useLocale();
  const tc = useTranslations("Categories");
  const Icon = categoryIcons[place.category];
  const name = pick(place.name, locale);
  const area = pick(place.area, locale);
  const wide = variant === "wide";

  return (
    <article
      className={`group relative isolate overflow-hidden rounded-4xl bg-forest-900 shadow-soft ${
        wide ? "aspect-[16/9] w-full" : "aspect-[5/6] w-full"
      }`}
    >
      <SlotImage
        src={placeImageSrc(place.id, place.image)}
        alt=""
        tone={categoryArt[place.category]}
        priority={priority}
        className="absolute inset-0 -z-10 transition-transform duration-700 group-hover:scale-[1.04]"
      />
      <div aria-hidden className="absolute inset-0 -z-10 bg-gradient-to-t from-forest-950/80 via-forest-950/10 to-transparent" />

      <div className="flex h-full flex-col justify-between p-3.5">
        <div className="flex items-start justify-between gap-2">
          <span className="glass inline-flex h-7 items-center gap-1.5 rounded-full px-2.5 text-xs font-medium text-forest-900">
            <Icon className="size-3.5" aria-hidden />
            {tc(place.category)}
          </span>
          {!wide && <FavoriteButton id={place.id} className="relative z-10 shrink-0" />}
        </div>

        <div className="flex items-end justify-between gap-3">
          <div className="min-w-0 text-white">
            <h3 className={`font-semibold leading-snug ${wide ? "text-xl" : "text-base"}`}>
              <Link href={`/discover/${place.id}`} className="after:absolute after:inset-0 after:content-['']">
                {name}
              </Link>
            </h3>
            {wide && place.reason && <p className="mt-1 line-clamp-1 text-sm text-white/90">{pick(place.reason, locale)}</p>}
            <p className="mt-1.5 flex items-center gap-3 text-xs text-white/85">
              {area && (
                <span className="flex min-w-0 items-center gap-1">
                  <MapPin className="size-3.5 shrink-0" aria-hidden />
                  <span className="truncate">{area}</span>
                </span>
              )}
              {place.rating && (
                <span className="flex shrink-0 items-center gap-1">
                  <Star className="size-3.5 fill-lime-400 text-lime-400" aria-hidden />
                  {place.rating.toFixed(1)}
                </span>
              )}
            </p>
          </div>
          {wide && (
            <span
              aria-hidden
              className="flex size-11 shrink-0 items-center justify-center rounded-full bg-lime-400 text-forest-950 transition group-hover:bg-lime-300"
            >
              <ArrowRight className="size-5 rtl:rotate-180" />
            </span>
          )}
        </div>
      </div>
    </article>
  );
}
