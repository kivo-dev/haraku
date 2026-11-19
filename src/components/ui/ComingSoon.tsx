import { Map as MapIcon, Route, Sparkles } from "lucide-react";
import { useTranslations } from "next-intl";
import { imageSlots } from "@/lib/images";
import { Badge } from "./Badge";
import { SlotImage } from "./SlotImage";

const config = {
  map: { icon: MapIcon, slot: imageSlots.soonMap, tone: "forest" },
  assistant: { icon: Sparkles, slot: imageSlots.soonAssistant, tone: "fog" },
  route: { icon: Route, slot: imageSlots.soonRoute, tone: "dawn" },
} as const;

export function ComingSoon({ id }: { id: keyof typeof config }) {
  const t = useTranslations("Soon");
  const { icon: Icon, slot, tone } = config[id];

  return (
    <section className="px-5 pt-4 md:mx-auto md:max-w-3xl md:pt-10">
      <div className="overflow-hidden rounded-4xl bg-white shadow-soft">
        <div className="relative">
          <SlotImage src={slot.src} alt="" tone={tone} className="relative aspect-[4/3] md:aspect-[16/9]" />
          <span className="glass absolute start-4 top-4 flex size-12 items-center justify-center rounded-full text-forest-800">
            <Icon className="size-5" aria-hidden />
          </span>
        </div>
        <div className="p-6 md:p-8">
          <h1 className="text-2xl font-bold">{t(`${id}.title`)}</h1>
          <p className="mt-2 max-w-md text-ink-500">{t(`${id}.text`)}</p>
          <Badge className="mt-5 bg-mist-100">{t("badge")}</Badge>
        </div>
      </div>
    </section>
  );
}
