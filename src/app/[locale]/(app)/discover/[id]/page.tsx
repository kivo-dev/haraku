import { ArrowLeft, Map as MapIcon, MapPin, Route, Star } from "lucide-react";
import { notFound } from "next/navigation";
import { getLocale, getTranslations, setRequestLocale } from "next-intl/server";
import { FavoriteButton } from "@/components/discover/FavoriteButton";
import { SlotImage } from "@/components/ui/SlotImage";
import { Link } from "@/i18n/navigation";
import { getPlace } from "@/lib/api/places";
import { placeGallerySrc, placeImageSrc } from "@/lib/images";
import { categoryArt, categoryIcons, pick, samplePlaces } from "@/lib/places";

export const revalidate = 300;

export function generateStaticParams() {
  return samplePlaces.map((p) => ({ id: p.id }));
}

type Props = { params: Promise<{ locale: string; id: string }> };

export default async function PlacePage({ params }: Props) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const place = await getPlace(id);
  if (!place) notFound();

  const t = await getTranslations("Place");
  const tc = await getTranslations("Categories");
  const td = await getTranslations("Discover");
  const lang = await getLocale();
  const Icon = categoryIcons[place.category];
  const name = pick(place.name, lang);
  const area = pick(place.area, lang);
  const summary = pick(place.summary, lang);
  const pill = "inline-flex h-10 items-center gap-1.5 rounded-full bg-white px-4 text-sm text-ink-700";
  const gallery = place.images?.length ? place.images : placeGallerySrc(place.id);

  return (
    <article className="-mt-4 md:mt-0 md:grid md:grid-cols-2 md:items-start md:gap-10 md:px-10">
      <div className="relative md:sticky md:top-6">
        <SlotImage
          src={placeImageSrc(place.id, place.image)}
          alt=""
          tone={categoryArt[place.category]}
          priority
          className="relative aspect-[4/5] md:rounded-5xl"
        />
        <div aria-hidden className="absolute inset-0 bg-gradient-to-t from-forest-950/75 via-transparent to-forest-950/25 md:rounded-5xl" />
        <Link
          href="/discover"
          aria-label={t("back")}
          className="glass-dark absolute start-4 flex size-11 items-center justify-center rounded-full text-white"
          style={{ top: "calc(env(safe-area-inset-top) + 1rem)" }}
        >
          <ArrowLeft className="size-5 rtl:rotate-180" aria-hidden />
        </Link>
        <div className="absolute inset-x-0 bottom-14 px-5 text-white md:bottom-6 md:px-7">
          {area && (
            <p className="flex items-center gap-1.5 text-sm text-white/85">
              <MapPin className="size-4" aria-hidden />
              {area}
            </p>
          )}
          <h1 className="mt-1.5 text-[2rem] font-bold leading-[1.25] md:text-5xl">{name}</h1>
        </div>
      </div>

      <div className="relative -mt-8 rounded-t-5xl bg-mist-100 px-5 pb-6 pt-9 md:mt-0 md:rounded-none md:bg-transparent md:px-0 md:pt-4">
        <FavoriteButton id={place.id} size="lg" className="absolute -top-7 end-6 md:hidden" />

        <span className="inline-flex h-9 items-center gap-2 rounded-full bg-white px-3.5 text-sm font-medium text-forest-900">
          <Icon className="size-4" aria-hidden />
          {tc(place.category)}
        </span>

        <div className="mt-4 flex flex-wrap gap-2">
          {place.rating && (
            <span className={pill}>
              <Star className="size-4 fill-lime-500 text-lime-600" aria-hidden />
              {place.rating.toFixed(1)}
            </span>
          )}
          {place.distanceKm !== undefined && <span className={pill}>{t("distance", { km: place.distanceKm })}</span>}
          {place.source === "sample" && <span className={`${pill} !bg-lime-300/60 text-forest-900`}>{td("sample")}</span>}
        </div>

        {summary && (
          <section className="mt-6">
            <h2 className="text-lg font-semibold">{t("about")}</h2>
            <p className="mt-2 max-w-prose leading-8 text-ink-700">{summary}</p>
          </section>
        )}

        <div className="no-scrollbar mt-6 flex gap-3 overflow-x-auto">
          {gallery.map((src) => (
            <SlotImage key={src} src={src} alt="" optional className="relative aspect-[4/3] w-44 shrink-0 rounded-3xl md:w-56" />
          ))}
        </div>

        <div className="mt-7 flex flex-col gap-3 sm:flex-row">
          <Link
            href="/route"
            className="inline-flex h-14 flex-1 items-center justify-center gap-2 rounded-full bg-lime-400 font-semibold text-forest-950 transition hover:bg-lime-300"
          >
            <Route className="size-5" aria-hidden />
            {t("routeHere")}
          </Link>
          <Link
            href="/map"
            className="inline-flex h-14 flex-1 items-center justify-center gap-2 rounded-full bg-forest-950 font-medium text-white transition hover:bg-forest-800"
          >
            <MapIcon className="size-5" aria-hidden />
            {t("showOnMap")}
          </Link>
        </div>
        <div className="mt-3 hidden md:block">
          <FavoriteButton id={place.id} size="lg" className="!bg-white" />
        </div>
      </div>
    </article>
  );
}
