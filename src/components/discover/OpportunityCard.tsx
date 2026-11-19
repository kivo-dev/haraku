import { useLocale, useTranslations } from "next-intl";
import { SlotImage } from "@/components/ui/SlotImage";
import { opportunityImageSrc, sectorArt, sectorIcons, type Opportunity } from "@/lib/opportunities";
import { pick } from "@/lib/places";

/** Economic opportunity: photo on one side, sector, title and short description on the other. */
export function OpportunityCard({ item }: { item: Opportunity }) {
  const locale = useLocale();
  const t = useTranslations("Opportunities");
  const Icon = sectorIcons[item.sector];
  const summary = pick(item.summary, locale);

  return (
    <article className="flex h-full overflow-hidden rounded-4xl bg-white shadow-soft">
      <SlotImage
        src={opportunityImageSrc(item.id, item.image)}
        alt=""
        tone={sectorArt[item.sector]}
        className="relative w-[38%] shrink-0"
      />
      <div className="flex min-w-0 flex-1 flex-col justify-center gap-2 p-4">
        <span className="inline-flex h-7 w-fit items-center gap-1.5 rounded-full bg-lime-300/60 px-2.5 text-xs font-medium text-forest-900">
          <Icon className="size-3.5" aria-hidden />
          {t(`sectors.${item.sector}`)}
        </span>
        <h3 className="text-base font-semibold leading-snug text-forest-950">{pick(item.title, locale)}</h3>
        {summary && <p className="line-clamp-3 text-sm leading-6 text-ink-500">{summary}</p>}
      </div>
    </article>
  );
}
